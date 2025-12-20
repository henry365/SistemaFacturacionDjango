"""
ViewSets para el módulo de Caja

Este módulo implementa los ViewSets para Cajas, Sesiones y Movimientos,
siguiendo los estándares de la Guía Inicial.
"""
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from core.mixins import EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin

from .models import Caja, SesionCaja, MovimientoCaja
from .serializers import (
    CajaSerializer, CajaListSerializer,
    SesionCajaSerializer, SesionCajaListSerializer,
    MovimientoCajaSerializer, MovimientoCajaListSerializer,
    CerrarSesionSerializer, AbrirSesionSerializer
)
from .services import CajaService, SesionCajaService, MovimientoCajaService
from .constants import ESTADO_ABIERTA, TIPOS_NO_ELIMINABLES


# ============================================================
# PAGINACIÓN
# ============================================================

class CajaPagination(PageNumberPagination):
    """Paginación personalizada para Cajas"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SesionCajaPagination(PageNumberPagination):
    """Paginación personalizada para Sesiones de Caja"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MovimientoCajaPagination(PageNumberPagination):
    """Paginación personalizada para Movimientos de Caja"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ============================================================
# VIEWSETS
# ============================================================

class CajaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Cajas (puntos de venta).

    Endpoints:
        GET /cajas/ - Listar cajas de la empresa
        POST /cajas/ - Crear nueva caja
        GET /cajas/{id}/ - Detalle de caja
        PUT/PATCH /cajas/{id}/ - Actualizar caja
        DELETE /cajas/{id}/ - Eliminar caja
        GET /cajas/{id}/sesiones/ - Listar sesiones de una caja
        GET /cajas/{id}/sesion_activa/ - Obtener sesión activa
        POST /cajas/{id}/activar/ - Activar caja
        POST /cajas/{id}/desactivar/ - Desactivar caja

    Filtros disponibles:
        - activa: Filtrar por estado activo (true/false)
        - search: Buscar por nombre o descripción
        - ordering: Ordenar por nombre, fecha_creacion, activa

    Ejemplo Request (POST /cajas/):
        {
            "nombre": "Caja Principal",
            "descripcion": "Caja del local principal"
        }

    Ejemplo Response (POST /cajas/):
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "nombre": "Caja Principal",
            "descripcion": "Caja del local principal",
            "activa": true,
            "fecha_creacion": "2025-01-27T10:30:00Z",
            "sesiones_count": 0,
            "tiene_sesion_abierta": false
        }
    """
    queryset = Caja.objects.select_related(
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [IsAuthenticated]
    pagination_class = CajaPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activa']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion', 'activa']
    ordering = ['nombre']

    def get_serializer_class(self):
        """Retorna serializer según la acción"""
        if self.action == 'list':
            return CajaListSerializer
        return CajaSerializer

    @action(detail=True, methods=['get'])
    def sesiones(self, request, pk=None):
        """
        Lista las sesiones de una caja específica.

        GET /cajas/{id}/sesiones/
        """
        caja = self.get_object()
        sesiones = caja.sesiones.select_related(
            'usuario', 'usuario_creacion'
        ).order_by('-fecha_apertura')
        page = self.paginate_queryset(sesiones)
        if page is not None:
            serializer = SesionCajaListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SesionCajaListSerializer(sesiones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sesion_activa(self, request, pk=None):
        """
        Retorna la sesión activa de la caja si existe.

        GET /cajas/{id}/sesion_activa/
        """
        caja = self.get_object()
        sesion = caja.get_sesion_activa()
        if sesion:
            serializer = SesionCajaSerializer(sesion)
            return Response(serializer.data)
        return Response(
            {'detail': 'No hay sesión activa'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa una caja.

        POST /cajas/{id}/activar/
        """
        caja = self.get_object()
        exito, error = CajaService.activar_caja(caja, request.user)
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Caja "{caja.nombre}" activada correctamente'})

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Desactiva una caja.

        POST /cajas/{id}/desactivar/
        """
        caja = self.get_object()
        exito, error = CajaService.desactivar_caja(caja, request.user)
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Caja "{caja.nombre}" desactivada correctamente'})


class SesionCajaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Sesiones de Caja.

    Una sesión representa un turno de trabajo en una caja. Tiene un ciclo de vida:
    ABIERTA → CERRADA → ARQUEADA

    Endpoints:
        GET /sesiones-caja/ - Listar sesiones
        POST /sesiones-caja/ - Abrir nueva sesión
        GET /sesiones-caja/{id}/ - Detalle de sesión
        POST /sesiones-caja/{id}/cerrar/ - Cerrar sesión
        POST /sesiones-caja/{id}/arquear/ - Arquear sesión
        GET /sesiones-caja/{id}/resumen/ - Resumen de sesión

    Filtros disponibles:
        - caja: Filtrar por ID de caja
        - usuario: Filtrar por ID de usuario
        - estado: Filtrar por estado (ABIERTA, CERRADA, ARQUEADA)
        - search: Buscar por observaciones o nombre de caja
        - ordering: Ordenar por fecha_apertura, fecha_cierre, estado

    Ejemplo Request (POST /sesiones-caja/):
        {
            "caja": 1,
            "monto_apertura": "5000.00",
            "observaciones": "Apertura del turno mañana"
        }

    Ejemplo Response (POST /sesiones-caja/):
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "caja": 1,
            "caja_nombre": "Caja Principal",
            "usuario": 5,
            "usuario_nombre": "cajero1",
            "fecha_apertura": "2025-01-27T08:00:00Z",
            "monto_apertura": "5000.00",
            "estado": "ABIERTA",
            "estado_display": "Abierta",
            "observaciones": "Apertura del turno mañana",
            "movimientos": [],
            "total_ingresos": 5000.00,
            "total_egresos": 0,
            "saldo_actual": 5000.00
        }
    """
    queryset = SesionCaja.objects.select_related(
        'caja',
        'empresa',
        'usuario',
        'usuario_creacion',
        'usuario_modificacion'
    ).prefetch_related('movimientos').all()
    permission_classes = [IsAuthenticated]
    pagination_class = SesionCajaPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['caja', 'usuario', 'estado']
    search_fields = ['observaciones', 'caja__nombre']
    ordering_fields = ['fecha_apertura', 'fecha_cierre', 'estado']
    ordering = ['-fecha_apertura']

    def get_serializer_class(self):
        """Retorna serializer según la acción"""
        if self.action == 'list':
            return SesionCajaListSerializer
        if self.action == 'create':
            return AbrirSesionSerializer
        return SesionCajaSerializer

    def create(self, request, *args, **kwargs):
        """
        Abre una nueva sesión de caja.

        Usa SesionCajaService para la lógica de negocio.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        caja = serializer.validated_data['caja']
        monto_apertura = serializer.validated_data['monto_apertura']
        observaciones = serializer.validated_data.get('observaciones', '')

        sesion, error = SesionCajaService.abrir_sesion(
            caja=caja,
            monto_apertura=monto_apertura,
            usuario=request.user,
            observaciones=observaciones
        )

        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = SesionCajaSerializer(sesion)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Cierra una sesión de caja.

        POST /sesiones-caja/{id}/cerrar/

        Body:
        {
            "monto_cierre_usuario": 1500.00,
            "observaciones": "Cierre sin novedades"
        }
        """
        sesion = self.get_object()
        serializer = CerrarSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        monto_usuario = serializer.validated_data['monto_cierre_usuario']
        observaciones = serializer.validated_data.get('observaciones', '')

        exito, error = SesionCajaService.cerrar_sesion(
            sesion=sesion,
            monto_cierre_usuario=monto_usuario,
            ejecutado_por=request.user,
            observaciones=observaciones
        )

        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Refrescar desde la BD
        sesion.refresh_from_db()
        return Response(SesionCajaSerializer(sesion).data)

    @action(detail=True, methods=['post'])
    def arquear(self, request, pk=None):
        """
        Marca una sesión como arqueada (verificada/auditada).

        POST /sesiones-caja/{id}/arquear/

        Body (opcional):
        {
            "observaciones": "Arqueo verificado"
        }
        """
        sesion = self.get_object()
        observaciones = request.data.get('observaciones', '')

        exito, error = SesionCajaService.arquear_sesion(
            sesion=sesion,
            ejecutado_por=request.user,
            observaciones=observaciones
        )

        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        sesion.refresh_from_db()
        return Response(SesionCajaSerializer(sesion).data)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Obtiene resumen detallado de una sesión.

        GET /sesiones-caja/{id}/resumen/
        """
        sesion = self.get_object()
        resumen = SesionCajaService.obtener_resumen_sesion(sesion)
        return Response(resumen)


class MovimientoCajaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Movimientos de Caja.

    Los movimientos representan entradas y salidas de dinero de una sesión de caja.
    Tipos de ingreso: VENTA, INGRESO_MANUAL, APERTURA
    Tipos de egreso: RETIRO_MANUAL, GASTO_MENOR, CIERRE

    Endpoints:
        GET /movimientos-caja/ - Listar movimientos
        POST /movimientos-caja/ - Registrar movimiento
        GET /movimientos-caja/{id}/ - Detalle de movimiento
        PUT/PATCH /movimientos-caja/{id}/ - Actualizar movimiento
        DELETE /movimientos-caja/{id}/ - Eliminar movimiento
        POST /movimientos-caja/{id}/anular/ - Anular movimiento

    Filtros disponibles:
        - sesion: Filtrar por ID de sesión
        - tipo_movimiento: Filtrar por tipo (VENTA, INGRESO_MANUAL, etc.)
        - usuario: Filtrar por ID de usuario
        - search: Buscar por descripción o referencia
        - ordering: Ordenar por fecha, monto, tipo_movimiento

    Ejemplo Request (POST /movimientos-caja/):
        {
            "sesion": 1,
            "tipo_movimiento": "VENTA",
            "monto": "1500.00",
            "descripcion": "Venta de productos",
            "referencia": "FAC-001"
        }

    Ejemplo Response (POST /movimientos-caja/):
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440002",
            "sesion": 1,
            "sesion_estado": "ABIERTA",
            "caja_nombre": "Caja Principal",
            "tipo_movimiento": "VENTA",
            "tipo_movimiento_display": "Venta (Cobro)",
            "monto": "1500.00",
            "descripcion": "Venta de productos",
            "fecha": "2025-01-27T10:45:00Z",
            "referencia": "FAC-001",
            "usuario": 5,
            "usuario_nombre": "cajero1",
            "es_ingreso": true,
            "es_egreso": false
        }
    """
    queryset = MovimientoCaja.objects.select_related(
        'sesion',
        'sesion__caja',
        'empresa',
        'usuario',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [IsAuthenticated]
    pagination_class = MovimientoCajaPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['sesion', 'tipo_movimiento', 'usuario']
    search_fields = ['descripcion', 'referencia']
    ordering_fields = ['fecha', 'monto', 'tipo_movimiento']
    ordering = ['-fecha']

    def get_serializer_class(self):
        """Retorna serializer según la acción"""
        if self.action == 'list':
            return MovimientoCajaListSerializer
        return MovimientoCajaSerializer

    def create(self, request, *args, **kwargs):
        """
        Registra un nuevo movimiento.

        Usa MovimientoCajaService para la lógica de negocio.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sesion = serializer.validated_data['sesion']
        tipo = serializer.validated_data['tipo_movimiento']
        monto = serializer.validated_data['monto']
        descripcion = serializer.validated_data['descripcion']
        referencia = serializer.validated_data.get('referencia')

        movimiento, error = MovimientoCajaService.registrar_movimiento(
            sesion=sesion,
            tipo_movimiento=tipo,
            monto=monto,
            descripcion=descripcion,
            usuario=request.user,
            referencia=referencia
        )

        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = MovimientoCajaSerializer(movimiento)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Actualiza un movimiento con validaciones"""
        movimiento = self.get_object()

        # No permitir editar movimientos de sesiones cerradas
        if movimiento.sesion.estado != ESTADO_ABIERTA:
            return Response(
                {'error': 'No se pueden editar movimientos de una sesión cerrada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Elimina un movimiento con validaciones"""
        movimiento = self.get_object()

        puede, error = MovimientoCajaService.puede_eliminar(movimiento)
        if not puede:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        """
        Anula un movimiento creando un movimiento inverso.

        POST /movimientos-caja/{id}/anular/

        Body:
        {
            "motivo": "Error en el monto registrado"
        }
        """
        movimiento = self.get_object()
        motivo = request.data.get('motivo', '')

        if not motivo:
            return Response(
                {'error': 'Debe proporcionar un motivo para la anulación'},
                status=status.HTTP_400_BAD_REQUEST
            )

        exito, error = MovimientoCajaService.anular_movimiento(
            movimiento=movimiento,
            ejecutado_por=request.user,
            motivo=motivo
        )

        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'mensaje': f'Movimiento {movimiento.id} anulado correctamente',
            'movimiento_anulado': MovimientoCajaSerializer(movimiento).data
        })

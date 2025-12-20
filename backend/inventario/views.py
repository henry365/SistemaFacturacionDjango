"""
Vistas para el módulo de Inventario.

Implementa ViewSets con:
- Logging para operaciones
- Permisos personalizados
- Paginación
- Filtros avanzados
- Optimización de queries
"""
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, F
from django.utils import timezone
from django.db import transaction
from .models import (
    Almacen, InventarioProducto, MovimientoInventario,
    ReservaStock, Lote, AlertaInventario,
    TransferenciaInventario, DetalleTransferencia,
    AjusteInventario, DetalleAjusteInventario,
    ConteoFisico, DetalleConteoFisico
)
from .serializers import (
    AlmacenSerializer, AlmacenListSerializer,
    InventarioProductoSerializer, InventarioProductoListSerializer,
    MovimientoInventarioSerializer, MovimientoInventarioListSerializer,
    ReservaStockSerializer, LoteSerializer, LoteListSerializer,
    AlertaInventarioSerializer, AlertaInventarioListSerializer,
    TransferenciaInventarioSerializer, TransferenciaInventarioListSerializer,
    DetalleTransferenciaSerializer,
    AjusteInventarioSerializer, AjusteInventarioListSerializer,
    DetalleAjusteInventarioSerializer,
    ConteoFisicoSerializer, ConteoFisicoListSerializer,
    DetalleConteoFisicoSerializer
)
from .services import ServicioInventario, ServicioAlertasInventario
from .permissions import (
    CanGestionarAlmacen, CanGestionarInventario, CanGestionarMovimientos,
    CanGestionarReservas, CanGestionarLotes, CanGestionarAlertas,
    CanGestionarTransferencias, CanGestionarAjustes, CanAprobarAjustes,
    CanGestionarConteos, CanVerKardex
)
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
from usuarios.permissions import ActionBasedPermission

logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN PERSONALIZADA
# =============================================================================

class InventarioPagination(PageNumberPagination):
    """Paginación personalizada para el módulo de inventario."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# VIEWSET DE ALMACENES
# =============================================================================

class AlmacenViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de almacenes."""
    queryset = Almacen.objects.all()
    serializer_class = AlmacenSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'empresa']
    search_fields = ['nombre', 'direccion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarAlmacen()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return AlmacenListSerializer
        return AlmacenSerializer

    def get_queryset(self):
        """Filtrar almacenes según empresa del usuario."""
        user = self.request.user
        queryset = super().get_queryset().select_related('empresa', 'usuario_creacion')
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        return queryset

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear almacén."""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Almacén creado: {instance.nombre} (id={instance.id}, empresa_id={instance.empresa_id}, usuario={user.id})")

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Almacén actualizado: {instance.nombre} (id={instance.id}, usuario={self.request.user.id})")

    def perform_destroy(self, instance):
        """Log al eliminar almacén."""
        logger.warning(f"Almacén eliminado: {instance.nombre} (id={instance.id}, usuario={self.request.user.id})")
        super().perform_destroy(instance)


# =============================================================================
# VIEWSET DE INVENTARIO DE PRODUCTOS
# =============================================================================

class InventarioProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para inventario de productos."""
    queryset = InventarioProducto.objects.all()
    serializer_class = InventarioProductoSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['almacen', 'producto', 'empresa']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['producto__nombre', 'cantidad_disponible', 'fecha_creacion']
    ordering = ['producto__nombre']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarInventario()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return InventarioProductoListSerializer
        return InventarioProductoSerializer

    def get_queryset(self):
        """Filtrar inventarios según empresa del usuario."""
        queryset = super().get_queryset().select_related('producto', 'almacen', 'empresa')

        bajo_minimo = self.request.query_params.get('bajo_minimo')
        if bajo_minimo == 'true':
            queryset = queryset.filter(cantidad_disponible__lte=F('stock_minimo'))

        return queryset


# =============================================================================
# VIEWSET DE MOVIMIENTOS DE INVENTARIO
# =============================================================================

class MovimientoInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para movimientos de inventario."""
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['producto', 'almacen', 'tipo_movimiento', 'empresa']
    search_fields = ['producto__nombre', 'producto__codigo_sku', 'referencia']
    ordering_fields = ['fecha', 'tipo_movimiento']
    ordering = ['-fecha']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action == 'kardex':
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanVerKardex()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarMovimientos()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return MovimientoInventarioListSerializer
        return MovimientoInventarioSerializer

    def get_queryset(self):
        """Filtrar movimientos según empresa del usuario."""
        return super().get_queryset().select_related(
            'producto', 'almacen', 'usuario', 'lote', 'empresa'
        )

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear movimiento."""
        user = self.request.user
        kwargs = {
            'usuario': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(
            f"Movimiento creado: {instance.tipo_movimiento} de {instance.cantidad} unidades "
            f"(producto={instance.producto_id}, almacen={instance.almacen_id}, usuario={user.id})"
        )

    @action(detail=False, methods=['get'], url_path='kardex')
    def kardex(self, request):
        """
        Endpoint de Kardex según especificaciones.
        Devuelve el historial de movimientos por producto y almacén, con saldo acumulado.

        Parámetros de consulta:
        - producto_id: ID del producto (requerido)
        - almacen_id: ID del almacén (requerido)
        - fecha_desde: Fecha inicial (opcional, formato YYYY-MM-DD)
        - fecha_hasta: Fecha final (opcional, formato YYYY-MM-DD)
        """
        producto_id = request.query_params.get('producto_id')
        almacen_id = request.query_params.get('almacen_id')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')

        if not producto_id or not almacen_id:
            return Response(
                {'error': 'Los parámetros producto_id y almacen_id son requeridos'},
                status=400
            )

        logger.info(f"Kardex consultado: producto={producto_id}, almacen={almacen_id}, usuario={request.user.id}")

        # Filtrar movimientos por empresa también
        user = request.user
        queryset = MovimientoInventario.objects.filter(
            producto_id=producto_id,
            almacen_id=almacen_id
        )
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        queryset = queryset.select_related('producto', 'almacen', 'usuario', 'lote').order_by('fecha')

        # Filtros opcionales de fecha
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        # Calcular saldo inicial
        if fecha_desde:
            movimientos_anteriores = MovimientoInventario.objects.filter(
                producto_id=producto_id,
                almacen_id=almacen_id,
                fecha__lt=fecha_desde
            )
            if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
                movimientos_anteriores = movimientos_anteriores.filter(empresa=user.empresa)

            entradas = movimientos_anteriores.filter(
                tipo_movimiento__in=[
                    'ENTRADA_COMPRA', 'ENTRADA_AJUSTE', 'TRANSFERENCIA_ENTRADA',
                    'DEVOLUCION_CLIENTE'
                ]
            ).aggregate(total=Sum('cantidad'))['total'] or 0

            salidas = movimientos_anteriores.filter(
                tipo_movimiento__in=[
                    'SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA',
                    'DEVOLUCION_PROVEEDOR'
                ]
            ).aggregate(total=Sum('cantidad'))['total'] or 0

            saldo_inicial = entradas - salidas
        else:
            saldo_inicial = 0

        saldo_acumulado = saldo_inicial

        # Construir respuesta con saldo acumulado
        movimientos = []
        for movimiento in queryset:
            if movimiento.tipo_movimiento in [
                'ENTRADA_COMPRA', 'ENTRADA_AJUSTE', 'TRANSFERENCIA_ENTRADA',
                'DEVOLUCION_CLIENTE'
            ]:
                saldo_acumulado += movimiento.cantidad
            elif movimiento.tipo_movimiento in [
                'SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA',
                'DEVOLUCION_PROVEEDOR'
            ]:
                saldo_acumulado -= movimiento.cantidad

            movimientos.append({
                'id': movimiento.id,
                'fecha': movimiento.fecha,
                'tipo_movimiento': movimiento.tipo_movimiento,
                'tipo_movimiento_display': movimiento.get_tipo_movimiento_display(),
                'cantidad': float(movimiento.cantidad),
                'costo_unitario': float(movimiento.costo_unitario),
                'valor_total': float(movimiento.cantidad * movimiento.costo_unitario),
                'saldo_acumulado': float(saldo_acumulado),
                'referencia': movimiento.referencia,
                'numero_serie': movimiento.numero_serie,
                'numero_lote_proveedor': movimiento.numero_lote_proveedor,
                'lote_codigo': movimiento.lote.codigo_lote if movimiento.lote else None,
                'usuario': movimiento.usuario.username,
                'notas': movimiento.notas,
                'producto': {
                    'id': movimiento.producto.id,
                    'nombre': movimiento.producto.nombre,
                    'codigo_sku': movimiento.producto.codigo_sku,
                },
                'almacen': {
                    'id': movimiento.almacen.id,
                    'nombre': movimiento.almacen.nombre,
                },
            })

        producto = queryset.first().producto if queryset.exists() else None
        almacen = queryset.first().almacen if queryset.exists() else None

        return Response({
            'producto': {
                'id': producto.id if producto else producto_id,
                'nombre': producto.nombre if producto else None,
                'codigo_sku': producto.codigo_sku if producto else None,
            },
            'almacen': {
                'id': almacen.id if almacen else almacen_id,
                'nombre': almacen.nombre if almacen else None,
            },
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'saldo_inicial': float(saldo_inicial),
            'saldo_final': float(saldo_acumulado),
            'total_movimientos': len(movimientos),
            'movimientos': movimientos,
        })


# =============================================================================
# VIEWSET DE RESERVAS
# =============================================================================

class ReservaStockViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para reservas de stock."""
    queryset = ReservaStock.objects.all()
    serializer_class = ReservaStockSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'empresa']
    search_fields = ['referencia', 'inventario__producto__nombre']
    ordering_fields = ['fecha_reserva', 'estado']
    ordering = ['-fecha_reserva']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'confirmar', 'cancelar']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarReservas()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_queryset(self):
        """Filtrar reservas según empresa del usuario."""
        return super().get_queryset().select_related(
            'inventario__producto', 'inventario__almacen', 'usuario', 'empresa'
        )

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear reserva."""
        user = self.request.user
        kwargs = {
            'usuario': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Reserva creada: {instance.cantidad_reservada} unidades (id={instance.id}, usuario={user.id})")

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirma una reserva de stock."""
        reserva = self.get_object()
        try:
            ServicioInventario.confirmar_reserva(reserva)
            logger.info(f"Reserva confirmada: id={reserva.id}, usuario={request.user.id}")
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error confirmando reserva {reserva.id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una reserva de stock."""
        reserva = self.get_object()
        try:
            ServicioInventario.cancelar_reserva(reserva)
            logger.info(f"Reserva cancelada: id={reserva.id}, usuario={request.user.id}")
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error cancelando reserva {reserva.id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# VIEWSET DE LOTES
# =============================================================================

class LoteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para lotes de productos."""
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'producto', 'almacen', 'empresa']
    search_fields = ['codigo_lote', 'numero_lote', 'producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['fecha_ingreso', 'fecha_vencimiento', 'estado']
    ordering = ['-fecha_ingreso']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarLotes()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return LoteListSerializer
        return LoteSerializer

    def get_queryset(self):
        """Filtrar lotes según empresa del usuario."""
        queryset = super().get_queryset().select_related('producto', 'almacen', 'empresa', 'proveedor')

        vencidos = self.request.query_params.get('vencidos')
        if vencidos == 'true':
            queryset = queryset.filter(fecha_vencimiento__lt=timezone.now().date())

        return queryset

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear lote."""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Lote creado: {instance.codigo_lote} (id={instance.id}, producto={instance.producto_id}, usuario={user.id})")

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Lote actualizado: {instance.codigo_lote} (id={instance.id}, usuario={self.request.user.id})")


# =============================================================================
# VIEWSET DE ALERTAS
# =============================================================================

class AlertaInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para alertas de inventario."""
    queryset = AlertaInventario.objects.all()
    serializer_class = AlertaInventarioSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'prioridad', 'resuelta', 'empresa']
    search_fields = ['mensaje', 'inventario__producto__nombre', 'lote__codigo_lote']
    ordering_fields = ['fecha_alerta', 'prioridad', 'tipo']
    ordering = ['-fecha_alerta']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'resolver', 'generar_alertas']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarAlertas()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return AlertaInventarioListSerializer
        return AlertaInventarioSerializer

    def get_queryset(self):
        """Filtrar alertas según empresa del usuario."""
        queryset = super().get_queryset().select_related(
            'inventario__producto', 'inventario__almacen', 'lote__producto', 'empresa'
        )

        # Filtrar solo alertas no resueltas por defecto
        resueltas = self.request.query_params.get('resueltas')
        if resueltas != 'true':
            queryset = queryset.filter(resuelta=False)

        return queryset

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear alerta."""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Alerta creada: {instance.tipo} - {instance.prioridad} (id={instance.id}, usuario={user.id})")

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Alerta actualizada: id={instance.id}, usuario={self.request.user.id}")

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Marca una alerta como resuelta."""
        alerta = self.get_object()
        alerta.resuelta = True
        alerta.usuario_resolucion = request.user
        alerta.fecha_resuelta = timezone.now()
        alerta.save()
        logger.info(f"Alerta resuelta: id={alerta.id}, usuario={request.user.id}")
        serializer = self.get_serializer(alerta)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generar_alertas(self, request):
        """Genera todas las alertas de inventario."""
        try:
            resultado = ServicioAlertasInventario.generar_todas_las_alertas()
            logger.info(f"Alertas generadas: {resultado['total']} (usuario={request.user.id})")
            return Response({
                'mensaje': 'Alertas generadas exitosamente',
                'resultado': resultado
            })
        except Exception as e:
            logger.error(f"Error generando alertas: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# VIEWSETS DE TRANSFERENCIAS
# =============================================================================

class DetalleTransferenciaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para detalles de transferencias.

    Endpoints:
        GET /detalles-transferencia/ - Listar detalles
        POST /detalles-transferencia/ - Crear detalle
        GET /detalles-transferencia/{id}/ - Detalle
        PUT/PATCH /detalles-transferencia/{id}/ - Actualizar
        DELETE /detalles-transferencia/{id}/ - Eliminar
    """
    queryset = DetalleTransferencia.objects.select_related(
        'transferencia', 'transferencia__empresa', 'producto', 'lote'
    ).all()
    serializer_class = DetalleTransferenciaSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transferencia', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['id', 'cantidad']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarTransferencias()]

    def get_queryset(self):
        """Filtra por empresa de la transferencia."""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            qs = qs.filter(transferencia__empresa=self.request.user.empresa)
        return qs

    def perform_create(self, serializer):
        """Log al crear detalle."""
        super().perform_create(serializer)
        logger.info(f"DetalleTransferencia creado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_update(self, serializer):
        """Log al actualizar detalle."""
        super().perform_update(serializer)
        logger.info(f"DetalleTransferencia actualizado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_destroy(self, instance):
        """Log al eliminar detalle."""
        logger.warning(f"DetalleTransferencia eliminado: id={instance.id} (usuario={self.request.user.id})")
        instance.delete()


class TransferenciaInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para transferencias de inventario."""
    queryset = TransferenciaInventario.objects.all()
    serializer_class = TransferenciaInventarioSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'almacen_origen', 'almacen_destino', 'empresa']
    search_fields = ['numero_transferencia', 'almacen_origen__nombre', 'almacen_destino__nombre']
    ordering_fields = ['fecha_solicitud', 'estado']
    ordering = ['-fecha_solicitud']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'enviar', 'recibir']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarTransferencias()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return TransferenciaInventarioListSerializer
        return TransferenciaInventarioSerializer

    def get_queryset(self):
        """Filtrar transferencias según empresa del usuario."""
        return super().get_queryset().select_related(
            'almacen_origen', 'almacen_destino', 'usuario_solicitante', 'usuario_receptor', 'empresa'
        ).prefetch_related('detalles__producto')

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear transferencia."""
        user = self.request.user
        kwargs = {
            'usuario_solicitante': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(
            f"Transferencia creada: {instance.numero_transferencia} "
            f"({instance.almacen_origen} -> {instance.almacen_destino}, usuario={user.id})"
        )

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Transferencia actualizada: {instance.numero_transferencia} (usuario={self.request.user.id})")

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Marca la transferencia como enviada."""
        transferencia = self.get_object()
        if transferencia.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden enviar transferencias pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transferencia.estado = 'EN_TRANSITO'
        transferencia.fecha_envio = timezone.now()
        transferencia.save()

        # Registrar movimientos de salida para cada detalle
        detalles = transferencia.detalles.all()
        for detalle in detalles:
            if detalle.cantidad_enviada > 0:
                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=transferencia.almacen_origen,
                    tipo_movimiento='TRANSFERENCIA_SALIDA',
                    cantidad=detalle.cantidad_enviada,
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=transferencia.empresa,
                    referencia=f"TRF-{transferencia.numero_transferencia}",
                    lote=detalle.lote
                )

        logger.info(f"Transferencia enviada: {transferencia.numero_transferencia} (usuario={request.user.id})")
        serializer = self.get_serializer(transferencia)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def recibir(self, request, pk=None):
        """Marca la transferencia como recibida."""
        transferencia = self.get_object()
        if transferencia.estado not in ['EN_TRANSITO', 'RECIBIDA_PARCIAL']:
            return Response(
                {'error': 'Solo se pueden recibir transferencias en tránsito'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transferencia.estado = 'RECIBIDA'
        transferencia.fecha_recepcion = timezone.now()
        transferencia.usuario_receptor = request.user
        transferencia.save()

        # Registrar movimientos de entrada para cada detalle recibido
        detalles = transferencia.detalles.all()
        for detalle in detalles:
            if detalle.cantidad_recibida > 0:
                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=transferencia.almacen_destino,
                    tipo_movimiento='TRANSFERENCIA_ENTRADA',
                    cantidad=detalle.cantidad_recibida,
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=transferencia.empresa,
                    referencia=f"TRF-{transferencia.numero_transferencia}",
                    lote=detalle.lote
                )

        logger.info(f"Transferencia recibida: {transferencia.numero_transferencia} (usuario={request.user.id})")
        serializer = self.get_serializer(transferencia)
        return Response(serializer.data)


# =============================================================================
# VIEWSETS DE AJUSTES
# =============================================================================

class DetalleAjusteInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para detalles de ajustes.

    Endpoints:
        GET /detalles-ajuste/ - Listar detalles
        POST /detalles-ajuste/ - Crear detalle
        GET /detalles-ajuste/{id}/ - Detalle
        PUT/PATCH /detalles-ajuste/{id}/ - Actualizar
        DELETE /detalles-ajuste/{id}/ - Eliminar
    """
    queryset = DetalleAjusteInventario.objects.select_related(
        'ajuste', 'ajuste__empresa', 'producto', 'lote'
    ).all()
    serializer_class = DetalleAjusteInventarioSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ajuste', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['id', 'cantidad']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarAjustes()]

    def get_queryset(self):
        """Filtra por empresa del ajuste."""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            qs = qs.filter(ajuste__empresa=self.request.user.empresa)
        return qs

    def perform_create(self, serializer):
        """Log al crear detalle."""
        super().perform_create(serializer)
        logger.info(f"DetalleAjusteInventario creado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_update(self, serializer):
        """Log al actualizar detalle."""
        super().perform_update(serializer)
        logger.info(f"DetalleAjusteInventario actualizado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_destroy(self, instance):
        """Log al eliminar detalle."""
        logger.warning(f"DetalleAjusteInventario eliminado: id={instance.id} (usuario={self.request.user.id})")
        instance.delete()


class AjusteInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para ajustes de inventario."""
    queryset = AjusteInventario.objects.all()
    serializer_class = AjusteInventarioSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_ajuste', 'almacen', 'empresa']
    search_fields = ['motivo', 'almacen__nombre']
    ordering_fields = ['fecha_ajuste', 'estado']
    ordering = ['-fecha_ajuste']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['aprobar', 'rechazar']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanAprobarAjustes()]
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'procesar']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarAjustes()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return AjusteInventarioListSerializer
        return AjusteInventarioSerializer

    def get_queryset(self):
        """Filtrar ajustes según empresa del usuario."""
        return super().get_queryset().select_related(
            'almacen', 'usuario_solicitante', 'usuario_aprobador', 'empresa'
        ).prefetch_related('detalles__producto')

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear ajuste."""
        user = self.request.user
        kwargs = {
            'usuario_solicitante': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Ajuste creado: {instance.tipo_ajuste} (id={instance.id}, almacen={instance.almacen_id}, usuario={user.id})")

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Ajuste actualizado: id={instance.id}, usuario={self.request.user.id}")

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un ajuste de inventario."""
        ajuste = self.get_object()
        if ajuste.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden aprobar ajustes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ajuste.estado = 'APROBADO'
        ajuste.usuario_aprobador = request.user
        ajuste.fecha_aprobacion = timezone.now()
        ajuste.observaciones_aprobacion = request.data.get('observaciones', '')
        ajuste.save()

        logger.info(f"Ajuste aprobado: id={ajuste.id}, usuario={request.user.id}")
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechaza un ajuste de inventario."""
        ajuste = self.get_object()
        if ajuste.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden rechazar ajustes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ajuste.estado = 'RECHAZADO'
        ajuste.usuario_aprobador = request.user
        ajuste.fecha_aprobacion = timezone.now()
        ajuste.observaciones_aprobacion = request.data.get('observaciones', '')
        ajuste.save()

        logger.info(f"Ajuste rechazado: id={ajuste.id}, usuario={request.user.id}")
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def procesar(self, request, pk=None):
        """Procesa un ajuste aprobado (aplica los cambios al inventario)."""
        ajuste = self.get_object()
        if ajuste.estado != 'APROBADO':
            return Response(
                {'error': 'Solo se pueden procesar ajustes aprobados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Aplicar cada detalle del ajuste
        for detalle in ajuste.detalles.all():
            if detalle.diferencia != 0:
                tipo_movimiento = 'ENTRADA_AJUSTE' if detalle.diferencia > 0 else 'SALIDA_AJUSTE'

                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=ajuste.almacen,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=abs(detalle.diferencia),
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=ajuste.empresa,
                    referencia=f"AJUSTE-{ajuste.id}",
                    lote=detalle.lote,
                    notas=f"Ajuste: {ajuste.motivo}"
                )

        ajuste.estado = 'PROCESADO'
        ajuste.save()

        logger.info(f"Ajuste procesado: id={ajuste.id}, usuario={request.user.id}")
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)


# =============================================================================
# VIEWSETS DE CONTEO FÍSICO
# =============================================================================

class DetalleConteoFisicoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para detalles de conteos físicos.

    Endpoints:
        GET /detalles-conteo/ - Listar detalles
        POST /detalles-conteo/ - Crear detalle
        GET /detalles-conteo/{id}/ - Detalle
        PUT/PATCH /detalles-conteo/{id}/ - Actualizar
        DELETE /detalles-conteo/{id}/ - Eliminar
    """
    queryset = DetalleConteoFisico.objects.select_related(
        'conteo', 'conteo__empresa', 'producto', 'lote'
    ).all()
    serializer_class = DetalleConteoFisicoSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['conteo', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['id', 'cantidad_contada']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarConteos()]

    def get_queryset(self):
        """Filtra por empresa del conteo."""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            qs = qs.filter(conteo__empresa=self.request.user.empresa)
        return qs

    def perform_create(self, serializer):
        """Log al crear detalle."""
        super().perform_create(serializer)
        logger.info(f"DetalleConteoFisico creado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_update(self, serializer):
        """Log al actualizar detalle."""
        super().perform_update(serializer)
        logger.info(f"DetalleConteoFisico actualizado: id={serializer.instance.id} (usuario={self.request.user.id})")

    def perform_destroy(self, instance):
        """Log al eliminar detalle."""
        logger.warning(f"DetalleConteoFisico eliminado: id={instance.id} (usuario={self.request.user.id})")
        instance.delete()


class ConteoFisicoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para conteos físicos."""
    queryset = ConteoFisico.objects.all()
    serializer_class = ConteoFisicoSerializer
    pagination_class = InventarioPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_conteo', 'almacen', 'empresa']
    search_fields = ['numero_conteo', 'almacen__nombre']
    ordering_fields = ['fecha_conteo', 'estado']
    ordering = ['-fecha_conteo']

    def get_permissions(self):
        """Aplica permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'iniciar', 'finalizar', 'ajustar']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarConteos()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Retorna serializer optimizado para listado."""
        if self.action == 'list':
            return ConteoFisicoListSerializer
        return ConteoFisicoSerializer

    def get_queryset(self):
        """Filtrar conteos según empresa del usuario."""
        return super().get_queryset().select_related(
            'almacen', 'usuario_responsable', 'empresa'
        ).prefetch_related('detalles__producto')

    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear conteo."""
        user = self.request.user
        kwargs = {
            'usuario_responsable': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        instance = serializer.save(**kwargs)
        logger.info(f"Conteo creado: {instance.numero_conteo} (id={instance.id}, almacen={instance.almacen_id}, usuario={user.id})")

    def perform_update(self, serializer):
        """Actualizar usuario de modificación."""
        instance = serializer.save(usuario_modificacion=self.request.user)
        logger.info(f"Conteo actualizado: {instance.numero_conteo} (usuario={self.request.user.id})")

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Inicia un conteo físico."""
        conteo = self.get_object()
        if conteo.estado != 'PLANIFICADO':
            return Response(
                {'error': 'Solo se pueden iniciar conteos planificados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conteo.estado = 'EN_PROCESO'
        conteo.fecha_inicio = timezone.now()
        conteo.save()

        logger.info(f"Conteo iniciado: {conteo.numero_conteo} (usuario={request.user.id})")
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finaliza un conteo físico."""
        conteo = self.get_object()
        if conteo.estado != 'EN_PROCESO':
            return Response(
                {'error': 'Solo se pueden finalizar conteos en proceso'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conteo.estado = 'FINALIZADO'
        conteo.fecha_fin = timezone.now()
        conteo.save()

        logger.info(f"Conteo finalizado: {conteo.numero_conteo} (usuario={request.user.id})")
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def ajustar(self, request, pk=None):
        """Ajusta el inventario basado en las diferencias del conteo."""
        conteo = self.get_object()
        if conteo.estado != 'FINALIZADO':
            return Response(
                {'error': 'Solo se pueden ajustar conteos finalizados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear ajuste automático basado en las diferencias
        ajuste = AjusteInventario.objects.create(
            empresa=conteo.empresa,
            almacen=conteo.almacen,
            tipo_ajuste='AJUSTE_DIFERENCIA',
            motivo=f'Ajuste por conteo físico {conteo.numero_conteo}',
            fecha_ajuste=conteo.fecha_conteo,
            estado='APROBADO',
            usuario_solicitante=conteo.usuario_responsable,
            usuario_aprobador=conteo.usuario_responsable,
            fecha_aprobacion=timezone.now()
        )

        # Crear detalles del ajuste
        for detalle_conteo in conteo.detalles.all():
            if detalle_conteo.diferencia != 0:
                DetalleAjusteInventario.objects.create(
                    ajuste=ajuste,
                    producto=detalle_conteo.producto,
                    lote=detalle_conteo.lote,
                    cantidad_anterior=detalle_conteo.cantidad_sistema,
                    cantidad_nueva=detalle_conteo.cantidad_fisica,
                    costo_unitario=detalle_conteo.producto.precio_venta_base
                )

        # Procesar el ajuste automáticamente
        for detalle_conteo in conteo.detalles.all():
            if detalle_conteo.diferencia != 0:
                tipo_movimiento = 'ENTRADA_AJUSTE' if detalle_conteo.diferencia > 0 else 'SALIDA_AJUSTE'

                ServicioInventario.registrar_movimiento(
                    producto=detalle_conteo.producto,
                    almacen=conteo.almacen,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=abs(detalle_conteo.diferencia),
                    costo_unitario=detalle_conteo.producto.precio_venta_base,
                    usuario=request.user,
                    empresa=conteo.empresa,
                    referencia=f"CONTEO-{conteo.numero_conteo}",
                    lote=detalle_conteo.lote,
                    notas=f"Ajuste por conteo físico {conteo.numero_conteo}"
                )

        conteo.estado = 'AJUSTADO'
        conteo.save()

        logger.info(f"Conteo ajustado: {conteo.numero_conteo} (ajuste_id={ajuste.id}, usuario={request.user.id})")
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)

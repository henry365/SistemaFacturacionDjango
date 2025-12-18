"""
Views para Activos Fijos
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from decimal import Decimal

from core.mixins import EmpresaFilterMixin
from .models import TipoActivo, ActivoFijo, Depreciacion
from .serializers import (
    TipoActivoSerializer,
    ActivoFijoSerializer,
    ActivoFijoListSerializer,
    DepreciacionSerializer,
    CalcularDepreciacionSerializer
)

logger = logging.getLogger(__name__)


class TipoActivoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar tipos de activos.

    Endpoints:
    - GET /api/v1/activos/tipos/ - Lista tipos de activos
    - POST /api/v1/activos/tipos/ - Crea nuevo tipo
    - GET /api/v1/activos/tipos/{id}/ - Detalle de tipo
    - PUT/PATCH /api/v1/activos/tipos/{id}/ - Actualiza tipo
    - DELETE /api/v1/activos/tipos/{id}/ - Elimina tipo
    """
    queryset = TipoActivo.objects.all()
    serializer_class = TipoActivoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'porcentaje_depreciacion_anual']
    ordering = ['nombre']

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class ActivoFijoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar activos fijos.

    Endpoints:
    - GET /api/v1/activos/activos/ - Lista activos
    - POST /api/v1/activos/activos/ - Crea nuevo activo
    - GET /api/v1/activos/activos/{id}/ - Detalle de activo
    - PUT/PATCH /api/v1/activos/activos/{id}/ - Actualiza activo
    - DELETE /api/v1/activos/activos/{id}/ - Elimina activo
    - POST /api/v1/activos/activos/{id}/depreciar/ - Registra depreciacion
    - GET /api/v1/activos/activos/{id}/historial_depreciacion/ - Historial
    - POST /api/v1/activos/activos/{id}/cambiar_estado/ - Cambia estado
    - GET /api/v1/activos/activos/por_estado/ - Resumen por estado
    - GET /api/v1/activos/activos/por_tipo/ - Resumen por tipo
    """
    queryset = ActivoFijo.objects.select_related(
        'tipo_activo',
        'responsable',
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo_activo', 'estado', 'ubicacion_fisica']
    search_fields = ['codigo_interno', 'nombre', 'marca', 'modelo', 'serial']
    ordering_fields = ['codigo_interno', 'nombre', 'fecha_adquisicion', 'valor_adquisicion']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        if self.action == 'list':
            return ActivoFijoListSerializer
        return ActivoFijoSerializer

    def perform_create(self, serializer):
        serializer.save(
            empresa=self.request.user.empresa,
            usuario_creacion=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(usuario_modificacion=self.request.user)

    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        """
        Resumen de activos por estado.

        Returns:
            Lista con cantidad, valor_total y valor_libro_total por cada estado.
        """
        from django.db.models import Count, Sum
        resumen = self.get_queryset().values('estado').annotate(
            cantidad=Count('id'),
            valor_total=Sum('valor_adquisicion'),
            valor_libro_total=Sum('valor_libro_actual')
        ).order_by('estado')
        return Response(resumen)

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        Resumen de activos por tipo de activo.

        Returns:
            Lista con cantidad, valor_total y valor_libro_total por tipo.
        """
        from django.db.models import Count, Sum
        resumen = self.get_queryset().values(
            'tipo_activo__nombre'
        ).annotate(
            cantidad=Count('id'),
            valor_total=Sum('valor_adquisicion'),
            valor_libro_total=Sum('valor_libro_actual')
        ).order_by('tipo_activo__nombre')
        return Response(resumen)

    @action(detail=True, methods=['post'])
    def depreciar(self, request, pk=None):
        """
        Calcula y registra la depreciacion de un activo.

        Metodo: Linea recta (DGII RD)
        - Depreciacion = valor_adquisicion * (tasa_anual / 12 / 100)

        Request body:
            - fecha: Fecha de la depreciacion (YYYY-MM-DD)
            - observacion: Comentario opcional

        Returns:
            - depreciacion: Datos de la depreciacion creada
            - activo: valor_libro_actual y estado actualizados
        """
        activo = self.get_object()

        serializer = CalcularDepreciacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fecha = serializer.validated_data['fecha']
        observacion = serializer.validated_data.get('observacion', '')

        # Verificar que no exista depreciacion para esa fecha
        if Depreciacion.objects.filter(activo=activo, fecha=fecha).exists():
            return Response(
                {'error': 'Ya existe una depreciacion para esta fecha.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el activo pueda depreciarse
        if activo.valor_libro_actual <= 0:
            return Response(
                {'error': 'El activo ya esta totalmente depreciado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular depreciacion usando metodo de linea recta (DGII RD)
        # Nota: Se usa valor_adquisicion para linea recta (depreciacion constante)
        # Si se requiere metodo de saldos decrecientes, usar valor_libro_actual
        tasa_mensual = activo.tipo_activo.porcentaje_depreciacion_anual / Decimal('12') / Decimal('100')
        monto_depreciacion = activo.valor_adquisicion * tasa_mensual
        # Asegurar que no se deprecie mas del valor libro actual
        monto_depreciacion = min(monto_depreciacion, activo.valor_libro_actual)

        valor_libro_anterior = activo.valor_libro_actual
        valor_libro_nuevo = valor_libro_anterior - monto_depreciacion

        with transaction.atomic():
            depreciacion = Depreciacion.objects.create(
                activo=activo,
                fecha=fecha,
                monto=monto_depreciacion,
                valor_libro_anterior=valor_libro_anterior,
                valor_libro_nuevo=valor_libro_nuevo,
                observacion=observacion,
                usuario_creacion=request.user
            )

            # Actualizar estado si esta totalmente depreciado
            # Usar valor_libro_nuevo en lugar de activo.valor_libro_actual
            # porque el objeto en memoria no se ha refrescado
            if valor_libro_nuevo <= 0:
                activo.refresh_from_db()
                activo.estado = 'DEPRECIADO'
                activo.save(update_fields=['estado'])

        # Log de operacion critica
        logger.info(
            f"Depreciacion registrada: Activo {activo.codigo_interno}, "
            f"Monto {monto_depreciacion}, Usuario {request.user.username}"
        )

        return Response({
            'depreciacion': DepreciacionSerializer(depreciacion).data,
            'activo': {
                'valor_libro_actual': activo.valor_libro_actual,
                'estado': activo.estado
            }
        })

    @action(detail=True, methods=['get'])
    def historial_depreciacion(self, request, pk=None):
        """
        Obtiene el historial de depreciaciones de un activo.

        Returns:
            Lista de todas las depreciaciones del activo ordenadas por fecha desc.
        """
        activo = self.get_object()
        depreciaciones = activo.depreciaciones.all()
        serializer = DepreciacionSerializer(depreciaciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de un activo.

        Request body:
            - estado: Nuevo estado (ACTIVO, MANTENIMIENTO, DEPRECIADO, VENDIDO, DESINCORPORADO)

        Returns:
            Datos completos del activo actualizado.
        """
        activo = self.get_object()
        nuevo_estado = request.data.get('estado')

        estados_validos = [e[0] for e in ActivoFijo.ESTADO_CHOICES]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado invalido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        estado_anterior = activo.estado
        activo.estado = nuevo_estado
        activo.usuario_modificacion = request.user
        activo.save()

        # Log de cambio de estado
        logger.info(
            f"Cambio de estado: Activo {activo.codigo_interno}, "
            f"{estado_anterior} -> {nuevo_estado}, Usuario {request.user.username}"
        )

        return Response(ActivoFijoSerializer(activo).data)


class DepreciacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar depreciaciones.
    Solo lectura - las depreciaciones se crean via /activos/{id}/depreciar/

    Endpoints:
    - GET /api/v1/activos/depreciaciones/ - Lista depreciaciones
    - GET /api/v1/activos/depreciaciones/{id}/ - Detalle de depreciacion
    """
    queryset = Depreciacion.objects.select_related(
        'activo',
        'activo__empresa',
        'usuario_creacion'
    ).all()
    serializer_class = DepreciacionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['activo', 'fecha']
    ordering_fields = ['fecha']
    ordering = ['-fecha']

    def get_queryset(self):
        """Filtra por empresa del usuario"""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            return qs.filter(activo__empresa=self.request.user.empresa)
        return qs.none()

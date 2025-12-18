"""
Views para Activos Fijos
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from core.mixins import EmpresaFilterMixin
from .services import DepreciacionService, ActivoFijoService
from .permissions import CanDepreciarActivo, CanCambiarEstadoActivo, CanVerProyeccion


class ActivosPagination(PageNumberPagination):
    """Paginación personalizada para activos fijos"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DepreciacionPagination(PageNumberPagination):
    """Paginación personalizada para depreciaciones"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


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
    pagination_class = ActivosPagination
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
    - GET /api/v1/activos/activos/{id}/proyeccion_depreciacion/ - Proyeccion
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
    pagination_class = ActivosPagination
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanDepreciarActivo])
    def depreciar(self, request, pk=None):
        """
        Calcula y registra la depreciacion de un activo.

        Requiere permiso: activos.depreciar_activofijo (o ser staff/superuser)

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

        # Usar el servicio para registrar la depreciación
        depreciacion, error = DepreciacionService.registrar_depreciacion(
            activo=activo,
            fecha=fecha,
            usuario=request.user,
            observacion=observacion
        )

        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Refrescar el activo para obtener valores actualizados
        activo.refresh_from_db()

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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanCambiarEstadoActivo])
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de un activo.

        Requiere permiso: activos.cambiar_estado_activofijo (o ser staff/superuser)

        Request body:
            - estado: Nuevo estado (ACTIVO, MANTENIMIENTO, DEPRECIADO, VENDIDO, DESINCORPORADO)

        Returns:
            Datos completos del activo actualizado.
        """
        activo = self.get_object()
        nuevo_estado = request.data.get('estado')

        # Usar el servicio para cambiar el estado
        exito, error = ActivoFijoService.cambiar_estado(
            activo=activo,
            nuevo_estado=nuevo_estado,
            usuario=request.user
        )

        if not exito:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ActivoFijoSerializer(activo).data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanVerProyeccion])
    def proyeccion_depreciacion(self, request, pk=None):
        """
        Calcula una proyección de depreciaciones futuras para el activo.

        Requiere permiso: activos.ver_proyeccion_activofijo (o ser staff/superuser)

        Query params:
            - meses: Número de meses a proyectar (default: 12, max: 120)

        Returns:
            Lista de proyecciones mensuales con monto y valores libro.
        """
        activo = self.get_object()

        # Obtener número de meses del query param
        try:
            meses = int(request.query_params.get('meses', 12))
            meses = min(max(meses, 1), 120)  # Entre 1 y 120 meses
        except ValueError:
            meses = 12

        proyeccion = DepreciacionService.calcular_proyeccion_depreciacion(
            activo=activo,
            meses=meses
        )

        return Response({
            'activo': activo.codigo_interno,
            'valor_libro_actual': activo.valor_libro_actual,
            'meses_proyectados': len(proyeccion),
            'proyeccion': proyeccion
        })


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
    pagination_class = DepreciacionPagination
    filterset_fields = ['activo', 'fecha']
    ordering_fields = ['fecha']
    ordering = ['-fecha']

    def get_queryset(self):
        """Filtra por empresa del usuario"""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            return qs.filter(activo__empresa=self.request.user.empresa)
        return qs.none()

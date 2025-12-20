"""
ViewSets para el módulo de Despachos

Endpoints:
    GET/POST /api/v1/despachos/ - Listar/Crear despachos
    GET/PUT/PATCH/DELETE /api/v1/despachos/{id}/ - CRUD individual
    POST /api/v1/despachos/{id}/preparar/ - Marcar en preparación
    POST /api/v1/despachos/{id}/despachar/ - Registrar despacho
    POST /api/v1/despachos/{id}/completar/ - Marcar como completado
    POST /api/v1/despachos/{id}/cancelar/ - Cancelar despacho
    GET /api/v1/despachos/{id}/detalles/ - Listar detalles
    GET /api/v1/despachos/{id}/resumen/ - Resumen del despacho
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Despacho, DetalleDespacho
from .serializers import (
    DespachoSerializer, DespachoListSerializer,
    DespacharSerializer, CancelarSerializer, DetalleDespachoSerializer
)
from .services import DespachoService
from .constants import PAGE_SIZE_DESPACHOS, PAGE_SIZE_MAX
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin

logger = logging.getLogger(__name__)


class DespachoPagination(PageNumberPagination):
    """Paginación personalizada para Despachos"""
    page_size = PAGE_SIZE_DESPACHOS
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


class DespachoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Despachos.

    Todos los endpoints filtran automáticamente por empresa del usuario.
    Las acciones de estado son idempotentes.
    """
    queryset = Despacho.objects.all()
    serializer_class = DespachoSerializer
    permission_classes = [IsAuthenticated, ActionBasedPermission]
    pagination_class = DespachoPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'cliente', 'almacen', 'factura']
    search_fields = ['cliente__nombre', 'factura__numero_factura', 'numero_guia']
    ordering_fields = ['fecha', 'estado', 'fecha_despacho', 'fecha_creacion']
    ordering = ['-fecha']

    def get_serializer_class(self):
        """Usa serializer optimizado para listados"""
        if self.action == 'list':
            return DespachoListSerializer
        return DespachoSerializer

    def get_queryset(self):
        """Optimiza queries con select_related y prefetch_related"""
        queryset = super().get_queryset()
        return queryset.select_related(
            'factura', 'cliente', 'almacen', 'empresa',
            'usuario_creacion', 'usuario_despacho'
        ).prefetch_related('detalles', 'detalles__producto', 'detalles__lote')

    @action(detail=True, methods=['post'])
    def preparar(self, request, pk=None):
        """
        Marca el despacho como en preparación.

        IDEMPOTENTE: Si ya está en preparación, retorna éxito.

        Endpoint: POST /api/v1/despachos/{id}/preparar/

        Returns:
            Datos del despacho actualizado

        Status Codes:
            - 200: OK
            - 400: Estado no permite esta acción
            - 404: Despacho no encontrado
        """
        despacho = self.get_object()
        logger.info(f"Preparar despacho {pk} por usuario {request.user.id}")

        resultado, error = DespachoService.preparar(despacho, request.user)

        if error:
            logger.warning(f"Error preparando despacho {pk}: {error}")
            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(DespachoSerializer(resultado).data)

    @action(detail=True, methods=['post'])
    def despachar(self, request, pk=None):
        """
        Registra el despacho de productos.

        IDEMPOTENTE: Usa get_or_create para detalles.

        Endpoint: POST /api/v1/despachos/{id}/despachar/

        Request Body:
            {
                "detalles": [{"producto_id": 1, "cantidad": 10}, ...],
                "observaciones": "opcional"
            }

        Returns:
            Datos del despacho actualizado

        Status Codes:
            - 200: OK
            - 400: Datos inválidos o estado no permite despacho
            - 404: Despacho no encontrado
        """
        despacho = self.get_object()
        logger.info(f"Despachar productos para despacho {pk} por usuario {request.user.id}")

        serializer = DespacharSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detalles_data = serializer.validated_data['detalles']
        observaciones = serializer.validated_data.get('observaciones', '')

        resultado, error = DespachoService.procesar_despacho(
            despacho, detalles_data, request.user, observaciones
        )

        if error:
            logger.warning(f"Error despachando {pk}: {error}")
            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(DespachoSerializer(resultado).data)

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Marca el despacho como completado.

        IDEMPOTENTE: Si ya está completado, retorna éxito.

        Endpoint: POST /api/v1/despachos/{id}/completar/

        Returns:
            Datos del despacho actualizado

        Status Codes:
            - 200: OK
            - 400: Estado no permite esta acción
            - 404: Despacho no encontrado
        """
        despacho = self.get_object()
        logger.info(f"Completar despacho {pk} por usuario {request.user.id}")

        resultado, error = DespachoService.completar(despacho, request.user)

        if error:
            logger.warning(f"Error completando despacho {pk}: {error}")
            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(DespachoSerializer(resultado).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela el despacho.

        IDEMPOTENTE: Si ya está cancelado, retorna éxito.

        Endpoint: POST /api/v1/despachos/{id}/cancelar/

        Request Body:
            {
                "observaciones": "Motivo de cancelación (opcional)"
            }

        Returns:
            Datos del despacho actualizado

        Status Codes:
            - 200: OK
            - 400: Estado no permite cancelación
            - 404: Despacho no encontrado
        """
        despacho = self.get_object()
        logger.info(f"Cancelar despacho {pk} por usuario {request.user.id}")

        serializer = CancelarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observaciones = serializer.validated_data.get('observaciones', '')

        resultado, error = DespachoService.cancelar(
            despacho, request.user, observaciones
        )

        if error:
            logger.warning(f"Error cancelando despacho {pk}: {error}")
            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(DespachoSerializer(resultado).data)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        """
        Lista los detalles de un despacho.

        Endpoint: GET /api/v1/despachos/{id}/detalles/

        Returns:
            Lista de detalles del despacho
        """
        despacho = self.get_object()
        detalles = despacho.detalles.select_related('producto', 'lote').all()
        serializer = DetalleDespachoSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Obtiene un resumen del estado del despacho.

        Endpoint: GET /api/v1/despachos/{id}/resumen/

        Returns:
            dict con resumen de cantidades y porcentaje
        """
        despacho = self.get_object()
        resumen = DespachoService.obtener_resumen(despacho)
        return Response(resumen)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de despachos por estado.

        Endpoint: GET /api/v1/despachos/estadisticas/

        Returns:
            dict con conteo por estado
        """
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {'detail': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stats = DespachoService.obtener_estadisticas(empresa)
        return Response(stats)


class DetalleDespachoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar Detalles de Despacho"""
    queryset = DetalleDespacho.objects.all()
    serializer_class = DetalleDespachoSerializer
    permission_classes = [IsAuthenticated, ActionBasedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['despacho', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['id', 'cantidad_despachada']

    def get_queryset(self):
        """Optimiza queries y filtra por empresa del despacho"""
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'despacho', 'despacho__empresa', 'producto', 'lote'
        )

        # Filtrar por empresa del usuario
        if hasattr(self.request.user, 'empresa') and self.request.user.empresa:
            queryset = queryset.filter(despacho__empresa=self.request.user.empresa)

        return queryset

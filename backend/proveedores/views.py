"""
ViewSets para el módulo Proveedores

Este módulo contiene los ViewSets para gestión de proveedores.
Incluye soporte para multi-tenancy con filtrado y asignación automática de empresa.
"""
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Proveedor
from .serializers import ProveedorSerializer, ProveedorListSerializer
from .permissions import CanGestionarProveedor
from .services import ServicioProveedor
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin


logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN
# =============================================================================

class ProveedoresPagination(PageNumberPagination):
    """Paginación personalizada para el módulo Proveedores"""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# VIEWSETS
# =============================================================================

class ProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar proveedores.

    Endpoints:
    - GET /proveedores/ - Lista todos los proveedores (filtrado por empresa)
    - POST /proveedores/ - Crea un nuevo proveedor (asigna empresa del usuario)
    - GET /proveedores/{id}/ - Obtiene un proveedor
    - PUT /proveedores/{id}/ - Actualiza un proveedor
    - DELETE /proveedores/{id}/ - Elimina un proveedor
    - GET /proveedores/{id}/historial_compras/ - Historial de compras
    - GET /proveedores/{id}/historial_ordenes/ - Historial de órdenes
    - GET /proveedores/{id}/resumen/ - Resumen con estadísticas
    """
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    pagination_class = ProveedoresPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'tipo_identificacion', 'tipo_contribuyente', 'es_internacional']
    search_fields = ['nombre', 'numero_identificacion', 'telefono', 'correo_electronico']
    ordering_fields = ['nombre', 'fecha_creacion', 'tipo_contribuyente']
    ordering = ['nombre']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanGestionarProveedor()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return ProveedorListSerializer
        return ProveedorSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con select_related.
        """
        return super().get_queryset().select_related('empresa')

    def perform_create(self, serializer):
        """
        Guarda el proveedor con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(
            f"Proveedor creado: {instance.nombre} (id={instance.id}) "
            f"empresa={instance.empresa_id} por usuario {self.request.user.username}"
        )

    def perform_update(self, serializer):
        """
        Actualiza el proveedor y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(
            f"Proveedor actualizado: {instance.nombre} (id={instance.id}) "
            f"por usuario {self.request.user.username}"
        )

    def perform_destroy(self, instance):
        """
        Elimina el proveedor y registra la acción.
        """
        nombre = instance.nombre
        instance_id = instance.id
        super().perform_destroy(instance)
        logger.info(
            f"Proveedor eliminado: {nombre} (id={instance_id}) "
            f"por usuario {self.request.user.username}"
        )

    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """
        Obtener historial de compras del proveedor.

        Returns:
            Response con lista de compras y estadísticas totales
        """
        proveedor = self.get_object()
        resultado = ServicioProveedor.obtener_historial_compras(proveedor)

        logger.info(
            f"Historial de compras consultado para proveedor {proveedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response(resultado)

    @action(detail=True, methods=['get'])
    def historial_ordenes(self, request, pk=None):
        """
        Obtener historial de órdenes de compra del proveedor.

        Returns:
            Response con lista de órdenes y estadísticas totales
        """
        proveedor = self.get_object()
        resultado = ServicioProveedor.obtener_historial_ordenes(proveedor)

        logger.info(
            f"Historial de órdenes consultado para proveedor {proveedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response(resultado)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Resumen completo del proveedor con estadísticas.

        Returns:
            Response con datos del proveedor y estadísticas de compras/órdenes
        """
        proveedor = self.get_object()
        estadisticas = ServicioProveedor.obtener_resumen_completo(proveedor)

        logger.info(
            f"Resumen consultado para proveedor {proveedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response({
            'proveedor': ProveedorSerializer(proveedor).data,
            **estadisticas
        })

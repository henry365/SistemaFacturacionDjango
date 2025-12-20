"""
ViewSets para el módulo Ventas

Implementa CRUD con permisos personalizados, paginación,
filtros y logging.
"""
import logging
from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CotizacionCliente, Factura, PagoCaja,
    NotaCredito, NotaDebito, DevolucionVenta,
    ListaEsperaProducto
)
from .serializers import (
    CotizacionClienteSerializer, CotizacionClienteListSerializer,
    FacturaSerializer, FacturaListSerializer,
    PagoCajaSerializer, PagoCajaListSerializer,
    NotaCreditoSerializer, NotaCreditoListSerializer,
    NotaDebitoSerializer, NotaDebitoListSerializer,
    DevolucionVentaSerializer, DevolucionVentaListSerializer,
    ListaEsperaProductoSerializer, ListaEsperaProductoListSerializer
)
from .permissions import (
    CanGestionarCotizacion, CanGestionarFactura, CanGestionarPagoCaja,
    CanGestionarNotaCredito, CanGestionarNotaDebito,
    CanGestionarDevolucionVenta, CanGestionarListaEspera
)
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
from usuarios.permissions import ActionBasedPermission

logger = logging.getLogger(__name__)


# =============================================================================
# Paginación
# =============================================================================

class VentasPagination(PageNumberPagination):
    """Paginación estándar para el módulo Ventas."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# Lista de Espera
# =============================================================================

class ListaEsperaProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de listas de espera de productos.

    Endpoints:
    - GET /listas-espera/ - Listar listas de espera
    - POST /listas-espera/ - Crear lista de espera
    - GET /listas-espera/{id}/ - Obtener detalle
    - PUT /listas-espera/{id}/ - Actualizar
    - DELETE /listas-espera/{id}/ - Eliminar
    """
    queryset = ListaEsperaProducto.objects.all()
    serializer_class = ListaEsperaProductoSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'prioridad', 'cliente', 'producto']
    search_fields = ['cliente__nombre', 'producto__nombre']
    ordering_fields = ['fecha_solicitud', 'prioridad']
    ordering = ['-fecha_solicitud']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarListaEspera()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return ListaEsperaProductoListSerializer
        return ListaEsperaProductoSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related."""
        return super().get_queryset().select_related('empresa', 'cliente', 'producto')

    def perform_create(self, serializer):
        """Log al crear lista de espera."""
        super().perform_create(serializer)
        logger.info(f"Lista de espera {serializer.instance.id} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar lista de espera."""
        super().perform_update(serializer)
        logger.info(f"Lista de espera {serializer.instance.id} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar lista de espera."""
        lista_id = instance.id
        logger.info(f"Lista de espera {lista_id} eliminada por {self.request.user}")
        instance.delete()


# =============================================================================
# Cotizaciones
# =============================================================================

class CotizacionClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de cotizaciones.

    Endpoints:
    - GET /cotizaciones/ - Listar cotizaciones
    - POST /cotizaciones/ - Crear cotización
    - GET /cotizaciones/{id}/ - Obtener detalle
    - PUT /cotizaciones/{id}/ - Actualizar
    - DELETE /cotizaciones/{id}/ - Eliminar
    """
    queryset = CotizacionCliente.objects.all()
    serializer_class = CotizacionClienteSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'cliente', 'vendedor']
    search_fields = ['cliente__nombre', 'vendedor__nombre']
    ordering_fields = ['fecha', 'estado', 'total']
    ordering = ['-fecha']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarCotizacion()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return CotizacionClienteListSerializer
        return CotizacionClienteSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'vendedor', 'usuario'
        ).prefetch_related('detalles')

    def perform_create(self, serializer):
        """Log al crear cotización."""
        super().perform_create(serializer)
        logger.info(f"Cotización {serializer.instance.id} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar cotización."""
        super().perform_update(serializer)
        logger.info(f"Cotización {serializer.instance.id} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar cotización."""
        cotizacion_id = instance.id
        logger.info(f"Cotización {cotizacion_id} eliminada por {self.request.user}")
        instance.delete()


# =============================================================================
# Facturas
# =============================================================================

class FacturaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de facturas.

    Endpoints:
    - GET /facturas/ - Listar facturas
    - POST /facturas/ - Crear factura
    - GET /facturas/{id}/ - Obtener detalle
    - PUT /facturas/{id}/ - Actualizar
    - DELETE /facturas/{id}/ - Eliminar
    """
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_venta', 'cliente', 'vendedor']
    search_fields = ['numero_factura', 'cliente__nombre', 'ncf']
    ordering_fields = ['fecha', 'total', 'estado', 'numero_factura']
    ordering = ['-fecha']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarFactura()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return FacturaListSerializer
        return FacturaSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'vendedor', 'cotizacion', 'usuario'
        ).prefetch_related('detalles')

    def perform_create(self, serializer):
        """Log al crear factura."""
        super().perform_create(serializer)
        logger.info(f"Factura {serializer.instance.numero_factura} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar factura."""
        super().perform_update(serializer)
        logger.info(f"Factura {serializer.instance.numero_factura} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar factura."""
        numero = instance.numero_factura
        logger.info(f"Factura {numero} eliminada por {self.request.user}")
        instance.delete()


# =============================================================================
# Pagos
# =============================================================================

class PagoCajaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de pagos en caja.

    Endpoints:
    - GET /pagos-caja/ - Listar pagos
    - POST /pagos-caja/ - Registrar pago
    - GET /pagos-caja/{id}/ - Obtener detalle
    - PUT /pagos-caja/{id}/ - Actualizar
    - DELETE /pagos-caja/{id}/ - Eliminar
    """
    queryset = PagoCaja.objects.all()
    serializer_class = PagoCajaSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['metodo_pago', 'cliente']
    search_fields = ['cliente__nombre', 'referencia']
    ordering_fields = ['fecha_pago', 'monto']
    ordering = ['-fecha_pago']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarPagoCaja()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return PagoCajaListSerializer
        return PagoCajaSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'usuario'
        ).prefetch_related('facturas')

    def perform_create(self, serializer):
        """Log al crear pago."""
        super().perform_create(serializer)
        logger.info(f"Pago {serializer.instance.id} de {serializer.instance.monto} creado por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar pago."""
        super().perform_update(serializer)
        logger.info(f"Pago {serializer.instance.id} actualizado por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar pago."""
        pago_id = instance.id
        monto = instance.monto
        logger.info(f"Pago {pago_id} de {monto} eliminado por {self.request.user}")
        instance.delete()


# =============================================================================
# Notas de Crédito
# =============================================================================

class NotaCreditoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de notas de crédito.

    Endpoints:
    - GET /notas-credito/ - Listar notas de crédito
    - POST /notas-credito/ - Crear nota
    - GET /notas-credito/{id}/ - Obtener detalle
    - PUT /notas-credito/{id}/ - Actualizar
    - DELETE /notas-credito/{id}/ - Eliminar
    """
    queryset = NotaCredito.objects.all()
    serializer_class = NotaCreditoSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['aplicada', 'cliente', 'factura']
    search_fields = ['cliente__nombre', 'motivo']
    ordering_fields = ['fecha', 'monto']
    ordering = ['-fecha']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarNotaCredito()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return NotaCreditoListSerializer
        return NotaCreditoSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'factura', 'usuario'
        )

    def perform_create(self, serializer):
        """Log al crear nota de crédito."""
        super().perform_create(serializer)
        logger.info(f"Nota de crédito {serializer.instance.id} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar nota de crédito."""
        super().perform_update(serializer)
        logger.info(f"Nota de crédito {serializer.instance.id} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar nota de crédito."""
        nota_id = instance.id
        logger.info(f"Nota de crédito {nota_id} eliminada por {self.request.user}")
        instance.delete()


# =============================================================================
# Notas de Débito
# =============================================================================

class NotaDebitoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de notas de débito.

    Endpoints:
    - GET /notas-debito/ - Listar notas de débito
    - POST /notas-debito/ - Crear nota
    - GET /notas-debito/{id}/ - Obtener detalle
    - PUT /notas-debito/{id}/ - Actualizar
    - DELETE /notas-debito/{id}/ - Eliminar
    """
    queryset = NotaDebito.objects.all()
    serializer_class = NotaDebitoSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'factura']
    search_fields = ['cliente__nombre', 'motivo']
    ordering_fields = ['fecha', 'monto']
    ordering = ['-fecha']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarNotaDebito()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return NotaDebitoListSerializer
        return NotaDebitoSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'factura', 'usuario'
        )

    def perform_create(self, serializer):
        """Log al crear nota de débito."""
        super().perform_create(serializer)
        logger.info(f"Nota de débito {serializer.instance.id} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar nota de débito."""
        super().perform_update(serializer)
        logger.info(f"Nota de débito {serializer.instance.id} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar nota de débito."""
        nota_id = instance.id
        logger.info(f"Nota de débito {nota_id} eliminada por {self.request.user}")
        instance.delete()


# =============================================================================
# Devoluciones
# =============================================================================

class DevolucionVentaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de devoluciones de venta.

    Endpoints:
    - GET /devoluciones/ - Listar devoluciones
    - POST /devoluciones/ - Crear devolución
    - GET /devoluciones/{id}/ - Obtener detalle
    - PUT /devoluciones/{id}/ - Actualizar
    - DELETE /devoluciones/{id}/ - Eliminar
    """
    queryset = DevolucionVenta.objects.all()
    serializer_class = DevolucionVentaSerializer
    pagination_class = VentasPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'factura']
    search_fields = ['cliente__nombre', 'factura__numero_factura', 'motivo']
    ordering_fields = ['fecha']
    ordering = ['-fecha']

    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarDevolucionVenta()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usar serializer optimizado para listados."""
        if self.action == 'list':
            return DevolucionVentaListSerializer
        return DevolucionVentaSerializer

    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related."""
        return super().get_queryset().select_related(
            'empresa', 'cliente', 'factura', 'usuario'
        ).prefetch_related('detalles')

    def perform_create(self, serializer):
        """Log al crear devolución."""
        super().perform_create(serializer)
        logger.info(f"Devolución {serializer.instance.id} creada por {self.request.user}")

    def perform_update(self, serializer):
        """Log al actualizar devolución."""
        super().perform_update(serializer)
        logger.info(f"Devolución {serializer.instance.id} actualizada por {self.request.user}")

    def perform_destroy(self, instance):
        """Log al eliminar devolución."""
        devolucion_id = instance.id
        logger.info(f"Devolución {devolucion_id} eliminada por {self.request.user}")
        instance.delete()

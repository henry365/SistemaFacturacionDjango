"""
Views para el módulo Empresas

Gestión de empresas del sistema multi-tenant.
"""
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum

from .models import Empresa
from .serializers import EmpresaSerializer, EmpresaListSerializer
from .permissions import (
    CanGestionarEmpresa, CanActualizarConfiguracionFiscal, CanVerEstadisticas
)
from .constants import (
    PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX,
    ERROR_CONFIGURACION_FISCAL_REQUERIDA, ERROR_CONFIGURACION_FISCAL_INVALIDA
)
from core.mixins import IdempotencyMixin

logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN
# =============================================================================

class EmpresaPagination(PageNumberPagination):
    """Paginación para Empresa"""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# VIEWSETS
# =============================================================================

class EmpresaViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar empresas.

    Las empresas son la base del sistema multiempresa.
    Cada usuario puede estar asociado a una empresa y solo verá datos de su empresa.

    Endpoints:
        GET/POST /api/v1/empresas/
        GET/PUT/PATCH/DELETE /api/v1/empresas/{id}/
        GET /api/v1/empresas/{id}/estadisticas/
        GET /api/v1/empresas/{id}/configuracion_fiscal/
        PATCH /api/v1/empresas/{id}/actualizar_configuracion_fiscal/
        GET /api/v1/empresas/mi_empresa/

    Permisos:
        - IsAuthenticated para lectura
        - CanGestionarEmpresa para crear/editar/eliminar
        - CanVerEstadisticas para estadísticas
        - CanActualizarConfiguracionFiscal para actualizar configuración fiscal
    """
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EmpresaPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'rnc', 'telefono', 'direccion']
    filterset_fields = ['activo']
    ordering_fields = ['nombre', 'rnc', 'fecha_creacion', 'activo']
    ordering = ['nombre']

    def get_permissions(self):
        """Aplica permisos según la acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanGestionarEmpresa()]
        if self.action == 'estadisticas':
            return [permissions.IsAuthenticated(), CanVerEstadisticas()]
        if self.action == 'actualizar_configuracion_fiscal':
            return [permissions.IsAuthenticated(), CanActualizarConfiguracionFiscal()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Usa serializer optimizado para listados"""
        if self.action == 'list':
            return EmpresaListSerializer
        return EmpresaSerializer

    def get_queryset(self):
        """Filtrar empresas según permisos del usuario"""
        queryset = super().get_queryset()

        # Si el usuario tiene una empresa asignada, solo puede ver su empresa
        # Los superusuarios pueden ver todas las empresas
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser or user.is_staff:
                # Superusuarios y staff pueden ver todas las empresas
                pass
            elif hasattr(user, 'empresa') and user.empresa:
                # Usuarios normales solo ven su empresa
                queryset = queryset.filter(id=user.empresa.id)

        # Filtro por activo
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')

        return queryset

    def perform_create(self, serializer):
        """Log al crear empresa"""
        instance = serializer.save()
        logger.info(
            f"Empresa creada: {instance.nombre} (id={instance.id}, "
            f"rnc={instance.rnc}, usuario={self.request.user.id})"
        )

    def perform_update(self, serializer):
        """Log al actualizar empresa"""
        instance = serializer.save()
        logger.info(
            f"Empresa actualizada: {instance.nombre} (id={instance.id}, "
            f"usuario={self.request.user.id})"
        )

    def perform_destroy(self, instance):
        """Log al eliminar empresa"""
        logger.warning(
            f"Empresa eliminada: {instance.nombre} (id={instance.id}, "
            f"rnc={instance.rnc}, usuario={self.request.user.id})"
        )
        instance.delete()

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtener estadísticas de la empresa.

        Endpoint: GET /api/v1/empresas/{id}/estadisticas/

        Returns:
            Estadísticas de clientes, facturas, ventas, proveedores, productos y compras.
        """
        empresa = self.get_object()

        # Importar modelos relacionados
        from clientes.models import Cliente
        from proveedores.models import Proveedor
        from productos.models import Producto
        from ventas.models import Factura
        from compras.models import Compra

        # Estadísticas básicas de la empresa
        estadisticas = {
            'empresa': EmpresaSerializer(empresa).data,
            'resumen': {
                'total_clientes': Cliente.objects.filter(empresa=empresa).count(),
            }
        }

        # Estadísticas de facturas (filtradas por cliente__empresa)
        facturas = Factura.objects.filter(cliente__empresa=empresa)
        estadisticas['resumen']['total_facturas'] = facturas.count()
        estadisticas['resumen']['total_ventas'] = float(
            facturas.aggregate(total=Sum('total'))['total'] or 0
        )
        estadisticas['resumen']['ventas_pendientes'] = float(
            facturas.aggregate(total=Sum('monto_pendiente'))['total'] or 0
        )

        # Estadísticas adicionales (solo si los modelos tienen campo empresa)
        # Proveedores
        try:
            if 'empresa' in [f.name for f in Proveedor._meta.get_fields()]:
                estadisticas['resumen']['total_proveedores'] = Proveedor.objects.filter(
                    empresa=empresa
                ).count()
            else:
                estadisticas['resumen']['total_proveedores'] = Proveedor.objects.count()
        except Exception:
            estadisticas['resumen']['total_proveedores'] = 0

        # Productos
        try:
            if 'empresa' in [f.name for f in Producto._meta.get_fields()]:
                estadisticas['resumen']['total_productos'] = Producto.objects.filter(
                    empresa=empresa
                ).count()
            else:
                estadisticas['resumen']['total_productos'] = Producto.objects.count()
        except Exception:
            estadisticas['resumen']['total_productos'] = 0

        # Compras
        try:
            estadisticas['resumen']['total_compras'] = Compra.objects.filter(
                empresa=empresa
            ).count()
        except Exception:
            estadisticas['resumen']['total_compras'] = 0

        logger.info(
            f"Estadísticas consultadas para empresa {empresa.id} "
            f"(usuario={request.user.id})"
        )

        return Response(estadisticas)

    @action(detail=True, methods=['get'])
    def configuracion_fiscal(self, request, pk=None):
        """
        Obtener configuración fiscal de la empresa.

        Endpoint: GET /api/v1/empresas/{id}/configuracion_fiscal/
        """
        empresa = self.get_object()
        return Response({
            'empresa': empresa.nombre,
            'configuracion_fiscal': empresa.configuracion_fiscal
        })

    @action(detail=True, methods=['patch'])
    def actualizar_configuracion_fiscal(self, request, pk=None):
        """
        Actualizar configuración fiscal.

        IDEMPOTENTE: Si la configuración ya es igual, no hace cambios.

        Endpoint: PATCH /api/v1/empresas/{id}/actualizar_configuracion_fiscal/

        Body:
            configuracion_fiscal: dict con la nueva configuración
        """
        empresa = self.get_object()
        nueva_config = request.data.get('configuracion_fiscal')

        if nueva_config is None:
            return Response(
                {'error': ERROR_CONFIGURACION_FISCAL_REQUERIDA},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(nueva_config, dict):
            return Response(
                {'error': ERROR_CONFIGURACION_FISCAL_INVALIDA},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar idempotencia - si ya tiene la misma config, no hacer nada
        if empresa.configuracion_fiscal == nueva_config:
            logger.info(
                f"Configuración fiscal ya actualizada para empresa {empresa.id} "
                f"(usuario={request.user.id}) - sin cambios"
            )
            return Response({
                'mensaje': 'Configuración fiscal sin cambios (ya actualizada)',
                'configuracion_fiscal': empresa.configuracion_fiscal
            })

        # Actualizar configuración fiscal
        empresa.configuracion_fiscal = nueva_config
        empresa.save(update_fields=['configuracion_fiscal', 'fecha_actualizacion'])

        logger.info(
            f"Configuración fiscal actualizada para empresa {empresa.id} "
            f"(usuario={request.user.id})"
        )

        return Response({
            'mensaje': 'Configuración fiscal actualizada correctamente',
            'configuracion_fiscal': empresa.configuracion_fiscal
        })

    @action(detail=False, methods=['get'])
    def mi_empresa(self, request):
        """
        Obtener la empresa del usuario autenticado.

        Endpoint: GET /api/v1/empresas/mi_empresa/
        """
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if hasattr(user, 'empresa') and user.empresa:
            serializer = self.get_serializer(user.empresa)
            return Response(serializer.data)

        return Response(
            {'error': 'El usuario no tiene una empresa asignada'},
            status=status.HTTP_404_NOT_FOUND
        )

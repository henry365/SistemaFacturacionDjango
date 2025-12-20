"""
ViewSets para el módulo Vendedores

Este módulo contiene los ViewSets para gestión de vendedores.
Incluye soporte para multi-tenancy con filtrado y asignación automática de empresa.
"""
import logging
from datetime import datetime
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Vendedor
from .serializers import VendedorSerializer, VendedorListSerializer
from .permissions import CanGestionarVendedor
from .services import ServicioVendedor
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
from usuarios.permissions import ActionBasedPermission


logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN
# =============================================================================

class VendedoresPagination(PageNumberPagination):
    """Paginación personalizada para el módulo Vendedores"""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# VIEWSETS
# =============================================================================

class VendedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar vendedores.

    Endpoints:
    - GET /vendedores/ - Lista todos los vendedores (filtrado por empresa)
    - POST /vendedores/ - Crea un nuevo vendedor (asigna empresa del usuario)
    - GET /vendedores/{id}/ - Obtiene un vendedor
    - PUT /vendedores/{id}/ - Actualiza un vendedor
    - DELETE /vendedores/{id}/ - Elimina un vendedor
    - GET /vendedores/{id}/estadisticas/ - Estadísticas del vendedor
    - GET /vendedores/{id}/ventas/ - Historial de ventas
    - GET /vendedores/{id}/cotizaciones/ - Historial de cotizaciones
    - GET /vendedores/{id}/clientes/ - Clientes asignados
    - GET /vendedores/{id}/comisiones/ - Cálculo de comisiones
    """
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = VendedoresPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'usuario']
    search_fields = ['nombre', 'cedula', 'telefono', 'correo']
    ordering_fields = ['nombre', 'fecha_creacion', 'comision_porcentaje']
    ordering = ['nombre']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarVendedor()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return VendedorListSerializer
        return VendedorSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con select_related.
        """
        return super().get_queryset().select_related('empresa', 'usuario')

    def perform_create(self, serializer):
        """
        Guarda el vendedor con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(
            f"Vendedor creado: {instance.nombre} (id={instance.id}) "
            f"empresa={instance.empresa_id} por usuario {self.request.user.username}"
        )

    def perform_update(self, serializer):
        """
        Actualiza el vendedor y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(
            f"Vendedor actualizado: {instance.nombre} (id={instance.id}) "
            f"por usuario {self.request.user.username}"
        )

    def perform_destroy(self, instance):
        """
        Elimina el vendedor y registra la acción.
        """
        nombre = instance.nombre
        instance_id = instance.id
        super().perform_destroy(instance)
        logger.info(
            f"Vendedor eliminado: {nombre} (id={instance_id}) "
            f"por usuario {self.request.user.username}"
        )

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtener estadísticas completas del vendedor.

        Returns:
            Response con datos del vendedor y estadísticas de ventas,
            cotizaciones y clientes
        """
        vendedor = self.get_object()
        estadisticas = ServicioVendedor.obtener_estadisticas_completas(vendedor)

        logger.info(
            f"Estadísticas consultadas para vendedor {vendedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response({
            'vendedor': VendedorSerializer(vendedor).data,
            'estadisticas': estadisticas
        })

    @action(detail=True, methods=['get'])
    def ventas(self, request, pk=None):
        """
        Listar ventas del vendedor.

        Returns:
            Response con lista de ventas y estadísticas totales
        """
        vendedor = self.get_object()
        resultado = ServicioVendedor.obtener_historial_ventas(vendedor)

        logger.info(
            f"Historial de ventas consultado para vendedor {vendedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response(resultado)

    @action(detail=True, methods=['get'])
    def cotizaciones(self, request, pk=None):
        """
        Listar cotizaciones del vendedor.

        Returns:
            Response con lista de cotizaciones y estadísticas totales
        """
        vendedor = self.get_object()
        resultado = ServicioVendedor.obtener_historial_cotizaciones(vendedor)

        logger.info(
            f"Historial de cotizaciones consultado para vendedor {vendedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response(resultado)

    @action(detail=True, methods=['get'])
    def clientes(self, request, pk=None):
        """
        Listar clientes asignados al vendedor.

        Returns:
            Response con lista de clientes asignados
        """
        vendedor = self.get_object()
        clientes = vendedor.clientes.all()

        from clientes.serializers import ClienteSerializer
        serializer = ClienteSerializer(clientes, many=True)

        logger.info(
            f"Clientes consultados para vendedor {vendedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response({
            'vendedor': vendedor.nombre,
            'total_clientes': clientes.count(),
            'clientes': serializer.data
        })

    @action(detail=True, methods=['get'])
    def comisiones(self, request, pk=None):
        """
        Calcular comisiones del vendedor en un período.

        Query Params:
            fecha_inicio: Fecha de inicio (YYYY-MM-DD)
            fecha_fin: Fecha de fin (YYYY-MM-DD)

        Returns:
            Response con resumen y detalle de comisiones
        """
        vendedor = self.get_object()

        # Obtener parámetros de fecha (opcional)
        fecha_inicio_str = request.query_params.get('fecha_inicio')
        fecha_fin_str = request.query_params.get('fecha_fin')

        fecha_inicio = None
        fecha_fin = None

        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        resultado = ServicioVendedor.calcular_comisiones(vendedor, fecha_inicio, fecha_fin)

        logger.info(
            f"Comisiones calculadas para vendedor {vendedor.nombre} "
            f"por usuario {request.user.username}"
        )

        return Response({
            'vendedor': vendedor.nombre,
            'comision_porcentaje': float(vendedor.comision_porcentaje),
            'periodo': {
                'fecha_inicio': fecha_inicio_str,
                'fecha_fin': fecha_fin_str
            },
            **resultado
        })

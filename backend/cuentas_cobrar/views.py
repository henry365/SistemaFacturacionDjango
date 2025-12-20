"""
Views para Cuentas por Cobrar

Este módulo define los ViewSets para el módulo de cuentas por cobrar,
con optimizaciones de consultas, paginación y uso de servicios.

Endpoints:
- CuentaPorCobrar: /api/cuentas-por-cobrar/
- CobroCliente: /api/cobros-clientes/
- DetalleCobroCliente: /api/detalles-cobros-clientes/
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError

from core.mixins import EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from .serializers import (
    CuentaPorCobrarSerializer,
    CobroClienteSerializer,
    DetalleCobroClienteSerializer,
    AplicarCobroSerializer
)
from .services import CuentaPorCobrarService, CobroClienteService
from .permissions import (
    CanAplicarCobro, CanReversarCobro, CanAnularCuentaPorCobrar, CanMarcarVencidas
)
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX


# ============================================================
# CLASES DE PAGINACION
# ============================================================

class CuentasPorCobrarPagination(PageNumberPagination):
    """Paginación para cuentas por cobrar."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


class CobrosPagination(PageNumberPagination):
    """Paginación para cobros de clientes."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# ============================================================
# VIEWSETS
# ============================================================

class CuentaPorCobrarViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Cuentas por Cobrar.

    Endpoints:
        GET /api/cuentas-por-cobrar/ - Listar cuentas por cobrar
        POST /api/cuentas-por-cobrar/ - Crear cuenta por cobrar
        GET /api/cuentas-por-cobrar/{id}/ - Obtener detalle
        PUT /api/cuentas-por-cobrar/{id}/ - Actualizar completo
        PATCH /api/cuentas-por-cobrar/{id}/ - Actualizar parcial
        DELETE /api/cuentas-por-cobrar/{id}/ - Eliminar

        GET /api/cuentas-por-cobrar/pendientes/ - CxC pendientes
        GET /api/cuentas-por-cobrar/vencidas/ - CxC vencidas
        GET /api/cuentas-por-cobrar/por_cliente/ - Resumen por cliente
        POST /api/cuentas-por-cobrar/{id}/anular/ - Anular CxC
        POST /api/cuentas-por-cobrar/marcar_vencidas/ - Marcar vencidas
    """
    queryset = CuentaPorCobrar.objects.select_related(
        'empresa', 'cliente', 'factura',
        'usuario_creacion', 'usuario_modificacion'
    ).prefetch_related('cobros_aplicados')
    serializer_class = CuentaPorCobrarSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CuentasPorCobrarPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'cliente']
    search_fields = ['numero_documento', 'cliente__nombre']
    ordering_fields = ['fecha_vencimiento', 'monto_pendiente', 'fecha_documento']
    ordering = ['-fecha_vencimiento']

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Obtener todas las CxC pendientes de cobro.

        Incluye estados: PENDIENTE, PARCIAL, VENCIDA
        """
        from .constants import ESTADOS_CXC_COBRABLES
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=ESTADOS_CXC_COBRABLES
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """
        Obtener todas las CxC vencidas.

        Retorna cuentas con fecha_vencimiento < hoy.
        """
        queryset = CuentaPorCobrarService.obtener_vencidas(request.empresa)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, CanMarcarVencidas])
    def marcar_vencidas(self, request):
        """
        Marcar como vencidas todas las CxC con fecha pasada.

        Retorna la cantidad de cuentas marcadas.
        """
        count = CuentaPorCobrarService.marcar_vencidas(request.empresa)
        return Response({
            'mensaje': f'Se marcaron {count} cuentas como vencidas.',
            'cantidad': count
        })

    @action(detail=False, methods=['get'])
    def por_cliente(self, request):
        """
        Resumen de CxC pendientes agrupado por cliente.

        Retorna total_pendiente y cantidad_facturas por cliente.
        """
        resumen = CuentaPorCobrarService.resumen_por_cliente(request.empresa)
        return Response(resumen)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAnularCuentaPorCobrar])
    def anular(self, request, pk=None):
        """
        Anular una cuenta por cobrar.

        Solo se puede anular si no tiene cobros aplicados.
        """
        cxc = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')

        try:
            cxc = CuentaPorCobrarService.anular(cxc, request.user, motivo)
            serializer = self.get_serializer(cxc)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CobroClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Cobros de Clientes.

    Endpoints:
        GET /api/cobros-clientes/ - Listar cobros
        POST /api/cobros-clientes/ - Crear cobro
        GET /api/cobros-clientes/{id}/ - Obtener detalle
        PUT /api/cobros-clientes/{id}/ - Actualizar completo
        PATCH /api/cobros-clientes/{id}/ - Actualizar parcial
        DELETE /api/cobros-clientes/{id}/ - Eliminar

        POST /api/cobros-clientes/{id}/aplicar/ - Aplicar a CxC
        POST /api/cobros-clientes/{id}/reversar/ - Reversar cobro
        GET /api/cobros-clientes/{id}/monto_disponible/ - Monto disponible
    """
    queryset = CobroCliente.objects.select_related(
        'empresa', 'cliente',
        'usuario_creacion', 'usuario_modificacion'
    ).prefetch_related(
        'detalles',
        'detalles__cuenta_por_cobrar'
    )
    serializer_class = CobroClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CobrosPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cliente', 'metodo_pago']
    search_fields = ['numero_recibo', 'cliente__nombre', 'referencia']
    ordering_fields = ['fecha_cobro', 'monto']
    ordering = ['-fecha_cobro']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAplicarCobro])
    def aplicar(self, request, pk=None):
        """
        Aplicar un cobro a múltiples cuentas por cobrar.

        Body: {"detalles": [{"cuenta_por_cobrar_id": 1, "monto_aplicado": 100.00}, ...]}
        """
        cobro = self.get_object()
        serializer = AplicarCobroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cobro = CobroClienteService.aplicar_cobro(
                cobro,
                serializer.validated_data['detalles'],
                request.user
            )
            return Response(CobroClienteSerializer(cobro).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanReversarCobro])
    def reversar(self, request, pk=None):
        """
        Reversar un cobro y restaurar las cuentas por cobrar.

        Body: {"motivo": "Razón de la reversión"}
        """
        cobro = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')

        try:
            cobro = CobroClienteService.reversar_cobro(cobro, request.user, motivo)
            return Response(CobroClienteSerializer(cobro).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def monto_disponible(self, request, pk=None):
        """
        Obtener el monto disponible para aplicar de un cobro.
        """
        cobro = self.get_object()
        monto = CobroClienteService.obtener_monto_disponible(cobro)
        return Response({
            'monto_total': cobro.monto,
            'monto_disponible': monto
        })


class DetalleCobroClienteViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar Detalles de Cobros a Clientes.

    Solo lectura, los detalles se crean a través del endpoint aplicar del cobro.

    Endpoints:
        GET /api/detalles-cobros-clientes/ - Listar detalles
        GET /api/detalles-cobros-clientes/{id}/ - Obtener detalle
    """
    queryset = DetalleCobroCliente.objects.select_related(
        'empresa', 'cobro', 'cobro__cliente',
        'cuenta_por_cobrar', 'cuenta_por_cobrar__cliente'
    )
    serializer_class = DetalleCobroClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cobro', 'cuenta_por_cobrar', 'empresa']

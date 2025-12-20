"""
Views para Cuentas por Pagar

Este módulo define los ViewSets para el módulo de cuentas por pagar,
con optimizaciones de consultas, paginación y uso de servicios.

Endpoints:
- CuentaPorPagar: /api/cuentas-por-pagar/
- PagoProveedor: /api/pagos-proveedores/
- DetallePagoProveedor: /api/detalles-pagos-proveedores/
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
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from .serializers import (
    CuentaPorPagarSerializer,
    PagoProveedorSerializer,
    DetallePagoProveedorSerializer,
    AplicarPagoSerializer
)
from .services import CuentaPorPagarService, PagoProveedorService
from .permissions import (
    CanAplicarPago, CanReversarPago, CanAnularCuentaPorPagar, CanMarcarVencidas
)
from .constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX


# ============================================================
# CLASES DE PAGINACION
# ============================================================

class CuentasPorPagarPagination(PageNumberPagination):
    """Paginación para cuentas por pagar."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


class PagosPagination(PageNumberPagination):
    """Paginación para pagos a proveedores."""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# ============================================================
# VIEWSETS
# ============================================================

class CuentaPorPagarViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Cuentas por Pagar.

    Endpoints:
        GET /api/cuentas-por-pagar/ - Listar cuentas por pagar
        POST /api/cuentas-por-pagar/ - Crear cuenta por pagar
        GET /api/cuentas-por-pagar/{id}/ - Obtener detalle
        PUT /api/cuentas-por-pagar/{id}/ - Actualizar completo
        PATCH /api/cuentas-por-pagar/{id}/ - Actualizar parcial
        DELETE /api/cuentas-por-pagar/{id}/ - Eliminar

        GET /api/cuentas-por-pagar/pendientes/ - CxP pendientes
        GET /api/cuentas-por-pagar/vencidas/ - CxP vencidas
        GET /api/cuentas-por-pagar/por_proveedor/ - Resumen por proveedor
        POST /api/cuentas-por-pagar/{id}/anular/ - Anular CxP
        POST /api/cuentas-por-pagar/marcar_vencidas/ - Marcar vencidas
    """
    queryset = CuentaPorPagar.objects.select_related(
        'empresa', 'proveedor', 'compra',
        'usuario_creacion', 'usuario_modificacion'
    ).prefetch_related('pagos_aplicados')
    serializer_class = CuentaPorPagarSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CuentasPorPagarPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'proveedor']
    search_fields = ['numero_documento', 'proveedor__nombre']
    ordering_fields = ['fecha_vencimiento', 'monto_pendiente', 'fecha_documento']
    ordering = ['-fecha_vencimiento']

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Obtener todas las CxP pendientes de pago.

        Incluye estados: PENDIENTE, PARCIAL, VENCIDA
        """
        from .constants import ESTADOS_CXP_PAGABLES
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=ESTADOS_CXP_PAGABLES
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
        Obtener todas las CxP vencidas.

        Retorna cuentas con fecha_vencimiento < hoy.
        """
        queryset = CuentaPorPagarService.obtener_vencidas(request.empresa)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, CanMarcarVencidas])
    def marcar_vencidas(self, request):
        """
        Marcar como vencidas todas las CxP con fecha pasada.

        Retorna la cantidad de cuentas marcadas.
        """
        count = CuentaPorPagarService.marcar_vencidas(request.empresa)
        return Response({
            'mensaje': f'Se marcaron {count} cuentas como vencidas.',
            'cantidad': count
        })

    @action(detail=False, methods=['get'])
    def por_proveedor(self, request):
        """
        Resumen de CxP pendientes agrupado por proveedor.

        Retorna total_pendiente y cantidad_facturas por proveedor.
        """
        resumen = CuentaPorPagarService.resumen_por_proveedor(request.empresa)
        return Response(resumen)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAnularCuentaPorPagar])
    def anular(self, request, pk=None):
        """
        Anular una cuenta por pagar.

        Solo se puede anular si no tiene pagos aplicados.
        """
        cxp = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')

        try:
            cxp = CuentaPorPagarService.anular(cxp, request.user, motivo)
            serializer = self.get_serializer(cxp)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PagoProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Pagos a Proveedores.

    Endpoints:
        GET /api/pagos-proveedores/ - Listar pagos
        POST /api/pagos-proveedores/ - Crear pago
        GET /api/pagos-proveedores/{id}/ - Obtener detalle
        PUT /api/pagos-proveedores/{id}/ - Actualizar completo
        PATCH /api/pagos-proveedores/{id}/ - Actualizar parcial
        DELETE /api/pagos-proveedores/{id}/ - Eliminar

        POST /api/pagos-proveedores/{id}/aplicar/ - Aplicar a CxP
        POST /api/pagos-proveedores/{id}/reversar/ - Reversar pago
        GET /api/pagos-proveedores/{id}/monto_disponible/ - Monto disponible
    """
    queryset = PagoProveedor.objects.select_related(
        'empresa', 'proveedor',
        'usuario_creacion', 'usuario_modificacion'
    ).prefetch_related(
        'detalles',
        'detalles__cuenta_por_pagar'
    )
    serializer_class = PagoProveedorSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PagosPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['proveedor', 'metodo_pago']
    search_fields = ['numero_pago', 'proveedor__nombre', 'referencia']
    ordering_fields = ['fecha_pago', 'monto']
    ordering = ['-fecha_pago']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAplicarPago])
    def aplicar(self, request, pk=None):
        """
        Aplicar un pago a múltiples cuentas por pagar.

        Body: {"detalles": [{"cuenta_por_pagar_id": 1, "monto_aplicado": 100.00}, ...]}
        """
        pago = self.get_object()
        serializer = AplicarPagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pago = PagoProveedorService.aplicar_pago(
                pago,
                serializer.validated_data['detalles'],
                request.user
            )
            return Response(PagoProveedorSerializer(pago).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanReversarPago])
    def reversar(self, request, pk=None):
        """
        Reversar un pago y restaurar las cuentas por pagar.

        Body: {"motivo": "Razón de la reversión"}
        """
        pago = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')

        try:
            pago = PagoProveedorService.reversar_pago(pago, request.user, motivo)
            return Response(PagoProveedorSerializer(pago).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def monto_disponible(self, request, pk=None):
        """
        Obtener el monto disponible para aplicar de un pago.
        """
        pago = self.get_object()
        monto = PagoProveedorService.obtener_monto_disponible(pago)
        return Response({
            'monto_total': pago.monto,
            'monto_disponible': monto
        })


class DetallePagoProveedorViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar Detalles de Pagos a Proveedores.

    Solo lectura, los detalles se crean a través del endpoint aplicar del pago.

    Endpoints:
        GET /api/detalles-pagos-proveedores/ - Listar detalles
        GET /api/detalles-pagos-proveedores/{id}/ - Obtener detalle
    """
    queryset = DetallePagoProveedor.objects.select_related(
        'empresa', 'pago', 'pago__proveedor',
        'cuenta_por_pagar', 'cuenta_por_pagar__proveedor'
    )
    serializer_class = DetallePagoProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pago', 'cuenta_por_pagar', 'empresa']

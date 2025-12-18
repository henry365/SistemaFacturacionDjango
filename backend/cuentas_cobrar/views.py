"""
Views para Cuentas por Cobrar
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from decimal import Decimal

from core.mixins import EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from .serializers import (
    CuentaPorCobrarSerializer,
    CobroClienteSerializer,
    DetalleCobroClienteSerializer,
    AplicarCobroSerializer
)


class CuentaPorCobrarViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = CuentaPorCobrar.objects.select_related('empresa', 'cliente', 'factura')
    serializer_class = CuentaPorCobrarSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'cliente']
    search_fields = ['numero_documento', 'cliente__nombre']
    ordering_fields = ['fecha_vencimiento', 'monto_pendiente', 'fecha_documento']
    ordering = ['-fecha_vencimiento']

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener todas las CxC pendientes"""
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Obtener todas las CxC vencidas"""
        from datetime import date
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL'],
            fecha_vencimiento__lt=date.today()
        )
        # Actualizar estado a VENCIDA
        for cxc in queryset:
            cxc.estado = 'VENCIDA'
            cxc.save(update_fields=['estado'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_cliente(self, request):
        """Resumen de CxC por cliente"""
        from django.db.models import Sum, Count
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        ).values('cliente__id', 'cliente__nombre').annotate(
            total_pendiente=Sum('monto_pendiente'),
            cantidad_facturas=Count('id')
        ).order_by('-total_pendiente')
        return Response(list(queryset))


class CobroClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = CobroCliente.objects.select_related('empresa', 'cliente').prefetch_related('detalles')
    serializer_class = CobroClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cliente', 'metodo_pago']
    search_fields = ['numero_recibo', 'cliente__nombre', 'referencia']
    ordering_fields = ['fecha_cobro', 'monto']
    ordering = ['-fecha_cobro']

    @action(detail=True, methods=['post'])
    def aplicar(self, request, pk=None):
        """Aplicar un cobro a multiples cuentas por cobrar"""
        cobro = self.get_object()
        serializer = AplicarCobroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detalles = serializer.validated_data['detalles']
        total_aplicado = sum(Decimal(str(d['monto_aplicado'])) for d in detalles)

        if total_aplicado > cobro.monto:
            return Response(
                {'error': f'El total aplicado ({total_aplicado}) excede el monto del cobro ({cobro.monto}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for detalle in detalles:
                cuenta = CuentaPorCobrar.objects.get(id=detalle['cuenta_por_cobrar_id'])
                monto = Decimal(str(detalle['monto_aplicado']))

                if monto > cuenta.monto_pendiente:
                    return Response(
                        {'error': f'El monto ({monto}) excede el pendiente de {cuenta.numero_documento} ({cuenta.monto_pendiente}).'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                DetalleCobroCliente.objects.create(
                    cobro=cobro,
                    cuenta_por_cobrar=cuenta,
                    monto_aplicado=monto
                )

                cuenta.monto_cobrado += monto
                cuenta.monto_pendiente -= monto
                cuenta.actualizar_estado()
                cuenta.save()

        cobro.refresh_from_db()
        return Response(CobroClienteSerializer(cobro).data)


class DetalleCobroClienteViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = DetalleCobroCliente.objects.select_related('cobro', 'cuenta_por_cobrar')
    serializer_class = DetalleCobroClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cobro', 'cuenta_por_cobrar']

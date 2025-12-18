"""
Views para Cuentas por Pagar
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
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from .serializers import (
    CuentaPorPagarSerializer,
    PagoProveedorSerializer,
    DetallePagoProveedorSerializer,
    AplicarPagoSerializer
)


class CuentaPorPagarViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = CuentaPorPagar.objects.select_related('empresa', 'proveedor', 'compra')
    serializer_class = CuentaPorPagarSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'proveedor']
    search_fields = ['numero_documento', 'proveedor__nombre']
    ordering_fields = ['fecha_vencimiento', 'monto_pendiente', 'fecha_documento']
    ordering = ['-fecha_vencimiento']

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener todas las CxP pendientes"""
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Obtener todas las CxP vencidas"""
        from datetime import date
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL'],
            fecha_vencimiento__lt=date.today()
        )
        # Actualizar estado a VENCIDA
        for cxp in queryset:
            cxp.estado = 'VENCIDA'
            cxp.save(update_fields=['estado'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_proveedor(self, request):
        """Resumen de CxP por proveedor"""
        from django.db.models import Sum, Count
        queryset = self.filter_queryset(self.get_queryset()).filter(
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        ).values('proveedor__id', 'proveedor__nombre').annotate(
            total_pendiente=Sum('monto_pendiente'),
            cantidad_facturas=Count('id')
        ).order_by('-total_pendiente')
        return Response(list(queryset))


class PagoProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = PagoProveedor.objects.select_related('empresa', 'proveedor').prefetch_related('detalles')
    serializer_class = PagoProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['proveedor', 'metodo_pago']
    search_fields = ['numero_pago', 'proveedor__nombre', 'referencia']
    ordering_fields = ['fecha_pago', 'monto']
    ordering = ['-fecha_pago']

    @action(detail=True, methods=['post'])
    def aplicar(self, request, pk=None):
        """Aplicar un pago a multiples cuentas por pagar"""
        pago = self.get_object()
        serializer = AplicarPagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detalles = serializer.validated_data['detalles']
        total_aplicado = sum(Decimal(str(d['monto_aplicado'])) for d in detalles)

        if total_aplicado > pago.monto:
            return Response(
                {'error': f'El total aplicado ({total_aplicado}) excede el monto del pago ({pago.monto}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for detalle in detalles:
                cuenta = CuentaPorPagar.objects.get(id=detalle['cuenta_por_pagar_id'])
                monto = Decimal(str(detalle['monto_aplicado']))

                if monto > cuenta.monto_pendiente:
                    return Response(
                        {'error': f'El monto ({monto}) excede el pendiente de {cuenta.numero_documento} ({cuenta.monto_pendiente}).'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                DetallePagoProveedor.objects.create(
                    pago=pago,
                    cuenta_por_pagar=cuenta,
                    monto_aplicado=monto
                )

                cuenta.monto_pagado += monto
                cuenta.monto_pendiente -= monto
                cuenta.actualizar_estado()
                cuenta.save()

        pago.refresh_from_db()
        return Response(PagoProveedorSerializer(pago).data)


class DetallePagoProveedorViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = DetallePagoProveedor.objects.select_related('pago', 'cuenta_por_pagar')
    serializer_class = DetallePagoProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pago', 'cuenta_por_pagar']

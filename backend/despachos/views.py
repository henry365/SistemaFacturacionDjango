from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Despacho, DetalleDespacho
from .serializers import DespachoSerializer, DespacharSerializer, DetalleDespachoSerializer
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin


class DespachoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar Despachos"""
    queryset = Despacho.objects.all()
    serializer_class = DespachoSerializer
    permission_classes = [IsAuthenticated, ActionBasedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'cliente', 'almacen', 'factura']
    search_fields = ['cliente__nombre', 'factura__numero_factura', 'numero_guia']
    ordering_fields = ['fecha', 'estado', 'fecha_despacho']
    ordering = ['-fecha']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('factura', 'cliente', 'almacen', 'empresa')

    @action(detail=True, methods=['post'])
    def preparar(self, request, pk=None):
        """Marca el despacho como en preparación"""
        despacho = self.get_object()

        if despacho.estado != 'PENDIENTE':
            return Response(
                {'detail': 'Solo se pueden preparar despachos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        despacho.estado = 'EN_PREPARACION'
        despacho.save()

        return Response(DespachoSerializer(despacho).data)

    @action(detail=True, methods=['post'])
    def despachar(self, request, pk=None):
        """Registra el despacho de productos"""
        despacho = self.get_object()

        if despacho.estado not in ['PENDIENTE', 'EN_PREPARACION', 'PARCIAL']:
            return Response(
                {'detail': 'No se puede despachar en este estado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DespacharSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detalles_data = serializer.validated_data['detalles']
        observaciones = serializer.validated_data.get('observaciones', '')

        # Procesar detalles
        for detalle_data in detalles_data:
            producto_id = detalle_data['producto_id']
            cantidad = detalle_data['cantidad']

            # Buscar o crear detalle
            detalle, created = DetalleDespacho.objects.get_or_create(
                despacho=despacho,
                producto_id=producto_id,
                defaults={
                    'cantidad_solicitada': cantidad,
                    'cantidad_despachada': cantidad
                }
            )

            if not created:
                detalle.cantidad_despachada += cantidad
                detalle.save()

        # Actualizar estado del despacho
        despacho.fecha_despacho = timezone.now()
        despacho.usuario_despacho = request.user

        if observaciones:
            despacho.observaciones = observaciones

        # Determinar si es parcial o completo
        total_solicitado = sum(d.cantidad_solicitada for d in despacho.detalles.all())
        total_despachado = sum(d.cantidad_despachada for d in despacho.detalles.all())

        if total_despachado >= total_solicitado:
            despacho.estado = 'COMPLETADO'
        else:
            despacho.estado = 'PARCIAL'

        despacho.save()

        return Response(DespachoSerializer(despacho).data)

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """Marca el despacho como completado"""
        despacho = self.get_object()

        if despacho.estado == 'COMPLETADO':
            return Response(
                {'detail': 'El despacho ya está completado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if despacho.estado == 'CANCELADO':
            return Response(
                {'detail': 'No se puede completar un despacho cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        despacho.estado = 'COMPLETADO'
        despacho.fecha_despacho = timezone.now()
        despacho.usuario_despacho = request.user
        despacho.save()

        return Response(DespachoSerializer(despacho).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela el despacho"""
        despacho = self.get_object()

        if despacho.estado == 'COMPLETADO':
            return Response(
                {'detail': 'No se puede cancelar un despacho completado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if despacho.estado == 'CANCELADO':
            return Response(
                {'detail': 'El despacho ya está cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        despacho.estado = 'CANCELADO'
        observaciones = request.data.get('observaciones', '')
        if observaciones:
            despacho.observaciones = observaciones
        despacho.save()

        return Response(DespachoSerializer(despacho).data)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        """Lista los detalles de un despacho"""
        despacho = self.get_object()
        detalles = despacho.detalles.all()
        serializer = DetalleDespachoSerializer(detalles, many=True)
        return Response(serializer.data)


class DetalleDespachoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Detalles de Despacho"""
    queryset = DetalleDespacho.objects.all()
    serializer_class = DetalleDespachoSerializer
    permission_classes = [IsAuthenticated, ActionBasedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['despacho', 'producto']
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('despacho', 'producto', 'lote')

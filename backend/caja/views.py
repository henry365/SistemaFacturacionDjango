from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from .models import Caja, SesionCaja, MovimientoCaja
from .serializers import (
    CajaSerializer, SesionCajaSerializer, SesionCajaListSerializer,
    MovimientoCajaSerializer, CerrarSesionSerializer
)


class CajaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Cajas"""
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activa']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    def perform_create(self, serializer):
        serializer.save(usuario_creacion=self.request.user)

    @action(detail=True, methods=['get'])
    def sesiones(self, request, pk=None):
        """Lista las sesiones de una caja específica"""
        caja = self.get_object()
        sesiones = caja.sesiones.all()
        serializer = SesionCajaListSerializer(sesiones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sesion_activa(self, request, pk=None):
        """Retorna la sesión activa de la caja si existe"""
        caja = self.get_object()
        sesion = caja.sesiones.filter(estado='ABIERTA').first()
        if sesion:
            serializer = SesionCajaSerializer(sesion)
            return Response(serializer.data)
        return Response({'detail': 'No hay sesión activa'}, status=status.HTTP_404_NOT_FOUND)


class SesionCajaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Sesiones de Caja"""
    queryset = SesionCaja.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['caja', 'usuario', 'estado']
    search_fields = ['observaciones']
    ordering_fields = ['fecha_apertura', 'fecha_cierre']
    ordering = ['-fecha_apertura']

    def get_serializer_class(self):
        if self.action == 'list':
            return SesionCajaListSerializer
        return SesionCajaSerializer

    def perform_create(self, serializer):
        caja = serializer.validated_data.get('caja')
        # Verificar que no haya sesión abierta
        if SesionCaja.objects.filter(caja=caja, estado='ABIERTA').exists():
            raise serializers.ValidationError({
                'caja': 'Esta caja ya tiene una sesión abierta'
            })

        sesion = serializer.save(usuario=self.request.user)

        # Crear movimiento de apertura
        MovimientoCaja.objects.create(
            sesion=sesion,
            tipo_movimiento='APERTURA',
            monto=sesion.monto_apertura,
            descripcion='Monto de apertura de caja',
            usuario=self.request.user
        )

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """Cierra una sesión de caja"""
        sesion = self.get_object()

        if sesion.estado != 'ABIERTA':
            return Response(
                {'detail': 'La sesión no está abierta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CerrarSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        monto_usuario = serializer.validated_data['monto_cierre_usuario']
        observaciones = serializer.validated_data.get('observaciones', '')

        # Calcular monto sistema
        ingresos = sesion.movimientos.filter(
            tipo_movimiento__in=['VENTA', 'INGRESO_MANUAL', 'APERTURA']
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

        egresos = sesion.movimientos.filter(
            tipo_movimiento__in=['RETIRO_MANUAL', 'GASTO_MENOR']
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

        monto_sistema = ingresos - egresos

        # Actualizar sesión
        sesion.fecha_cierre = timezone.now()
        sesion.monto_cierre_sistema = monto_sistema
        sesion.monto_cierre_usuario = monto_usuario
        sesion.diferencia = monto_usuario - monto_sistema
        sesion.estado = 'CERRADA'
        sesion.observaciones = observaciones
        sesion.save()

        return Response(SesionCajaSerializer(sesion).data)

    @action(detail=True, methods=['post'])
    def arquear(self, request, pk=None):
        """Marca una sesión como arqueada (verificada)"""
        sesion = self.get_object()

        if sesion.estado != 'CERRADA':
            return Response(
                {'detail': 'La sesión debe estar cerrada para arquear'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sesion.estado = 'ARQUEADA'
        sesion.save()

        return Response(SesionCajaSerializer(sesion).data)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Resumen de la sesión con totales por tipo de movimiento"""
        sesion = self.get_object()

        resumen = {}
        for tipo, _ in MovimientoCaja.TIPO_MOVIMIENTO_CHOICES:
            total = sesion.movimientos.filter(tipo_movimiento=tipo).aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0')
            resumen[tipo.lower()] = float(total)

        ingresos = sum([
            resumen.get('venta', 0),
            resumen.get('ingreso_manual', 0),
            resumen.get('apertura', 0)
        ])
        egresos = sum([
            resumen.get('retiro_manual', 0),
            resumen.get('gasto_menor', 0),
            resumen.get('cierre', 0)
        ])

        return Response({
            'sesion_id': sesion.id,
            'estado': sesion.estado,
            'monto_apertura': float(sesion.monto_apertura),
            'detalle_movimientos': resumen,
            'total_ingresos': ingresos,
            'total_egresos': egresos,
            'saldo_calculado': ingresos - egresos,
            'monto_cierre_sistema': float(sesion.monto_cierre_sistema) if sesion.monto_cierre_sistema else None,
            'monto_cierre_usuario': float(sesion.monto_cierre_usuario) if sesion.monto_cierre_usuario else None,
            'diferencia': float(sesion.diferencia) if sesion.diferencia else None
        })


class MovimientoCajaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Movimientos de Caja"""
    queryset = MovimientoCaja.objects.all()
    serializer_class = MovimientoCajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['sesion', 'tipo_movimiento', 'usuario']
    search_fields = ['descripcion', 'referencia']
    ordering_fields = ['fecha', 'monto']
    ordering = ['-fecha']

    def perform_create(self, serializer):
        sesion = serializer.validated_data.get('sesion')

        # Verificar que la sesión esté abierta
        if sesion.estado != 'ABIERTA':
            raise serializers.ValidationError({
                'sesion': 'No se pueden agregar movimientos a una sesión cerrada'
            })

        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        movimiento = self.get_object()

        # No permitir editar movimientos de sesiones cerradas
        if movimiento.sesion.estado != 'ABIERTA':
            raise serializers.ValidationError({
                'sesion': 'No se pueden editar movimientos de una sesión cerrada'
            })

        serializer.save()

    def perform_destroy(self, instance):
        # No permitir eliminar movimientos de sesiones cerradas
        if instance.sesion.estado != 'ABIERTA':
            raise serializers.ValidationError({
                'sesion': 'No se pueden eliminar movimientos de una sesión cerrada'
            })

        # No permitir eliminar movimiento de apertura
        if instance.tipo_movimiento == 'APERTURA':
            raise serializers.ValidationError({
                'tipo_movimiento': 'No se puede eliminar el movimiento de apertura'
            })

        instance.delete()

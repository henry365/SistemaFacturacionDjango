from rest_framework import serializers
from .models import Caja, SesionCaja, MovimientoCaja
from django.db.models import Sum


class CajaSerializer(serializers.ModelSerializer):
    sesiones_count = serializers.SerializerMethodField()

    class Meta:
        model = Caja
        fields = [
            'id', 'uuid', 'nombre', 'descripcion', 'activa',
            'fecha_creacion', 'usuario_creacion', 'sesiones_count'
        ]
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'usuario_creacion')

    def get_sesiones_count(self, obj):
        return obj.sesiones.count()


class MovimientoCajaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)

    class Meta:
        model = MovimientoCaja
        fields = [
            'id', 'uuid', 'sesion', 'tipo_movimiento', 'tipo_movimiento_display',
            'monto', 'descripcion', 'fecha', 'referencia', 'usuario', 'usuario_nombre'
        ]
        read_only_fields = ('id', 'uuid', 'fecha', 'usuario')


class SesionCajaSerializer(serializers.ModelSerializer):
    caja_nombre = serializers.CharField(source='caja.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    movimientos = MovimientoCajaSerializer(many=True, read_only=True)
    total_ingresos = serializers.SerializerMethodField()
    total_egresos = serializers.SerializerMethodField()

    class Meta:
        model = SesionCaja
        fields = [
            'id', 'uuid', 'caja', 'caja_nombre', 'usuario', 'usuario_nombre',
            'fecha_apertura', 'monto_apertura', 'fecha_cierre',
            'monto_cierre_sistema', 'monto_cierre_usuario', 'diferencia',
            'estado', 'estado_display', 'observaciones', 'movimientos',
            'total_ingresos', 'total_egresos'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha_apertura', 'fecha_cierre',
            'monto_cierre_sistema', 'diferencia', 'usuario'
        )

    def get_total_ingresos(self, obj):
        """Suma de movimientos de entrada"""
        tipos_ingreso = ['VENTA', 'INGRESO_MANUAL', 'APERTURA']
        total = obj.movimientos.filter(tipo_movimiento__in=tipos_ingreso).aggregate(
            total=Sum('monto')
        )['total']
        return total or 0

    def get_total_egresos(self, obj):
        """Suma de movimientos de salida"""
        tipos_egreso = ['RETIRO_MANUAL', 'GASTO_MENOR', 'CIERRE']
        total = obj.movimientos.filter(tipo_movimiento__in=tipos_egreso).aggregate(
            total=Sum('monto')
        )['total']
        return total or 0


class SesionCajaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    caja_nombre = serializers.CharField(source='caja.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    movimientos_count = serializers.SerializerMethodField()

    class Meta:
        model = SesionCaja
        fields = [
            'id', 'uuid', 'caja', 'caja_nombre', 'usuario', 'usuario_nombre',
            'fecha_apertura', 'monto_apertura', 'fecha_cierre',
            'monto_cierre_sistema', 'monto_cierre_usuario', 'diferencia',
            'estado', 'estado_display', 'movimientos_count'
        ]

    def get_movimientos_count(self, obj):
        return obj.movimientos.count()


class CerrarSesionSerializer(serializers.Serializer):
    """Serializer para cerrar sesión de caja"""
    monto_cierre_usuario = serializers.DecimalField(max_digits=14, decimal_places=2)
    observaciones = serializers.CharField(required=False, allow_blank=True)

"""
Serializers para el módulo de Caja

Este módulo contiene los serializers para Cajas, Sesiones y Movimientos,
siguiendo los estándares de la Guía Inicial.
"""
from rest_framework import serializers
from django.db.models import Sum

from .models import Caja, SesionCaja, MovimientoCaja
from .constants import (
    TIPOS_INGRESO, TIPOS_EGRESO,
    TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR
)


# ============================================================
# SERIALIZERS DE CAJA
# ============================================================

class CajaSerializer(serializers.ModelSerializer):
    """Serializer completo para Caja"""
    sesiones_count = serializers.SerializerMethodField()
    tiene_sesion_abierta = serializers.SerializerMethodField()
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username', read_only=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username', read_only=True
    )

    class Meta:
        model = Caja
        fields = [
            'id', 'uuid', 'nombre', 'descripcion', 'activa',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_creacion_nombre',
            'usuario_modificacion', 'usuario_modificacion_nombre',
            'sesiones_count', 'tiene_sesion_abierta'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        )

    def get_sesiones_count(self, obj):
        return obj.sesiones.count()

    def get_tiene_sesion_abierta(self, obj):
        return obj.tiene_sesion_abierta()

    def validate_nombre(self, value):
        """Validar nombre no vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError('El nombre no puede estar vacío.')
        return value.strip()


class CajaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de Cajas"""
    sesiones_count = serializers.SerializerMethodField()
    tiene_sesion_abierta = serializers.SerializerMethodField()

    class Meta:
        model = Caja
        fields = [
            'id', 'uuid', 'nombre', 'descripcion', 'activa',
            'fecha_creacion', 'sesiones_count', 'tiene_sesion_abierta'
        ]

    def get_sesiones_count(self, obj):
        return obj.sesiones.count()

    def get_tiene_sesion_abierta(self, obj):
        return obj.tiene_sesion_abierta()


# ============================================================
# SERIALIZERS DE MOVIMIENTO
# ============================================================

class MovimientoCajaSerializer(serializers.ModelSerializer):
    """Serializer completo para MovimientoCaja"""
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    tipo_movimiento_display = serializers.CharField(
        source='get_tipo_movimiento_display', read_only=True
    )
    es_ingreso = serializers.BooleanField(read_only=True)
    es_egreso = serializers.BooleanField(read_only=True)
    sesion_estado = serializers.CharField(source='sesion.estado', read_only=True)
    caja_nombre = serializers.CharField(source='sesion.caja.nombre', read_only=True)

    class Meta:
        model = MovimientoCaja
        fields = [
            'id', 'uuid', 'sesion', 'sesion_estado', 'caja_nombre',
            'tipo_movimiento', 'tipo_movimiento_display',
            'monto', 'descripcion', 'fecha', 'referencia',
            'usuario', 'usuario_nombre',
            'es_ingreso', 'es_egreso',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha', 'usuario',
            'fecha_creacion', 'fecha_actualizacion'
        )

    def validate_monto(self, value):
        """Validar monto positivo"""
        if value is None or value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a cero.')
        return value

    def validate_tipo_movimiento(self, value):
        """Validar tipo de movimiento permitido para creación manual"""
        tipos_permitidos = [TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR]
        if value not in tipos_permitidos:
            raise serializers.ValidationError(
                f'Tipo de movimiento no permitido. Use: {tipos_permitidos}'
            )
        return value

    def validate_sesion(self, value):
        """
        Valida que la sesión pertenezca a la empresa del usuario.

        Args:
            value: Instancia de SesionCaja a validar

        Returns:
            SesionCaja: La sesión validada

        Raises:
            ValidationError: Si la sesión no pertenece a la empresa del usuario
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if user_empresa and value.empresa and value.empresa != user_empresa:
                raise serializers.ValidationError(
                    'La sesión no pertenece a su empresa.'
                )
        return value


class MovimientoCajaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de Movimientos"""
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    tipo_movimiento_display = serializers.CharField(
        source='get_tipo_movimiento_display', read_only=True
    )
    caja_nombre = serializers.CharField(source='sesion.caja.nombre', read_only=True)

    class Meta:
        model = MovimientoCaja
        fields = [
            'id', 'uuid', 'sesion', 'caja_nombre',
            'tipo_movimiento', 'tipo_movimiento_display',
            'monto', 'descripcion', 'fecha', 'referencia',
            'usuario_nombre'
        ]


# ============================================================
# SERIALIZERS DE SESION
# ============================================================

class SesionCajaSerializer(serializers.ModelSerializer):
    """Serializer completo para SesionCaja"""
    caja_nombre = serializers.CharField(source='caja.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    movimientos = MovimientoCajaListSerializer(many=True, read_only=True)
    total_ingresos = serializers.SerializerMethodField()
    total_egresos = serializers.SerializerMethodField()
    saldo_actual = serializers.SerializerMethodField()
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username', read_only=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username', read_only=True
    )

    class Meta:
        model = SesionCaja
        fields = [
            'id', 'uuid', 'caja', 'caja_nombre', 'usuario', 'usuario_nombre',
            'fecha_apertura', 'monto_apertura', 'fecha_cierre',
            'monto_cierre_sistema', 'monto_cierre_usuario', 'diferencia',
            'estado', 'estado_display', 'observaciones',
            'movimientos', 'total_ingresos', 'total_egresos', 'saldo_actual',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_creacion_nombre',
            'usuario_modificacion', 'usuario_modificacion_nombre'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha_apertura', 'fecha_cierre',
            'monto_cierre_sistema', 'diferencia', 'usuario',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        )

    def validate_caja(self, value):
        """
        Valida que la caja pertenezca a la empresa del usuario.

        Args:
            value: Instancia de Caja a validar

        Returns:
            Caja: La caja validada

        Raises:
            ValidationError: Si la caja no pertenece a la empresa del usuario
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if user_empresa and value.empresa and value.empresa != user_empresa:
                raise serializers.ValidationError(
                    'La caja no pertenece a su empresa.'
                )
        return value

    def get_total_ingresos(self, obj):
        """Suma de movimientos de entrada"""
        total = obj.movimientos.filter(
            tipo_movimiento__in=TIPOS_INGRESO
        ).aggregate(total=Sum('monto'))['total']
        return total or 0

    def get_total_egresos(self, obj):
        """Suma de movimientos de salida (excluyendo cierre)"""
        tipos_egreso_sin_cierre = [t for t in TIPOS_EGRESO if t != 'CIERRE']
        total = obj.movimientos.filter(
            tipo_movimiento__in=tipos_egreso_sin_cierre
        ).aggregate(total=Sum('monto'))['total']
        return total or 0

    def get_saldo_actual(self, obj):
        """Calcula el saldo actual de la sesión"""
        ingresos = self.get_total_ingresos(obj)
        egresos = self.get_total_egresos(obj)
        return ingresos - egresos


class SesionCajaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de Sesiones"""
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


# ============================================================
# SERIALIZERS DE ACCIONES
# ============================================================

class AbrirSesionSerializer(serializers.Serializer):
    """Serializer para abrir sesión de caja"""
    caja = serializers.PrimaryKeyRelatedField(queryset=Caja.objects.all())
    monto_apertura = serializers.DecimalField(max_digits=14, decimal_places=2)
    observaciones = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_monto_apertura(self, value):
        """Validar monto no negativo"""
        if value is not None and value < 0:
            raise serializers.ValidationError('El monto de apertura no puede ser negativo.')
        return value

    def validate_caja(self, value):
        """
        Valida que la caja esté activa y pertenezca a la empresa del usuario.

        Args:
            value: Instancia de Caja a validar

        Returns:
            Caja: La caja validada

        Raises:
            ValidationError: Si la caja no está activa o no pertenece a la empresa
        """
        # Validar empresa
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if user_empresa and value.empresa and value.empresa != user_empresa:
                raise serializers.ValidationError(
                    'La caja no pertenece a su empresa.'
                )

        # Validar que esté activa
        if not value.activa:
            raise serializers.ValidationError('La caja no está activa.')

        return value


class CerrarSesionSerializer(serializers.Serializer):
    """Serializer para cerrar sesión de caja"""
    monto_cierre_usuario = serializers.DecimalField(max_digits=14, decimal_places=2)
    observaciones = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_monto_cierre_usuario(self, value):
        """Validar monto no negativo"""
        if value is not None and value < 0:
            raise serializers.ValidationError('El monto de cierre no puede ser negativo.')
        return value

"""
Serializers para Cuentas por Cobrar
"""
from rest_framework import serializers
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = CuentaPorCobrar
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente', 'cliente_nombre',
            'factura', 'numero_documento', 'fecha_documento', 'fecha_vencimiento',
            'fecha_registro', 'monto_original', 'monto_cobrado', 'monto_pendiente',
            'estado', 'estado_display', 'observaciones',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente_nombre',
            'monto_cobrado', 'estado_display', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]


class DetalleCobroClienteSerializer(serializers.ModelSerializer):
    cuenta_numero_documento = serializers.CharField(source='cuenta_por_cobrar.numero_documento', read_only=True)

    class Meta:
        model = DetalleCobroCliente
        fields = ['id', 'cobro', 'cuenta_por_cobrar', 'cuenta_numero_documento', 'monto_aplicado']
        read_only_fields = ['id', 'cuenta_numero_documento']


class CobroClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    detalles = DetalleCobroClienteSerializer(many=True, read_only=True)

    class Meta:
        model = CobroCliente
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente', 'cliente_nombre',
            'numero_recibo', 'fecha_cobro', 'monto', 'metodo_pago', 'metodo_pago_display',
            'referencia', 'observaciones', 'detalles',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente_nombre',
            'metodo_pago_display', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]


class AplicarCobroSerializer(serializers.Serializer):
    """Serializer para aplicar un cobro a multiples cuentas por cobrar"""
    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de {cuenta_por_cobrar_id, monto_aplicado}"
    )

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe proporcionar al menos un detalle de cobro.")

        for detalle in value:
            if 'cuenta_por_cobrar_id' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener cuenta_por_cobrar_id.")
            if 'monto_aplicado' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener monto_aplicado.")
            if float(detalle['monto_aplicado']) <= 0:
                raise serializers.ValidationError("El monto aplicado debe ser mayor a cero.")

        return value

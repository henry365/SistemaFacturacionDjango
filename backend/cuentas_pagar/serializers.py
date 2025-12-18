"""
Serializers para Cuentas por Pagar
"""
from rest_framework import serializers
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor


class CuentaPorPagarSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = CuentaPorPagar
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor', 'proveedor_nombre',
            'compra', 'numero_documento', 'fecha_documento', 'fecha_vencimiento',
            'fecha_registro', 'monto_original', 'monto_pagado', 'monto_pendiente',
            'estado', 'estado_display', 'observaciones',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor_nombre',
            'monto_pagado', 'estado_display', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]


class DetallePagoProveedorSerializer(serializers.ModelSerializer):
    cuenta_numero_documento = serializers.CharField(source='cuenta_por_pagar.numero_documento', read_only=True)

    class Meta:
        model = DetallePagoProveedor
        fields = ['id', 'pago', 'cuenta_por_pagar', 'cuenta_numero_documento', 'monto_aplicado']
        read_only_fields = ['id', 'cuenta_numero_documento']


class PagoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    detalles = DetallePagoProveedorSerializer(many=True, read_only=True)

    class Meta:
        model = PagoProveedor
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor', 'proveedor_nombre',
            'numero_pago', 'fecha_pago', 'monto', 'metodo_pago', 'metodo_pago_display',
            'referencia', 'observaciones', 'detalles',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor_nombre',
            'metodo_pago_display', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]


class AplicarPagoSerializer(serializers.Serializer):
    """Serializer para aplicar un pago a multiples cuentas por pagar"""
    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de {cuenta_por_pagar_id, monto_aplicado}"
    )

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe proporcionar al menos un detalle de pago.")

        for detalle in value:
            if 'cuenta_por_pagar_id' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener cuenta_por_pagar_id.")
            if 'monto_aplicado' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener monto_aplicado.")
            if float(detalle['monto_aplicado']) <= 0:
                raise serializers.ValidationError("El monto aplicado debe ser mayor a cero.")

        return value

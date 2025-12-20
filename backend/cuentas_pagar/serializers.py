"""
Serializers para Cuentas por Pagar
"""
from rest_framework import serializers
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from .constants import ERROR_PROVEEDOR_EMPRESA, ERROR_COMPRA_EMPRESA


class CuentaPorPagarSerializer(serializers.ModelSerializer):
    """
    Serializer para CuentaPorPagar.

    Incluye validación de empresa para proveedor y compra.
    """
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
            'monto_pagado', 'monto_pendiente', 'estado_display',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def validate(self, attrs):
        """Validar que proveedor y compra pertenezcan a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'empresa', None) if request else None

        if not empresa and self.instance:
            empresa = self.instance.empresa

        proveedor = attrs.get('proveedor') or (self.instance.proveedor if self.instance else None)
        compra = attrs.get('compra') or (self.instance.compra if self.instance else None)

        if empresa and proveedor and proveedor.empresa_id != empresa.id:
            raise serializers.ValidationError({'proveedor': ERROR_PROVEEDOR_EMPRESA})

        if empresa and compra and compra.empresa_id != empresa.id:
            raise serializers.ValidationError({'compra': ERROR_COMPRA_EMPRESA})

        return attrs


class DetallePagoProveedorSerializer(serializers.ModelSerializer):
    """
    Serializer para DetallePagoProveedor.

    Incluye validación de empresa.
    """
    cuenta_numero_documento = serializers.CharField(
        source='cuenta_por_pagar.numero_documento', read_only=True
    )
    cuenta_monto_pendiente = serializers.DecimalField(
        source='cuenta_por_pagar.monto_pendiente',
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = DetallePagoProveedor
        fields = [
            'id', 'uuid', 'empresa', 'pago', 'cuenta_por_pagar',
            'cuenta_numero_documento', 'cuenta_monto_pendiente', 'monto_aplicado',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'cuenta_numero_documento',
            'cuenta_monto_pendiente', 'fecha_creacion', 'fecha_actualizacion'
        ]


class PagoProveedorSerializer(serializers.ModelSerializer):
    """
    Serializer para PagoProveedor.

    Incluye validación de empresa para proveedor.
    """
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    detalles = DetallePagoProveedorSerializer(many=True, read_only=True)
    monto_disponible = serializers.SerializerMethodField()

    class Meta:
        model = PagoProveedor
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor', 'proveedor_nombre',
            'numero_pago', 'fecha_pago', 'monto', 'metodo_pago', 'metodo_pago_display',
            'referencia', 'observaciones', 'detalles', 'monto_disponible',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'proveedor_nombre',
            'metodo_pago_display', 'monto_disponible',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def get_monto_disponible(self, obj):
        """Calcula el monto disponible para aplicar."""
        from django.db.models import Sum
        aplicado = obj.detalles.aggregate(total=Sum('monto_aplicado'))['total'] or 0
        return obj.monto - aplicado

    def validate(self, attrs):
        """Validar que el proveedor pertenezca a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'empresa', None) if request else None

        if not empresa and self.instance:
            empresa = self.instance.empresa

        proveedor = attrs.get('proveedor') or (self.instance.proveedor if self.instance else None)

        if empresa and proveedor and proveedor.empresa_id != empresa.id:
            raise serializers.ValidationError({'proveedor': ERROR_PROVEEDOR_EMPRESA})

        return attrs


class AplicarPagoSerializer(serializers.Serializer):
    """Serializer para aplicar un pago a múltiples cuentas por pagar."""

    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de {cuenta_por_pagar_id, monto_aplicado}"
    )

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un detalle de pago."
            )

        for detalle in value:
            if 'cuenta_por_pagar_id' not in detalle:
                raise serializers.ValidationError(
                    "Cada detalle debe tener cuenta_por_pagar_id."
                )
            if 'monto_aplicado' not in detalle:
                raise serializers.ValidationError(
                    "Cada detalle debe tener monto_aplicado."
                )
            if float(detalle['monto_aplicado']) <= 0:
                raise serializers.ValidationError(
                    "El monto aplicado debe ser mayor a cero."
                )

        return value

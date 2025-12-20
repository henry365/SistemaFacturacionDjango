"""
Serializers para Cuentas por Cobrar
"""
from rest_framework import serializers
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from .constants import ERROR_CLIENTE_EMPRESA, ERROR_FACTURA_EMPRESA


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    """
    Serializer para CuentaPorCobrar.

    Incluye validación de empresa para cliente y factura.
    """
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
            'monto_cobrado', 'monto_pendiente', 'estado_display',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def validate(self, attrs):
        """Validar que cliente y factura pertenezcan a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'empresa', None) if request else None

        if not empresa and self.instance:
            empresa = self.instance.empresa

        cliente = attrs.get('cliente') or (self.instance.cliente if self.instance else None)
        factura = attrs.get('factura') or (self.instance.factura if self.instance else None)

        if empresa and cliente and cliente.empresa_id != empresa.id:
            raise serializers.ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if empresa and factura and factura.empresa_id != empresa.id:
            raise serializers.ValidationError({'factura': ERROR_FACTURA_EMPRESA})

        return attrs


class DetalleCobroClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para DetalleCobroCliente.

    Incluye validación de empresa.
    """
    cuenta_numero_documento = serializers.CharField(
        source='cuenta_por_cobrar.numero_documento', read_only=True
    )
    cuenta_monto_pendiente = serializers.DecimalField(
        source='cuenta_por_cobrar.monto_pendiente',
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = DetalleCobroCliente
        fields = [
            'id', 'uuid', 'empresa', 'cobro', 'cuenta_por_cobrar',
            'cuenta_numero_documento', 'cuenta_monto_pendiente', 'monto_aplicado',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'cuenta_numero_documento',
            'cuenta_monto_pendiente', 'fecha_creacion', 'fecha_actualizacion'
        ]


class CobroClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para CobroCliente.

    Incluye validación de empresa para cliente.
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    detalles = DetalleCobroClienteSerializer(many=True, read_only=True)
    monto_disponible = serializers.SerializerMethodField()

    class Meta:
        model = CobroCliente
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente', 'cliente_nombre',
            'numero_recibo', 'fecha_cobro', 'monto', 'metodo_pago', 'metodo_pago_display',
            'referencia', 'observaciones', 'detalles', 'monto_disponible',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'cliente_nombre',
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
        """Validar que el cliente pertenezca a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'empresa', None) if request else None

        if not empresa and self.instance:
            empresa = self.instance.empresa

        cliente = attrs.get('cliente') or (self.instance.cliente if self.instance else None)

        if empresa and cliente and cliente.empresa_id != empresa.id:
            raise serializers.ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        return attrs


class AplicarCobroSerializer(serializers.Serializer):
    """Serializer para aplicar un cobro a múltiples cuentas por cobrar."""

    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de {cuenta_por_cobrar_id, monto_aplicado}"
    )

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un detalle de cobro."
            )

        for detalle in value:
            if 'cuenta_por_cobrar_id' not in detalle:
                raise serializers.ValidationError(
                    "Cada detalle debe tener cuenta_por_cobrar_id."
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


class AplicarCobroDetalleSerializer(serializers.Serializer):
    """Serializer para un detalle individual de aplicación de cobro."""

    cuenta_por_cobrar_id = serializers.IntegerField()
    monto_aplicado = serializers.DecimalField(max_digits=14, decimal_places=2)

    def validate_monto_aplicado(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto aplicado debe ser mayor a cero."
            )
        return value

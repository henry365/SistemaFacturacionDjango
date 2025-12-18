from rest_framework import serializers
from .models import Despacho, DetalleDespacho


class DetalleDespachoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)

    class Meta:
        model = DetalleDespacho
        fields = '__all__'
        read_only_fields = ('id',)


class DespachoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    cliente_rnc = serializers.ReadOnlyField(source='cliente.rnc')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    usuario_creacion_nombre = serializers.ReadOnlyField(source='usuario_creacion.username', allow_null=True)
    usuario_despacho_nombre = serializers.ReadOnlyField(source='usuario_despacho.username', allow_null=True)
    detalles = DetalleDespachoSerializer(many=True, read_only=True)

    class Meta:
        model = Despacho
        fields = '__all__'
        read_only_fields = (
            'id', 'uuid', 'fecha', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'usuario_despacho', 'empresa'
        )

    def validate(self, data):
        """Validaciones de negocio"""
        factura = data.get('factura') or (self.instance.factura if self.instance else None)
        cliente = data.get('cliente') or (self.instance.cliente if self.instance else None)

        # Verificar que cliente coincida con la factura
        if factura and cliente:
            if factura.cliente != cliente:
                raise serializers.ValidationError({
                    "cliente": "El cliente debe coincidir con el cliente de la factura."
                })

        return data


class DespacharSerializer(serializers.Serializer):
    """Serializer para la acción de despachar"""
    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de detalles a despachar [{producto_id, cantidad}]"
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe especificar al menos un detalle a despachar.")
        for detalle in value:
            if 'producto_id' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener 'producto_id'.")
            if 'cantidad' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener 'cantidad'.")
            if float(detalle['cantidad']) <= 0:
                raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
        return value

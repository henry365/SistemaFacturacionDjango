"""
Serializers para el módulo de Despachos

Incluye validación de empresa en relaciones para garantizar
aislamiento multi-tenant.
"""
from rest_framework import serializers
from .models import Despacho, DetalleDespacho
from .constants import (
    ERROR_FACTURA_OTRA_EMPRESA, ERROR_CLIENTE_OTRA_EMPRESA,
    ERROR_ALMACEN_OTRA_EMPRESA, ERROR_CLIENTE_FACTURA
)


class DetalleDespachoSerializer(serializers.ModelSerializer):
    """Serializer para DetalleDespacho"""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)

    class Meta:
        model = DetalleDespacho
        fields = '__all__'
        read_only_fields = (
            'id', 'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'cantidad'
        )


class DespachoSerializer(serializers.ModelSerializer):
    """Serializer para Despacho con validación de empresa"""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    cliente_rnc = serializers.ReadOnlyField(source='cliente.rnc')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    usuario_creacion_nombre = serializers.ReadOnlyField(
        source='usuario_creacion.username',
        allow_null=True
    )
    usuario_despacho_nombre = serializers.ReadOnlyField(
        source='usuario_despacho.username',
        allow_null=True
    )
    detalles = DetalleDespachoSerializer(many=True, read_only=True)

    class Meta:
        model = Despacho
        fields = '__all__'
        read_only_fields = (
            'id', 'uuid', 'fecha', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'usuario_despacho', 'empresa'
        )

    def validate_factura(self, value):
        """Valida que la factura pertenezca a la misma empresa del usuario"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(ERROR_FACTURA_OTRA_EMPRESA)
        return value

    def validate_cliente(self, value):
        """Valida que el cliente pertenezca a la misma empresa del usuario"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(ERROR_CLIENTE_OTRA_EMPRESA)
        return value

    def validate_almacen(self, value):
        """Valida que el almacén pertenezca a la misma empresa del usuario"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(ERROR_ALMACEN_OTRA_EMPRESA)
        return value

    def validate(self, data):
        """Validaciones de negocio"""
        factura = data.get('factura') or (self.instance.factura if self.instance else None)
        cliente = data.get('cliente') or (self.instance.cliente if self.instance else None)

        # Verificar que cliente coincida con la factura
        if factura and cliente:
            if hasattr(factura, 'cliente') and factura.cliente:
                if factura.cliente != cliente:
                    raise serializers.ValidationError({
                        "cliente": ERROR_CLIENTE_FACTURA
                    })

        return data


class DespachoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados (menos campos)"""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    total_productos = serializers.SerializerMethodField()

    class Meta:
        model = Despacho
        fields = [
            'id', 'uuid', 'factura', 'factura_numero',
            'cliente', 'cliente_nombre',
            'almacen', 'almacen_nombre',
            'estado', 'estado_display',
            'fecha', 'fecha_despacho',
            'numero_guia', 'total_productos'
        ]

    def get_total_productos(self, obj):
        """Obtiene el total de productos en el despacho"""
        return obj.detalles.count()


class DespacharSerializer(serializers.Serializer):
    """Serializer para la acción de despachar"""
    detalles = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de detalles a despachar [{producto_id, cantidad}]"
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate_detalles(self, value):
        """Valida la estructura de los detalles"""
        if not value:
            raise serializers.ValidationError(
                "Debe especificar al menos un detalle a despachar."
            )

        for i, detalle in enumerate(value):
            if 'producto_id' not in detalle:
                raise serializers.ValidationError(
                    f"Detalle {i+1}: Falta 'producto_id'."
                )
            if 'cantidad' not in detalle:
                raise serializers.ValidationError(
                    f"Detalle {i+1}: Falta 'cantidad'."
                )
            try:
                cantidad = float(detalle['cantidad'])
                if cantidad <= 0:
                    raise serializers.ValidationError(
                        f"Detalle {i+1}: La cantidad debe ser mayor a cero."
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Detalle {i+1}: Cantidad inválida."
                )

        return value


class CancelarSerializer(serializers.Serializer):
    """Serializer para la acción de cancelar"""
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Motivo de la cancelación"
    )

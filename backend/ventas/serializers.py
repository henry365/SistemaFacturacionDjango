"""
Serializers para el módulo Ventas

Incluye serializers completos y List serializers optimizados para listados.
"""
from rest_framework import serializers
from .models import (
    CotizacionCliente, DetalleCotizacion,
    Factura, DetalleFactura,
    PagoCaja, NotaCredito, NotaDebito,
    DevolucionVenta, DetalleDevolucion,
    ListaEsperaProducto
)
from .constants import (
    ERROR_CLIENTE_EMPRESA, ERROR_VENDEDOR_EMPRESA,
    ERROR_TOTAL_NEGATIVO, ERROR_MONTO_MAYOR_CERO,
    ERROR_CANTIDAD_INVALIDA, ERROR_MOTIVO_VACIO,
)


# =============================================================================
# Lista de Espera
# =============================================================================

class ListaEsperaProductoSerializer(serializers.ModelSerializer):
    """Serializer completo para lista de espera."""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = ListaEsperaProducto
        fields = '__all__'

    def validate_cantidad_solicitada(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_CANTIDAD_INVALIDA)
        return value


class ListaEsperaProductoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de listas de espera."""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')

    class Meta:
        model = ListaEsperaProducto
        fields = [
            'id', 'producto_nombre', 'cliente_nombre',
            'cantidad_solicitada', 'estado', 'prioridad', 'fecha_solicitud'
        ]


# =============================================================================
# Cotizaciones
# =============================================================================

class DetalleCotizacionSerializer(serializers.ModelSerializer):
    """Serializer completo para detalles de cotización."""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleCotizacion
        fields = '__all__'

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_CANTIDAD_INVALIDA)
        return value


class CotizacionClienteSerializer(serializers.ModelSerializer):
    """Serializer completo para cotizaciones."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleCotizacionSerializer(many=True, read_only=True)

    class Meta:
        model = CotizacionCliente
        fields = '__all__'

    def validate_total(self, value):
        if value < 0:
            raise serializers.ValidationError(ERROR_TOTAL_NEGATIVO)
        return value


class CotizacionClienteListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de cotizaciones."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')

    class Meta:
        model = CotizacionCliente
        fields = [
            'id', 'cliente_nombre', 'vendedor_nombre',
            'fecha', 'vigencia', 'estado', 'total'
        ]


# =============================================================================
# Facturas
# =============================================================================

class DetalleFacturaSerializer(serializers.ModelSerializer):
    """Serializer completo para detalles de factura."""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleFactura
        fields = '__all__'

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_CANTIDAD_INVALIDA)
        return value


class FacturaSerializer(serializers.ModelSerializer):
    """Serializer completo para facturas."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'

    def validate_total(self, value):
        if value < 0:
            raise serializers.ValidationError(ERROR_TOTAL_NEGATIVO)
        return value


class FacturaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de facturas."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')

    class Meta:
        model = Factura
        fields = [
            'id', 'numero_factura', 'cliente_nombre', 'vendedor_nombre',
            'fecha', 'estado', 'tipo_venta', 'total', 'monto_pendiente'
        ]


# =============================================================================
# Pagos
# =============================================================================

class PagoCajaSerializer(serializers.ModelSerializer):
    """Serializer completo para pagos en caja."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = PagoCaja
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_MONTO_MAYOR_CERO)
        return value


class PagoCajaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de pagos."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')

    class Meta:
        model = PagoCaja
        fields = [
            'id', 'cliente_nombre', 'fecha_pago',
            'monto', 'metodo_pago', 'referencia'
        ]


# =============================================================================
# Notas de Crédito
# =============================================================================

class NotaCreditoSerializer(serializers.ModelSerializer):
    """Serializer completo para notas de crédito."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')

    class Meta:
        model = NotaCredito
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_MONTO_MAYOR_CERO)
        return value

    def validate_motivo(self, value):
        if value:
            value = value.strip()
            if not value:
                raise serializers.ValidationError(ERROR_MOTIVO_VACIO)
        return value


class NotaCreditoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de notas de crédito."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')

    class Meta:
        model = NotaCredito
        fields = [
            'id', 'cliente_nombre', 'factura_numero',
            'fecha', 'monto', 'aplicada'
        ]


# =============================================================================
# Notas de Débito
# =============================================================================

class NotaDebitoSerializer(serializers.ModelSerializer):
    """Serializer completo para notas de débito."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')

    class Meta:
        model = NotaDebito
        fields = '__all__'

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_MONTO_MAYOR_CERO)
        return value

    def validate_motivo(self, value):
        if value:
            value = value.strip()
            if not value:
                raise serializers.ValidationError(ERROR_MOTIVO_VACIO)
        return value


class NotaDebitoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de notas de débito."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')

    class Meta:
        model = NotaDebito
        fields = [
            'id', 'cliente_nombre', 'factura_numero',
            'fecha', 'monto'
        ]


# =============================================================================
# Devoluciones
# =============================================================================

class DetalleDevolucionSerializer(serializers.ModelSerializer):
    """Serializer completo para detalles de devolución."""
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleDevolucion
        fields = '__all__'

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError(ERROR_CANTIDAD_INVALIDA)
        return value


class DevolucionVentaSerializer(serializers.ModelSerializer):
    """Serializer completo para devoluciones de venta."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')
    detalles = DetalleDevolucionSerializer(many=True, read_only=True)

    class Meta:
        model = DevolucionVenta
        fields = '__all__'

    def validate_motivo(self, value):
        if value:
            value = value.strip()
            if not value:
                raise serializers.ValidationError(ERROR_MOTIVO_VACIO)
        return value


class DevolucionVentaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de devoluciones."""
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    factura_numero = serializers.ReadOnlyField(source='factura.numero_factura')

    class Meta:
        model = DevolucionVenta
        fields = [
            'id', 'factura_numero', 'cliente_nombre', 'fecha'
        ]

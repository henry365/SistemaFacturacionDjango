from rest_framework import serializers
from .models import (
    CotizacionCliente, DetalleCotizacion,
    Factura, DetalleFactura,
    PagoCaja, NotaCredito, NotaDebito,
    DevolucionVenta, DetalleDevolucion,
    ListaEsperaProducto
)

# --- Lista de Espera ---
class ListaEsperaProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    
    class Meta:
        model = ListaEsperaProducto
        fields = '__all__'

# --- Cotizaciones ---
class DetalleCotizacionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    
    class Meta:
        model = DetalleCotizacion
        fields = '__all__'

class CotizacionClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')
    detalles = DetalleCotizacionSerializer(many=True, read_only=True)

    class Meta:
        model = CotizacionCliente
        fields = '__all__'

# --- Facturas ---
class DetalleFacturaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleFactura
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor.nombre')
    detalles = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'

# --- Pagos ---
class PagoCajaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    
    class Meta:
        model = PagoCaja
        fields = '__all__'

# --- Notas y Devoluciones ---
class NotaCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaCredito
        fields = '__all__'

class NotaDebitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaDebito
        fields = '__all__'

class DetalleDevolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleDevolucion
        fields = '__all__'

class DevolucionVentaSerializer(serializers.ModelSerializer):
    detalles = DetalleDevolucionSerializer(many=True, read_only=True)
    class Meta:
        model = DevolucionVenta
        fields = '__all__'

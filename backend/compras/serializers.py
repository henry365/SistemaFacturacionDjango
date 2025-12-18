from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from core.mixins import ProveedorEmpresaValidatorMixin
from .models import (
    SolicitudCotizacionProveedor,
    OrdenCompra,
    DetalleOrdenCompra,
    Compra,
    DetalleCompra,
    Gasto,
    RecepcionCompra,
    DetalleRecepcion,
    DevolucionProveedor,
    DetalleDevolucionProveedor,
    LiquidacionImportacion,
    GastoImportacion,
    TipoRetencion,
    RetencionCompra
)
from proveedores.serializers import ProveedorSerializer
from productos.serializers import ProductoSerializer

# --- Solicitudes ---
class SolicitudCotizacionProveedorSerializer(ProveedorEmpresaValidatorMixin, serializers.ModelSerializer):
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = SolicitudCotizacionProveedor
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

# --- Ordenes de Compra ---
class DetalleOrdenCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleOrdenCompra
        fields = '__all__'
        read_only_fields = ('id', 'subtotal')

class OrdenCompraSerializer(ProveedorEmpresaValidatorMixin, serializers.ModelSerializer):
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleOrdenCompraSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenCompra
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'usuario_aprobacion', 'empresa')

# --- Compras (Facturas Proveedor) ---
class DetalleCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetalleCompra
        fields = '__all__'
        read_only_fields = ('id',)

class CompraSerializer(ProveedorEmpresaValidatorMixin, serializers.ModelSerializer):
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'fecha_registro', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate(self, data):
        """Validar unicidad de factura por empresa"""
        data = super().validate(data)  # Llamar al mixin primero
        
        proveedor = data.get('proveedor') or (self.instance.proveedor if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        numero_factura = data.get('numero_factura_proveedor') or (self.instance.numero_factura_proveedor if self.instance else None)
        
        # Validar unicidad de factura por empresa
        if numero_factura and empresa and proveedor:
            queryset = Compra.objects.filter(empresa=empresa, proveedor=proveedor, numero_factura_proveedor=numero_factura)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    "numero_factura_proveedor": f"Ya existe una compra con este número de factura para este proveedor en la empresa {empresa.nombre}."
                })
        
        return data

# --- Gastos ---
class GastoSerializer(ProveedorEmpresaValidatorMixin, serializers.ModelSerializer):
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = Gasto
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')


# --- Recepciones de Compra ---
class DetalleRecepcionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo = serializers.ReadOnlyField(source='producto.codigo_sku')

    class Meta:
        model = DetalleRecepcion
        fields = '__all__'
        read_only_fields = ('id',)


class RecepcionCompraSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    orden_compra_numero = serializers.ReadOnlyField(source='orden_compra.id')
    proveedor_nombre = serializers.ReadOnlyField(source='orden_compra.proveedor.nombre')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    detalles = DetalleRecepcionSerializer(many=True, read_only=True)

    class Meta:
        model = RecepcionCompra
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'numero_recepcion', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

    def validate(self, data):
        orden_compra = data.get('orden_compra')
        empresa = self.context['request'].user.empresa if hasattr(self.context['request'].user, 'empresa') else None

        if orden_compra and empresa and orden_compra.empresa != empresa:
            raise serializers.ValidationError({
                'orden_compra': 'La orden de compra debe pertenecer a la misma empresa.'
            })

        almacen = data.get('almacen')
        if almacen and empresa and almacen.empresa != empresa:
            raise serializers.ValidationError({
                'almacen': 'El almacén debe pertenecer a la misma empresa.'
            })

        if orden_compra and orden_compra.estado not in ['APROBADA', 'ENVIADA', 'RECIBIDA_PARCIAL']:
            raise serializers.ValidationError({
                'orden_compra': 'La orden de compra debe estar aprobada o enviada para poder recibir mercancía.'
            })

        return data


class RecepcionCompraListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    proveedor_nombre = serializers.ReadOnlyField(source='orden_compra.proveedor.nombre')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')

    class Meta:
        model = RecepcionCompra
        fields = ['id', 'uuid', 'numero_recepcion', 'fecha_recepcion', 'estado', 'proveedor_nombre', 'almacen_nombre', 'orden_compra']


# --- Devoluciones a Proveedores ---
class DetalleDevolucionProveedorSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo = serializers.ReadOnlyField(source='producto.codigo_sku')
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleDevolucionProveedor
        fields = '__all__'
        read_only_fields = ('id',)


class DevolucionProveedorSerializer(ProveedorEmpresaValidatorMixin, serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')
    compra_numero = serializers.ReadOnlyField(source='compra.numero_factura_proveedor')
    detalles = DetalleDevolucionProveedorSerializer(many=True, read_only=True)

    class Meta:
        model = DevolucionProveedor
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'numero_devolucion', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa', 'subtotal', 'impuestos', 'total')

    def validate(self, data):
        data = super().validate(data)

        compra = data.get('compra')
        proveedor = data.get('proveedor')
        empresa = self.context['request'].user.empresa if hasattr(self.context['request'].user, 'empresa') else None

        if compra and proveedor and compra.proveedor != proveedor:
            raise serializers.ValidationError({
                'compra': 'La compra debe ser del mismo proveedor.'
            })

        if compra and empresa and compra.empresa != empresa:
            raise serializers.ValidationError({
                'compra': 'La compra debe pertenecer a la misma empresa.'
            })

        return data


class DevolucionProveedorListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')

    class Meta:
        model = DevolucionProveedor
        fields = ['id', 'uuid', 'numero_devolucion', 'fecha', 'motivo', 'estado', 'proveedor_nombre', 'total']


# --- Liquidaciones de Importación ---
class GastoImportacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.ReadOnlyField()
    proveedor_gasto_nombre = serializers.ReadOnlyField(source='proveedor_gasto.nombre')

    class Meta:
        model = GastoImportacion
        fields = '__all__'
        read_only_fields = ('id', 'liquidacion')


class LiquidacionImportacionSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    compra_numero = serializers.ReadOnlyField(source='compra.numero_factura_proveedor')
    proveedor_nombre = serializers.ReadOnlyField(source='compra.proveedor.nombre')
    gastos = GastoImportacionSerializer(many=True, read_only=True)

    class Meta:
        model = LiquidacionImportacion
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'numero_liquidacion', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa', 'total_gastos', 'total_cif')

    def validate(self, data):
        compra = data.get('compra')
        empresa = self.context['request'].user.empresa if hasattr(self.context['request'].user, 'empresa') else None

        if compra and empresa and compra.empresa != empresa:
            raise serializers.ValidationError({
                'compra': 'La compra debe pertenecer a la misma empresa.'
            })

        if compra and not compra.proveedor.es_internacional:
            raise serializers.ValidationError({
                'compra': 'La liquidación de importación solo aplica para proveedores internacionales.'
            })

        tasa_cambio = data.get('tasa_cambio', 1.0)
        if tasa_cambio <= 0:
            raise serializers.ValidationError({
                'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'
            })

        return data


class LiquidacionImportacionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    proveedor_nombre = serializers.ReadOnlyField(source='compra.proveedor.nombre')
    compra_numero = serializers.ReadOnlyField(source='compra.numero_factura_proveedor')

    class Meta:
        model = LiquidacionImportacion
        fields = ['id', 'uuid', 'numero_liquidacion', 'fecha', 'incoterm', 'estado', 'proveedor_nombre', 'compra_numero', 'total_fob', 'total_gastos', 'total_cif']


# --- Retenciones Fiscales ---
class TipoRetencionSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = TipoRetencion
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'empresa')


class RetencionCompraSerializer(serializers.ModelSerializer):
    tipo_retencion_nombre = serializers.ReadOnlyField(source='tipo_retencion.nombre')
    tipo_retencion_categoria = serializers.ReadOnlyField(source='tipo_retencion.categoria')
    compra_numero = serializers.ReadOnlyField(source='compra.numero_factura_proveedor')

    class Meta:
        model = RetencionCompra
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'fecha_aplicacion', 'empresa', 'usuario_creacion')

    def validate(self, data):
        compra = data.get('compra')
        empresa = self.context['request'].user.empresa if hasattr(self.context['request'].user, 'empresa') else None

        if compra and empresa and compra.empresa != empresa:
            raise serializers.ValidationError({'compra': 'La compra debe pertenecer a su empresa.'})

        tipo_retencion = data.get('tipo_retencion')
        if tipo_retencion and empresa and tipo_retencion.empresa and tipo_retencion.empresa != empresa:
            raise serializers.ValidationError({'tipo_retencion': 'El tipo de retención debe pertenecer a su empresa.'})

        return data


class AplicarRetencionSerializer(serializers.Serializer):
    """Serializer para aplicar retención a una compra"""
    tipo_retencion_id = serializers.IntegerField()
    base_imponible = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

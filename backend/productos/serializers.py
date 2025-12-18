from rest_framework import serializers
from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas
from django.db.models import Sum
import re

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

class ProductoSerializer(serializers.ModelSerializer):
    categorias_detalle = CategoriaSerializer(source='categorias', many=True, read_only=True)
    categorias_ids = serializers.PrimaryKeyRelatedField(
        source='categorias',
        many=True,
        queryset=Categoria.objects.all(),
        write_only=True,
        required=False
    )

    # Campos calculados
    precio_final_estimado = serializers.SerializerMethodField()
    existencia_total = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo_sku', 'nombre', 'descripcion',
            'tipo_producto', 'controlar_stock',
            'precio_venta_base', 'impuesto_itbis', 'es_exento',
            'tiene_garantia', 'meses_garantia',
            'porcentaje_descuento_promocional', 'porcentaje_descuento_maximo',
            'activo', 'categorias', 'categorias_detalle', 'categorias_ids',
            'precio_final_estimado', 'existencia_total',
            'fecha_creacion', 'fecha_actualizacion',
            'idempotency_key'
        ]
        read_only_fields = ('id', 'fecha_creacion', 'fecha_actualizacion')

    def validate_precio_venta_base(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio base no puede ser negativo.")
        return value

    def validate_impuesto_itbis(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El ITBIS debe ser un porcentaje entre 0 y 100.")
        return value

    def validate_porcentaje_descuento_promocional(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El descuento promocional debe ser entre 0 y 100.")
        return value

    def validate_porcentaje_descuento_maximo(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El descuento máximo debe ser entre 0 y 100.")
        return value

    def validate_codigo_sku(self, value):
        # Validar que solo tenga letras, numeros, guiones o guiones bajos
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError("El SKU solo puede contener letras, números, guiones (-) y guiones bajos (_).")
        return value

    def get_precio_final_estimado(self, obj):
        """
        Calcula el precio final: (Precio Base - Descuento Promo) + ITBIS
        El ITBIS se calcula sobre el precio ya descontado.
        """
        if obj.precio_venta_base is not None:
            # Aplicar descuento promocional si existe
            precio_con_descuento = float(obj.precio_venta_base)
            if obj.porcentaje_descuento_promocional and obj.porcentaje_descuento_promocional > 0:
                descuento = (float(obj.precio_venta_base) * float(obj.porcentaje_descuento_promocional)) / 100
                precio_con_descuento = float(obj.precio_venta_base) - descuento

            # Aplicar ITBIS (si no es exento)
            if not obj.es_exento and obj.impuesto_itbis:
                itbis = (precio_con_descuento * float(obj.impuesto_itbis)) / 100
                return round(precio_con_descuento + itbis, 2)
            return round(precio_con_descuento, 2)
        return 0

    def get_existencia_total(self, obj):
        """Suma la existencia disponible en todos los almacenes"""
        # Servicios y activos fijos no tienen stock
        if obj.tipo_producto in ['SERVICIO', 'ACTIVO_FIJO'] or not obj.controlar_stock:
            return None

        # Usamos el related_name 'inventarios' definido en InventarioProducto
        total = obj.inventarios.aggregate(total=Sum('cantidad_disponible'))['total']
        return total or 0


# --- Imágenes de Productos ---
class ImagenProductoSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.ReadOnlyField(source='producto.codigo_sku')
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ImagenProducto
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion')

    def get_imagen_url(self, obj):
        """Retorna la URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class ImagenProductoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ImagenProducto
        fields = ['id', 'uuid', 'imagen_url', 'titulo', 'es_principal', 'orden', 'activa']

    def get_imagen_url(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


# --- Referencias Cruzadas ---
class ReferenciasCruzadasSerializer(serializers.ModelSerializer):
    producto_origen_codigo = serializers.ReadOnlyField(source='producto_origen.codigo_sku')
    producto_origen_nombre = serializers.ReadOnlyField(source='producto_origen.nombre')
    producto_destino_codigo = serializers.ReadOnlyField(source='producto_destino.codigo_sku')
    producto_destino_nombre = serializers.ReadOnlyField(source='producto_destino.nombre')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ReferenciasCruzadas
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion')

    def validate(self, data):
        producto_origen = data.get('producto_origen')
        producto_destino = data.get('producto_destino')

        if producto_origen and producto_destino and producto_origen == producto_destino:
            raise serializers.ValidationError({
                'producto_destino': 'El producto destino no puede ser el mismo que el origen.'
            })

        return data


class ReferenciasCruzadasListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    producto_destino_codigo = serializers.ReadOnlyField(source='producto_destino.codigo_sku')
    producto_destino_nombre = serializers.ReadOnlyField(source='producto_destino.nombre')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ReferenciasCruzadas
        fields = ['id', 'producto_destino', 'producto_destino_codigo', 'producto_destino_nombre', 'tipo', 'tipo_display', 'bidireccional', 'activa']

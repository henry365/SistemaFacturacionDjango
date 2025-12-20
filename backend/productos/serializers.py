"""
Serializers para el módulo Productos

Este módulo contiene los serializers para productos, categorías,
imágenes y referencias cruzadas.

Incluye soporte para multi-tenancy con validación de empresa.
"""
from rest_framework import serializers
from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas
from .constants import SKU_REGEX, ERROR_SKU_FORMATO
from django.db.models import Sum
import re


# =============================================================================
# SERIALIZERS DE CATEGORÍA
# =============================================================================

class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer completo para Categoría"""
    productos_count = serializers.SerializerMethodField()
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = Categoria
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'nombre', 'descripcion', 'activa',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion',
            'productos_count', 'idempotency_key'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'productos_count'
        ]

    def get_productos_count(self, obj):
        """Cuenta de productos en la categoría"""
        return obj.productos.count()


class CategoriaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de Categorías"""
    productos_count = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'uuid', 'nombre', 'activa', 'productos_count', 'fecha_creacion']
        read_only_fields = fields

    def get_productos_count(self, obj):
        """Cuenta de productos en la categoría"""
        return obj.productos.count()


# =============================================================================
# SERIALIZERS DE PRODUCTO
# =============================================================================

class ProductoSerializer(serializers.ModelSerializer):
    """Serializer completo para Producto"""
    categorias_detalle = CategoriaListSerializer(source='categorias', many=True, read_only=True)
    categorias_ids = serializers.PrimaryKeyRelatedField(
        source='categorias',
        many=True,
        queryset=Categoria.objects.all(),
        write_only=True,
        required=False
    )
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    # Campos calculados
    precio_final_estimado = serializers.SerializerMethodField()
    existencia_total = serializers.SerializerMethodField()
    tipo_producto_display = serializers.CharField(source='get_tipo_producto_display', read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre', 'codigo_sku', 'nombre', 'descripcion',
            'tipo_producto', 'tipo_producto_display', 'controlar_stock',
            'precio_venta_base', 'impuesto_itbis', 'es_exento',
            'tiene_garantia', 'meses_garantia',
            'porcentaje_descuento_promocional', 'porcentaje_descuento_maximo',
            'activo', 'categorias', 'categorias_detalle', 'categorias_ids',
            'precio_final_estimado', 'existencia_total',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion',
            'idempotency_key'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

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
        if not re.match(SKU_REGEX, value):
            raise serializers.ValidationError(ERROR_SKU_FORMATO)
        return value

    def validate(self, data):
        """Valida que las categorías pertenezcan a la misma empresa"""
        categorias = data.get('categorias', [])

        # Obtener empresa del contexto o de la instancia
        request = self.context.get('request')
        empresa = None
        if request and hasattr(request.user, 'empresa'):
            empresa = request.user.empresa
        elif self.instance:
            empresa = self.instance.empresa

        # Validar que las categorías pertenezcan a la misma empresa
        if empresa and categorias:
            for categoria in categorias:
                if categoria.empresa_id != empresa.id:
                    raise serializers.ValidationError({
                        'categorias_ids': f'La categoría "{categoria.nombre}" no pertenece a su empresa.'
                    })

        return data

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


class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de Productos"""
    tipo_producto_display = serializers.CharField(source='get_tipo_producto_display', read_only=True)
    precio_final_estimado = serializers.SerializerMethodField()
    categorias_nombres = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'uuid', 'codigo_sku', 'nombre',
            'tipo_producto', 'tipo_producto_display',
            'precio_venta_base', 'impuesto_itbis', 'es_exento',
            'precio_final_estimado', 'activo', 'controlar_stock',
            'categorias_nombres', 'fecha_creacion'
        ]
        read_only_fields = fields

    def get_precio_final_estimado(self, obj):
        """Calcula el precio final"""
        if obj.precio_venta_base is not None:
            precio_con_descuento = float(obj.precio_venta_base)
            if obj.porcentaje_descuento_promocional and obj.porcentaje_descuento_promocional > 0:
                descuento = (float(obj.precio_venta_base) * float(obj.porcentaje_descuento_promocional)) / 100
                precio_con_descuento = float(obj.precio_venta_base) - descuento

            if not obj.es_exento and obj.impuesto_itbis:
                itbis = (precio_con_descuento * float(obj.impuesto_itbis)) / 100
                return round(precio_con_descuento + itbis, 2)
            return round(precio_con_descuento, 2)
        return 0

    def get_categorias_nombres(self, obj):
        """Lista de nombres de categorías"""
        return [cat.nombre for cat in obj.categorias.all()]


# =============================================================================
# SERIALIZERS DE IMAGEN DE PRODUCTO
# =============================================================================

class ImagenProductoSerializer(serializers.ModelSerializer):
    """Serializer completo para ImagenProducto"""
    producto_codigo = serializers.ReadOnlyField(source='producto.codigo_sku')
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ImagenProducto
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre',
            'producto', 'producto_codigo', 'producto_nombre',
            'imagen', 'imagen_url', 'titulo', 'descripcion',
            'es_principal', 'orden', 'activa',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def validate_producto(self, value):
        """Valida que el producto pertenezca a la misma empresa del usuario"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa') and request.user.empresa:
            if value.empresa_id != request.user.empresa.id:
                raise serializers.ValidationError("El producto no pertenece a su empresa.")
        return value

    def get_imagen_url(self, obj):
        """Retorna la URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class ImagenProductoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de imágenes"""
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ImagenProducto
        fields = ['id', 'uuid', 'imagen_url', 'titulo', 'es_principal', 'orden', 'activa']
        read_only_fields = fields

    def get_imagen_url(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


# =============================================================================
# SERIALIZERS DE REFERENCIAS CRUZADAS
# =============================================================================

class ReferenciasCruzadasSerializer(serializers.ModelSerializer):
    """Serializer completo para ReferenciasCruzadas"""
    producto_origen_codigo = serializers.ReadOnlyField(source='producto_origen.codigo_sku')
    producto_origen_nombre = serializers.ReadOnlyField(source='producto_origen.nombre')
    producto_destino_codigo = serializers.ReadOnlyField(source='producto_destino.codigo_sku')
    producto_destino_nombre = serializers.ReadOnlyField(source='producto_destino.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ReferenciasCruzadas
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre',
            'producto_origen', 'producto_origen_codigo', 'producto_origen_nombre',
            'producto_destino', 'producto_destino_codigo', 'producto_destino_nombre',
            'tipo', 'tipo_display', 'bidireccional', 'activa',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def validate(self, data):
        """Valida productos origen y destino"""
        producto_origen = data.get('producto_origen')
        producto_destino = data.get('producto_destino')

        if producto_origen and producto_destino and producto_origen == producto_destino:
            raise serializers.ValidationError({
                'producto_destino': 'El producto destino no puede ser el mismo que el origen.'
            })

        # Validar que ambos productos pertenezcan a la misma empresa del usuario
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa') and request.user.empresa:
            empresa = request.user.empresa
            if producto_origen and producto_origen.empresa_id != empresa.id:
                raise serializers.ValidationError({
                    'producto_origen': 'El producto origen no pertenece a su empresa.'
                })
            if producto_destino and producto_destino.empresa_id != empresa.id:
                raise serializers.ValidationError({
                    'producto_destino': 'El producto destino no pertenece a su empresa.'
                })

        return data


class ReferenciasCruzadasListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de referencias"""
    producto_origen_codigo = serializers.ReadOnlyField(source='producto_origen.codigo_sku')
    producto_destino_codigo = serializers.ReadOnlyField(source='producto_destino.codigo_sku')
    producto_destino_nombre = serializers.ReadOnlyField(source='producto_destino.nombre')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ReferenciasCruzadas
        fields = [
            'id', 'producto_origen_codigo', 'producto_destino',
            'producto_destino_codigo', 'producto_destino_nombre',
            'tipo', 'tipo_display', 'bidireccional', 'activa'
        ]
        read_only_fields = fields

"""
Configuración del Admin para el módulo Productos
"""
from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas


class ImagenProductoInline(admin.TabularInline):
    """Inline para mostrar imágenes en el detalle del producto"""
    model = ImagenProducto
    extra = 1
    fields = ['imagen', 'titulo', 'es_principal', 'orden', 'activa']
    readonly_fields = ['uuid', 'fecha_creacion']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Administración de Categorías"""
    list_display = ['nombre', 'activa', 'fecha_creacion', 'productos_count']
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'activa')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def productos_count(self, obj):
        """Cuenta de productos en la categoría"""
        return obj.productos.count()
    productos_count.short_description = 'Productos'

    def save_model(self, request, obj, form, change):
        """Guardar usuario de auditoría"""
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Administración de Productos"""
    list_display = [
        'codigo_sku', 'nombre', 'tipo_producto', 'precio_venta_base',
        'impuesto_itbis', 'activo', 'controlar_stock'
    ]
    list_filter = ['activo', 'tipo_producto', 'es_exento', 'tiene_garantia', 'categorias']
    search_fields = ['codigo_sku', 'nombre', 'descripcion']
    ordering = ['nombre']
    filter_horizontal = ['categorias']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']
    inlines = [ImagenProductoInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_sku', 'nombre', 'descripcion', 'tipo_producto', 'activo')
        }),
        ('Precios e Impuestos', {
            'fields': (
                'precio_venta_base', 'impuesto_itbis', 'es_exento',
                'porcentaje_descuento_promocional', 'porcentaje_descuento_maximo'
            )
        }),
        ('Stock y Garantía', {
            'fields': ('controlar_stock', 'tiene_garantia', 'meses_garantia')
        }),
        ('Categorías', {
            'fields': ('categorias',)
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Guardar usuario de auditoría"""
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    """Administración de Imágenes de Productos"""
    list_display = ['producto', 'titulo', 'es_principal', 'orden', 'activa', 'fecha_creacion']
    list_filter = ['es_principal', 'activa', 'fecha_creacion']
    search_fields = ['producto__codigo_sku', 'producto__nombre', 'titulo']
    ordering = ['producto', 'orden']
    raw_id_fields = ['producto']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']

    fieldsets = (
        ('Imagen', {
            'fields': ('producto', 'imagen', 'titulo', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('es_principal', 'orden', 'activa')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Guardar usuario de auditoría"""
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReferenciasCruzadas)
class ReferenciasCruzadasAdmin(admin.ModelAdmin):
    """Administración de Referencias Cruzadas"""
    list_display = ['producto_origen', 'producto_destino', 'tipo', 'bidireccional', 'activa']
    list_filter = ['tipo', 'bidireccional', 'activa']
    search_fields = [
        'producto_origen__codigo_sku', 'producto_origen__nombre',
        'producto_destino__codigo_sku', 'producto_destino__nombre'
    ]
    ordering = ['producto_origen', 'tipo']
    raw_id_fields = ['producto_origen', 'producto_destino']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']

    fieldsets = (
        ('Referencia', {
            'fields': ('producto_origen', 'producto_destino', 'tipo')
        }),
        ('Configuración', {
            'fields': ('bidireccional', 'activa')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Guardar usuario de auditoría"""
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)

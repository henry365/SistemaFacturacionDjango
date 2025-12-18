from django.contrib import admin
from .models import Cliente, CategoriaCliente

@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descuento_porcentaje', 'activa', 'empresa', 'fecha_creacion')
    list_filter = ('activa', 'empresa', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'nombre', 'descripcion', 'descuento_porcentaje', 'activa')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_identificacion', 'numero_identificacion', 'telefono', 'categoria', 'vendedor_asignado', 'activo', 'empresa')
    list_filter = ('activo', 'tipo_identificacion', 'categoria', 'vendedor_asignado', 'empresa', 'fecha_creacion')
    search_fields = ('nombre', 'numero_identificacion', 'telefono', 'correo_electronico')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'idempotency_key')
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'nombre', 'categoria')
        }),
        ('Identificación', {
            'fields': ('tipo_identificacion', 'numero_identificacion')
        }),
        ('Contacto', {
            'fields': ('telefono', 'correo_electronico', 'direccion')
        }),
        ('Comercial', {
            'fields': ('limite_credito', 'vendedor_asignado', 'activo')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

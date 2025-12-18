from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_identificacion', 'numero_identificacion', 'tipo_contribuyente', 'telefono', 'es_internacional', 'activo', 'empresa', 'fecha_creacion')
    list_filter = ('activo', 'tipo_identificacion', 'tipo_contribuyente', 'es_internacional', 'empresa', 'fecha_creacion')
    search_fields = ('nombre', 'numero_identificacion', 'telefono', 'correo_electronico', 'direccion')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'idempotency_key')
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'nombre', 'activo')
        }),
        ('Identificación', {
            'fields': ('tipo_identificacion', 'numero_identificacion', 'tipo_contribuyente')
        }),
        ('Contacto', {
            'fields': ('telefono', 'correo_electronico', 'direccion')
        }),
        ('Configuración', {
            'fields': ('es_internacional',)
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

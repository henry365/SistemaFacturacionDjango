from django.contrib import admin
from .models import Vendedor

@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'telefono', 'correo', 'comision_porcentaje', 'usuario', 'activo', 'empresa', 'fecha_creacion')
    list_filter = ('activo', 'empresa', 'fecha_creacion')
    search_fields = ('nombre', 'cedula', 'telefono', 'correo', 'usuario__username', 'empresa__nombre')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'idempotency_key')
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'nombre', 'activo')
        }),
        ('Identificación', {
            'fields': ('cedula',)
        }),
        ('Contacto', {
            'fields': ('telefono', 'correo')
        }),
        ('Configuración', {
            'fields': ('comision_porcentaje', 'usuario')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

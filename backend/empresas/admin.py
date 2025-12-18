from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rnc', 'telefono', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'rnc', 'telefono', 'direccion')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'rnc', 'activo')
        }),
        ('Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Configuración', {
            'fields': ('logo', 'configuracion_fiscal')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

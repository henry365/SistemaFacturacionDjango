"""
Configuración del Admin de Django para el módulo Core.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ConfiguracionEmpresa


@admin.register(ConfiguracionEmpresa)
class ConfiguracionEmpresaAdmin(admin.ModelAdmin):
    """
    Admin para ConfiguracionEmpresa.
    Solo superusers pueden acceder.
    """
    list_display = [
        'empresa',
        'fecha_actualizacion',
        'usuario_modificacion',
        'mostrar_estado',
    ]
    list_filter = ['fecha_actualizacion']
    search_fields = ['empresa__nombre', 'empresa__rnc']
    readonly_fields = [
        'fecha_creacion',
        'fecha_actualizacion',
        'usuario_creacion',
        'usuario_modificacion',
    ]

    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Configuración Fiscal (DGII)', {
            'fields': ('config_fiscal',),
            'classes': ('collapse',),
            'description': 'Configuración relacionada con impuestos y DGII. Solo superusers pueden modificar.'
        }),
        ('Configuración de Facturación', {
            'fields': ('config_facturacion',),
            'classes': ('collapse',),
        }),
        ('Configuración de Inventario', {
            'fields': ('config_inventario',),
            'classes': ('collapse',),
        }),
        ('Configuración de Notificaciones', {
            'fields': ('config_notificaciones',),
            'classes': ('collapse',),
        }),
        ('Configuración de Reportes', {
            'fields': ('config_reportes',),
            'classes': ('collapse',),
        }),
        ('Configuración de Compras', {
            'fields': ('config_compras',),
            'classes': ('collapse',),
        }),
        ('Configuración de Seguridad', {
            'fields': ('config_seguridad',),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': (
                'usuario_creacion',
                'usuario_modificacion',
                'fecha_creacion',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',),
        }),
    )

    def mostrar_estado(self, obj):
        """Muestra un indicador visual del estado de configuración."""
        # Verificar si todas las secciones tienen valores
        secciones = [
            obj.config_fiscal,
            obj.config_facturacion,
            obj.config_inventario,
            obj.config_notificaciones,
            obj.config_reportes,
            obj.config_compras,
            obj.config_seguridad,
        ]

        vacias = sum(1 for s in secciones if not s)

        if vacias == 0:
            return format_html(
                '<span style="color: green;">Completa</span>'
            )
        elif vacias <= 2:
            return format_html(
                '<span style="color: orange;">Parcial ({}/7)</span>',
                7 - vacias
            )
        else:
            return format_html(
                '<span style="color: red;">Incompleta ({}/7)</span>',
                7 - vacias
            )

    mostrar_estado.short_description = 'Estado'

    def has_add_permission(self, request):
        """No permitir agregar manualmente (se crea con la empresa)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar."""
        return False

    def get_readonly_fields(self, request, obj=None):
        """config_fiscal solo lectura para no-superusers."""
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly.append('config_fiscal')
        return readonly

    def save_model(self, request, obj, form, change):
        """Registrar usuario de modificación."""
        if change:
            obj.usuario_modificacion = request.user
        else:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)

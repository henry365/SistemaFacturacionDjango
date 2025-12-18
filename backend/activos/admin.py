from django.contrib import admin
from .models import TipoActivo, ActivoFijo, Depreciacion


@admin.register(TipoActivo)
class TipoActivoAdmin(admin.ModelAdmin):
    """Admin para TipoActivo"""
    list_display = [
        'nombre', 'empresa', 'porcentaje_depreciacion_anual',
        'vida_util_anos', 'activo', 'fecha_creacion'
    ]
    list_filter = ['activo', 'empresa']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']

    fieldsets = (
        ('Informacion General', {
            'fields': ('empresa', 'nombre', 'descripcion', 'activo')
        }),
        ('Depreciacion', {
            'fields': ('porcentaje_depreciacion_anual', 'vida_util_anos')
        }),
        ('Metadata', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivoFijo)
class ActivoFijoAdmin(admin.ModelAdmin):
    """Admin para ActivoFijo"""
    list_display = [
        'codigo_interno', 'nombre', 'tipo_activo', 'estado',
        'valor_adquisicion', 'valor_libro_actual', 'fecha_adquisicion'
    ]
    list_filter = ['estado', 'tipo_activo', 'empresa', 'fecha_adquisicion']
    search_fields = ['codigo_interno', 'nombre', 'marca', 'modelo', 'serial']
    ordering = ['-fecha_creacion']
    readonly_fields = [
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'depreciacion_acumulada', 'porcentaje_depreciado'
    ]
    autocomplete_fields = ['tipo_activo', 'responsable']
    date_hierarchy = 'fecha_adquisicion'

    fieldsets = (
        ('Identificacion', {
            'fields': (
                'empresa', 'tipo_activo', 'codigo_interno',
                'nombre', 'descripcion'
            )
        }),
        ('Caracteristicas', {
            'fields': ('marca', 'modelo', 'serial', 'especificaciones')
        }),
        ('Ubicacion', {
            'fields': ('ubicacion_fisica', 'responsable')
        }),
        ('Valoracion', {
            'fields': (
                'fecha_adquisicion', 'valor_adquisicion',
                'valor_libro_actual', 'depreciacion_acumulada',
                'porcentaje_depreciado'
            )
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Origen', {
            'fields': ('producto_origen', 'compra_origen', 'detalle_compra_origen'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def porcentaje_depreciado(self, obj):
        return f"{obj.porcentaje_depreciado}%"
    porcentaje_depreciado.short_description = 'Depreciado %'


@admin.register(Depreciacion)
class DepreciacionAdmin(admin.ModelAdmin):
    """Admin para Depreciacion"""
    list_display = [
        'activo', 'fecha', 'monto',
        'valor_libro_anterior', 'valor_libro_nuevo'
    ]
    list_filter = ['fecha', 'activo__empresa']
    search_fields = ['activo__codigo_interno', 'activo__nombre', 'observacion']
    ordering = ['-fecha']
    readonly_fields = ['uuid', 'fecha_creacion']
    date_hierarchy = 'fecha'

    fieldsets = (
        ('Depreciacion', {
            'fields': ('activo', 'fecha', 'monto', 'observacion')
        }),
        ('Valores de Libro', {
            'fields': ('valor_libro_anterior', 'valor_libro_nuevo')
        }),
        ('Auditoria', {
            'fields': ('uuid', 'fecha_creacion', 'usuario_creacion'),
            'classes': ('collapse',)
        }),
    )

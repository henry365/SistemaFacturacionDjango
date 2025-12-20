"""
Configuración del Admin para el módulo DGII
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import TipoComprobante, SecuenciaNCF


class SecuenciaNCFInline(admin.TabularInline):
    """Inline para ver secuencias de un tipo de comprobante"""
    model = SecuenciaNCF
    extra = 0
    readonly_fields = (
        'uuid', 'secuencia_actual', 'agotada', 'disponibles',
        'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    fields = (
        'descripcion', 'secuencia_inicial', 'secuencia_final',
        'secuencia_actual', 'fecha_vencimiento', 'activo', 'agotada'
    )


@admin.register(TipoComprobante)
class TipoComprobanteAdmin(admin.ModelAdmin):
    """Admin para TipoComprobante"""
    list_display = (
        'codigo', 'nombre', 'prefijo', 'ncf_ejemplo',
        'empresa', 'activo_badge', 'fecha_creacion'
    )
    list_filter = ('activo', 'prefijo', 'empresa', 'fecha_creacion')
    search_fields = ('codigo', 'nombre')
    ordering = ['codigo']
    readonly_fields = (
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    raw_id_fields = ['empresa']
    inlines = [SecuenciaNCFInline]

    fieldsets = (
        ('Información General', {
            'fields': ('empresa', 'codigo', 'nombre', 'prefijo', 'activo')
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def ncf_ejemplo(self, obj):
        """Muestra ejemplo de NCF"""
        return f"{obj.prefijo}{obj.codigo}00000001"
    ncf_ejemplo.short_description = 'Ejemplo NCF'

    def activo_badge(self, obj):
        """Muestra estado activo con color"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'

    def get_queryset(self, request):
        """Optimiza queries"""
        return super().get_queryset(request).select_related(
            'empresa', 'usuario_creacion', 'usuario_modificacion'
        )


@admin.register(SecuenciaNCF)
class SecuenciaNCFAdmin(admin.ModelAdmin):
    """Admin para SecuenciaNCF"""
    list_display = (
        'tipo_comprobante', 'descripcion', 'empresa',
        'secuencia_actual', 'secuencia_final', 'disponibles_display',
        'porcentaje_uso_display', 'fecha_vencimiento',
        'activo_badge', 'agotada_badge'
    )
    list_filter = (
        'activo', 'empresa', 'fecha_vencimiento',
        'tipo_comprobante'
    )
    search_fields = ('descripcion', 'tipo_comprobante__nombre')
    ordering = ['-fecha_creacion']
    readonly_fields = (
        'uuid', 'secuencia_actual', 'agotada', 'disponibles', 'porcentaje_uso',
        'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    raw_id_fields = ['empresa', 'tipo_comprobante']
    date_hierarchy = 'fecha_vencimiento'

    fieldsets = (
        ('Información General', {
            'fields': ('empresa', 'tipo_comprobante', 'descripcion', 'activo')
        }),
        ('Secuencias', {
            'fields': (
                'secuencia_inicial', 'secuencia_final', 'secuencia_actual',
                'disponibles', 'porcentaje_uso', 'agotada'
            )
        }),
        ('Vencimiento y Alertas', {
            'fields': ('fecha_vencimiento', 'alerta_cantidad')
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def disponibles_display(self, obj):
        """Muestra NCF disponibles con color según cantidad"""
        disponibles = obj.disponibles
        if disponibles <= obj.alerta_cantidad:
            color = '#dc3545'  # Rojo
        elif disponibles <= obj.alerta_cantidad * 2:
            color = '#ffc107'  # Amarillo
        else:
            color = '#28a745'  # Verde
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, disponibles
        )
    disponibles_display.short_description = 'Disponibles'

    def porcentaje_uso_display(self, obj):
        """Muestra porcentaje de uso con barra de progreso"""
        porcentaje = obj.porcentaje_uso
        if porcentaje >= 90:
            color = '#dc3545'
        elif porcentaje >= 70:
            color = '#ffc107'
        else:
            color = '#28a745'
        return format_html(
            '<div style="width:100px; background-color:#e9ecef; border-radius:3px;">'
            '<div style="width:{}%; background-color:{}; height:20px; border-radius:3px; '
            'text-align:center; color:white; font-size:12px; line-height:20px;">'
            '{}%</div></div>',
            min(porcentaje, 100), color, porcentaje
        )
    porcentaje_uso_display.short_description = '% Uso'

    def activo_badge(self, obj):
        """Muestra estado activo con color"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'

    def agotada_badge(self, obj):
        """Muestra si está agotada con color"""
        if obj.agotada:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Agotada</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Disponible</span>'
        )
    agotada_badge.short_description = 'Agotada'

    def get_queryset(self, request):
        """Optimiza queries"""
        return super().get_queryset(request).select_related(
            'empresa', 'tipo_comprobante', 'tipo_comprobante__empresa',
            'usuario_creacion', 'usuario_modificacion'
        )

"""
Configuración del Admin para el módulo de Despachos
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Despacho, DetalleDespacho
from .constants import (
    ESTADO_PENDIENTE, ESTADO_EN_PREPARACION, ESTADO_PARCIAL,
    ESTADO_COMPLETADO, ESTADO_CANCELADO
)


class DetalleDespachoInline(admin.TabularInline):
    """Inline para ver detalles de despacho"""
    model = DetalleDespacho
    extra = 0
    readonly_fields = (
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    fields = (
        'producto', 'cantidad_solicitada', 'cantidad_despachada',
        'lote', 'observaciones'
    )
    raw_id_fields = ['producto', 'lote']


@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    """Admin para Despacho"""
    list_display = (
        'id', 'uuid_corto', 'factura', 'cliente', 'almacen',
        'estado_badge', 'fecha', 'fecha_despacho', 'empresa'
    )
    list_filter = ('estado', 'empresa', 'almacen', 'fecha', 'fecha_despacho')
    search_fields = (
        'factura__numero_factura', 'cliente__nombre',
        'numero_guia', 'uuid'
    )
    readonly_fields = (
        'uuid', 'fecha', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion', 'usuario_despacho'
    )
    raw_id_fields = ['factura', 'cliente', 'almacen', 'empresa']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']
    inlines = [DetalleDespachoInline]

    fieldsets = (
        ('Información Principal', {
            'fields': (
                'empresa', 'factura', 'cliente', 'almacen', 'estado'
            )
        }),
        ('Información de Entrega', {
            'fields': (
                'direccion_entrega', 'transportista', 'numero_guia',
                'fecha_despacho', 'observaciones'
            )
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'idempotency_key', 'fecha', 'fecha_creacion',
                'fecha_actualizacion', 'usuario_creacion',
                'usuario_modificacion', 'usuario_despacho'
            ),
            'classes': ('collapse',)
        }),
    )

    def uuid_corto(self, obj):
        """Muestra UUID abreviado"""
        return str(obj.uuid)[:8] if obj.uuid else '-'
    uuid_corto.short_description = 'UUID'

    def estado_badge(self, obj):
        """Muestra el estado con color"""
        colores = {
            ESTADO_PENDIENTE: '#ffc107',      # Amarillo
            ESTADO_EN_PREPARACION: '#17a2b8', # Azul
            ESTADO_PARCIAL: '#fd7e14',        # Naranja
            ESTADO_COMPLETADO: '#28a745',     # Verde
            ESTADO_CANCELADO: '#dc3545',      # Rojo
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def get_queryset(self, request):
        """Optimiza queries"""
        return super().get_queryset(request).select_related(
            'factura', 'cliente', 'almacen', 'empresa',
            'usuario_creacion', 'usuario_modificacion', 'usuario_despacho'
        )


@admin.register(DetalleDespacho)
class DetalleDespachoAdmin(admin.ModelAdmin):
    """Admin para DetalleDespacho"""
    list_display = (
        'id', 'uuid_corto', 'despacho', 'producto',
        'cantidad_solicitada', 'cantidad_despachada',
        'porcentaje_despachado', 'lote'
    )
    list_filter = ('despacho__estado', 'despacho__empresa')
    search_fields = (
        'producto__nombre', 'producto__codigo_sku',
        'despacho__factura__numero_factura', 'uuid'
    )
    readonly_fields = (
        'uuid', 'cantidad', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    raw_id_fields = ['despacho', 'producto', 'lote']

    fieldsets = (
        ('Información Principal', {
            'fields': ('despacho', 'producto', 'lote')
        }),
        ('Cantidades', {
            'fields': (
                'cantidad_solicitada', 'cantidad_despachada',
                'cantidad', 'observaciones'
            )
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def uuid_corto(self, obj):
        """Muestra UUID abreviado"""
        return str(obj.uuid)[:8] if obj.uuid else '-'
    uuid_corto.short_description = 'UUID'

    def porcentaje_despachado(self, obj):
        """Calcula porcentaje despachado"""
        if obj.cantidad_solicitada and obj.cantidad_solicitada > 0:
            porcentaje = (obj.cantidad_despachada / obj.cantidad_solicitada) * 100
            return f"{porcentaje:.1f}%"
        return "0%"
    porcentaje_despachado.short_description = '% Despachado'

    def get_queryset(self, request):
        """Optimiza queries"""
        return super().get_queryset(request).select_related(
            'despacho', 'despacho__empresa', 'producto', 'lote'
        )

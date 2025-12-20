"""
Configuración del Admin de Django para el módulo de Caja

Este módulo configura la interfaz de administración de Django
para Cajas, Sesiones y Movimientos de Caja.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Caja, SesionCaja, MovimientoCaja
from .constants import ESTADO_ABIERTA, ESTADO_CERRADA, ESTADO_ARQUEADA


class MovimientoCajaInline(admin.TabularInline):
    """Inline para ver movimientos dentro de una sesión"""
    model = MovimientoCaja
    extra = 0
    readonly_fields = (
        'uuid', 'tipo_movimiento', 'monto', 'descripcion',
        'fecha', 'referencia', 'usuario', 'usuario_creacion'
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    """Admin para Caja"""
    list_display = (
        'nombre', 'empresa', 'activa_badge', 'sesiones_count',
        'tiene_sesion_abierta_badge', 'fecha_creacion'
    )
    list_filter = ('activa', 'empresa', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion', 'empresa__razon_social')
    readonly_fields = (
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    ordering = ('nombre',)

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'activa', 'empresa')
        }),
        ('Identificación', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def sesiones_count(self, obj):
        return obj.sesiones.count()
    sesiones_count.short_description = 'Sesiones'

    def activa_badge(self, obj):
        if obj.activa:
            return format_html(
                '<span style="color: green; font-weight: bold;">Activa</span>'
            )
        return format_html(
            '<span style="color: red;">Inactiva</span>'
        )
    activa_badge.short_description = 'Estado'

    def tiene_sesion_abierta_badge(self, obj):
        if obj.tiene_sesion_abierta():
            return format_html(
                '<span style="color: orange; font-weight: bold;">Sí</span>'
            )
        return format_html('<span style="color: gray;">No</span>')
    tiene_sesion_abierta_badge.short_description = 'Sesión Abierta'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(SesionCaja)
class SesionCajaAdmin(admin.ModelAdmin):
    """Admin para SesionCaja"""
    list_display = (
        'id', 'caja', 'usuario', 'estado_badge', 'monto_apertura',
        'monto_cierre_usuario', 'diferencia_badge', 'fecha_apertura'
    )
    list_filter = ('estado', 'caja', 'empresa', 'fecha_apertura')
    search_fields = (
        'caja__nombre', 'usuario__username', 'observaciones'
    )
    readonly_fields = (
        'uuid', 'fecha_apertura', 'fecha_cierre', 'monto_cierre_sistema',
        'diferencia', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    ordering = ('-fecha_apertura',)
    inlines = [MovimientoCajaInline]
    date_hierarchy = 'fecha_apertura'

    fieldsets = (
        ('Información de Sesión', {
            'fields': ('caja', 'usuario', 'empresa', 'estado')
        }),
        ('Montos de Apertura', {
            'fields': ('monto_apertura',)
        }),
        ('Montos de Cierre', {
            'fields': (
                'monto_cierre_sistema', 'monto_cierre_usuario', 'diferencia'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_apertura', 'fecha_cierre'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Identificación', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def estado_badge(self, obj):
        colors = {
            ESTADO_ABIERTA: 'green',
            ESTADO_CERRADA: 'orange',
            ESTADO_ARQUEADA: 'blue',
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def diferencia_badge(self, obj):
        if obj.diferencia is None:
            return '-'
        if obj.diferencia == 0:
            return format_html(
                '<span style="color: green;">$0.00</span>'
            )
        elif obj.diferencia > 0:
            return format_html(
                '<span style="color: blue;">+${}</span>',
                obj.diferencia
            )
        else:
            return format_html(
                '<span style="color: red;">${}</span>',
                obj.diferencia
            )
    diferencia_badge.short_description = 'Diferencia'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    """Admin para MovimientoCaja"""
    list_display = (
        'id', 'sesion', 'tipo_movimiento_badge', 'monto',
        'descripcion_corta', 'referencia', 'usuario', 'fecha'
    )
    list_filter = ('tipo_movimiento', 'sesion__caja', 'empresa', 'fecha')
    search_fields = ('descripcion', 'referencia', 'sesion__caja__nombre')
    readonly_fields = (
        'uuid', 'fecha', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    )
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('sesion', 'empresa', 'tipo_movimiento', 'monto')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'referencia', 'usuario')
        }),
        ('Fechas', {
            'fields': ('fecha',),
            'classes': ('collapse',)
        }),
        ('Identificación', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    def tipo_movimiento_badge(self, obj):
        colors = {
            'VENTA': 'green',
            'INGRESO_MANUAL': 'blue',
            'RETIRO_MANUAL': 'orange',
            'GASTO_MENOR': 'red',
            'APERTURA': 'purple',
            'CIERRE': 'gray',
        }
        color = colors.get(obj.tipo_movimiento, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_tipo_movimiento_display()
        )
    tipo_movimiento_badge.short_description = 'Tipo'

    def descripcion_corta(self, obj):
        if len(obj.descripcion) > 50:
            return f'{obj.descripcion[:50]}...'
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)

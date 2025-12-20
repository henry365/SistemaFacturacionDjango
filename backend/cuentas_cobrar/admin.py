from django.contrib import admin
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente


class DetalleCobroClienteInline(admin.TabularInline):
    """Inline para detalles de cobro en el admin de CobroCliente."""
    model = DetalleCobroCliente
    extra = 0
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    """Admin para Cuentas por Cobrar con fieldsets organizados."""
    list_display = [
        'numero_documento', 'cliente', 'fecha_vencimiento',
        'monto_original', 'monto_pendiente', 'estado'
    ]
    list_filter = ['estado', 'empresa', 'fecha_vencimiento']
    search_fields = ['numero_documento', 'cliente__nombre', 'factura__numero_factura']
    readonly_fields = [
        'uuid', 'monto_pendiente', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    ]
    autocomplete_fields = ['empresa', 'cliente']
    date_hierarchy = 'fecha_vencimiento'
    list_per_page = 25
    list_select_related = ['empresa', 'cliente']

    fieldsets = (
        ('Informacion Principal', {
            'fields': ('empresa', 'cliente', 'numero_documento')
        }),
        ('Fechas', {
            'fields': ('fecha_documento', 'fecha_vencimiento')
        }),
        ('Montos', {
            'fields': ('monto_original', 'monto_cobrado', 'monto_pendiente')
        }),
        ('Estado', {
            'fields': ('estado', 'observaciones')
        }),
        ('Auditoria', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(CobroCliente)
class CobroClienteAdmin(admin.ModelAdmin):
    """Admin para Cobros a Clientes con fieldsets organizados."""
    list_display = [
        'numero_recibo', 'cliente', 'fecha_cobro', 'monto', 'metodo_pago'
    ]
    list_filter = ['metodo_pago', 'empresa', 'fecha_cobro']
    search_fields = ['numero_recibo', 'cliente__nombre', 'referencia']
    readonly_fields = [
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    ]
    autocomplete_fields = ['empresa', 'cliente']
    inlines = [DetalleCobroClienteInline]
    date_hierarchy = 'fecha_cobro'
    list_per_page = 25
    list_select_related = ['empresa', 'cliente']

    fieldsets = (
        ('Informacion Principal', {
            'fields': ('empresa', 'cliente', 'numero_recibo')
        }),
        ('Cobro', {
            'fields': ('fecha_cobro', 'monto', 'metodo_pago', 'referencia')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
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


@admin.register(DetalleCobroCliente)
class DetalleCobroClienteAdmin(admin.ModelAdmin):
    """Admin para Detalles de Cobro a Clientes."""
    list_display = ['cobro', 'cuenta_por_cobrar', 'monto_aplicado', 'fecha_creacion']
    list_filter = ['cobro__fecha_cobro', 'empresa']
    search_fields = ['cobro__numero_recibo', 'cuenta_por_cobrar__numero_documento']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']
    # autocomplete_fields = ['empresa']  # cobro and cuenta_por_cobrar need search_fields
    list_per_page = 25
    list_select_related = ['empresa', 'cobro', 'cuenta_por_cobrar']

    fieldsets = (
        ('Informacion Principal', {
            'fields': ('empresa', 'cobro', 'cuenta_por_cobrar', 'monto_aplicado')
        }),
        ('Auditoria', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

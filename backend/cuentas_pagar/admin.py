from django.contrib import admin
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor


class DetallePagoProveedorInline(admin.TabularInline):
    """Inline para detalles de pago en el admin de PagoProveedor."""
    model = DetallePagoProveedor
    extra = 0
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']
    autocomplete_fields = ['cuenta_por_pagar']


@admin.register(CuentaPorPagar)
class CuentaPorPagarAdmin(admin.ModelAdmin):
    """Admin para Cuentas por Pagar con fieldsets organizados."""
    list_display = [
        'numero_documento', 'proveedor', 'fecha_vencimiento',
        'monto_original', 'monto_pendiente', 'estado'
    ]
    list_filter = ['estado', 'empresa', 'fecha_vencimiento']
    search_fields = ['numero_documento', 'proveedor__nombre', 'compra__numero_factura_proveedor']
    readonly_fields = [
        'uuid', 'monto_pendiente', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    ]
    autocomplete_fields = ['empresa', 'proveedor', 'compra']
    date_hierarchy = 'fecha_vencimiento'
    list_per_page = 25
    list_select_related = ['empresa', 'proveedor']

    fieldsets = (
        ('Información Principal', {
            'fields': ('empresa', 'proveedor', 'compra', 'numero_documento')
        }),
        ('Fechas', {
            'fields': ('fecha_documento', 'fecha_vencimiento')
        }),
        ('Montos', {
            'fields': ('monto_original', 'monto_pagado', 'monto_pendiente')
        }),
        ('Estado', {
            'fields': ('estado', 'observaciones')
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    """Admin para Pagos a Proveedores con fieldsets organizados."""
    list_display = [
        'numero_pago', 'proveedor', 'fecha_pago', 'monto', 'metodo_pago'
    ]
    list_filter = ['metodo_pago', 'empresa', 'fecha_pago']
    search_fields = ['numero_pago', 'proveedor__nombre', 'referencia']
    readonly_fields = [
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_modificacion'
    ]
    autocomplete_fields = ['empresa', 'proveedor']
    inlines = [DetallePagoProveedorInline]
    date_hierarchy = 'fecha_pago'
    list_per_page = 25
    list_select_related = ['empresa', 'proveedor']

    fieldsets = (
        ('Información Principal', {
            'fields': ('empresa', 'proveedor', 'numero_pago')
        }),
        ('Pago', {
            'fields': ('fecha_pago', 'monto', 'metodo_pago', 'referencia')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'uuid', 'fecha_creacion', 'fecha_actualizacion',
                'usuario_creacion', 'usuario_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetallePagoProveedor)
class DetallePagoProveedorAdmin(admin.ModelAdmin):
    """Admin para Detalles de Pago a Proveedores."""
    list_display = ['pago', 'cuenta_por_pagar', 'monto_aplicado', 'fecha_creacion']
    list_filter = ['pago__fecha_pago', 'empresa']
    search_fields = ['pago__numero_pago', 'cuenta_por_pagar__numero_documento']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']
    autocomplete_fields = ['empresa', 'pago', 'cuenta_por_pagar']
    list_per_page = 25
    list_select_related = ['empresa', 'pago', 'cuenta_por_pagar']

    fieldsets = (
        ('Información Principal', {
            'fields': ('empresa', 'pago', 'cuenta_por_pagar', 'monto_aplicado')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

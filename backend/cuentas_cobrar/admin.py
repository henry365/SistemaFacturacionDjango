from django.contrib import admin
from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente


class DetalleCobroClienteInline(admin.TabularInline):
    model = DetalleCobroCliente
    extra = 0
    readonly_fields = ['cuenta_por_cobrar', 'monto_aplicado']


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'cliente', 'fecha_vencimiento', 'monto_original', 'monto_pendiente', 'estado']
    list_filter = ['estado', 'empresa', 'fecha_vencimiento']
    search_fields = ['numero_documento', 'cliente__nombre']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']
    date_hierarchy = 'fecha_vencimiento'


@admin.register(CobroCliente)
class CobroClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_recibo', 'cliente', 'fecha_cobro', 'monto', 'metodo_pago']
    list_filter = ['metodo_pago', 'empresa', 'fecha_cobro']
    search_fields = ['numero_recibo', 'cliente__nombre', 'referencia']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion']
    inlines = [DetalleCobroClienteInline]
    date_hierarchy = 'fecha_cobro'


@admin.register(DetalleCobroCliente)
class DetalleCobroClienteAdmin(admin.ModelAdmin):
    list_display = ['cobro', 'cuenta_por_cobrar', 'monto_aplicado']
    list_filter = ['cobro__fecha_cobro']
    search_fields = ['cobro__numero_recibo', 'cuenta_por_cobrar__numero_documento']

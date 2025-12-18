from django.contrib import admin
from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor


class DetallePagoProveedorInline(admin.TabularInline):
    model = DetallePagoProveedor
    extra = 0
    readonly_fields = ['cuenta_por_pagar', 'monto_aplicado']


@admin.register(CuentaPorPagar)
class CuentaPorPagarAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'proveedor', 'fecha_vencimiento', 'monto_original', 'monto_pendiente', 'estado']
    list_filter = ['estado', 'empresa', 'fecha_vencimiento']
    search_fields = ['numero_documento', 'proveedor__nombre']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion']
    date_hierarchy = 'fecha_vencimiento'


@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = ['numero_pago', 'proveedor', 'fecha_pago', 'monto', 'metodo_pago']
    list_filter = ['metodo_pago', 'empresa', 'fecha_pago']
    search_fields = ['numero_pago', 'proveedor__nombre', 'referencia']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion']
    inlines = [DetallePagoProveedorInline]
    date_hierarchy = 'fecha_pago'


@admin.register(DetallePagoProveedor)
class DetallePagoProveedorAdmin(admin.ModelAdmin):
    list_display = ['pago', 'cuenta_por_pagar', 'monto_aplicado']
    list_filter = ['pago__fecha_pago']
    search_fields = ['pago__numero_pago', 'cuenta_por_pagar__numero_documento']

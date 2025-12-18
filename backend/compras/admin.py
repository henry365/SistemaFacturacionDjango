from django.contrib import admin
from .models import (
    SolicitudCotizacionProveedor,
    OrdenCompra,
    DetalleOrdenCompra,
    Compra,
    DetalleCompra,
    Gasto
)


@admin.register(SolicitudCotizacionProveedor)
class SolicitudCotizacionProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'empresa', 'fecha_solicitud', 'estado', 'usuario_creacion', 'fecha_creacion')
    list_filter = ('estado', 'empresa', 'fecha_solicitud')
    search_fields = ('proveedor__nombre', 'detalles')
    list_select_related = ('proveedor', 'empresa', 'usuario_creacion')
    fieldsets = (
        (None, {
            'fields': ('empresa', 'proveedor', 'fecha_solicitud', 'estado', 'detalles')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


class DetalleOrdenCompraInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1
    fields = ('producto', 'cantidad', 'cantidad_recibida', 'costo_unitario', 'impuesto', 'descuento', 'tipo_linea', 'subtotal')
    readonly_fields = ('subtotal',)


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'empresa', 'fecha_emision', 'estado', 'total', 'usuario_creacion', 'usuario_aprobacion')
    list_filter = ('estado', 'empresa', 'fecha_emision')
    search_fields = ('proveedor__nombre', 'observaciones')
    inlines = [DetalleOrdenCompraInline]
    list_select_related = ('proveedor', 'empresa', 'usuario_creacion', 'usuario_aprobacion')
    list_prefetch_related = ('detalles__producto',)
    fieldsets = (
        (None, {
            'fields': ('empresa', 'proveedor', 'fecha_emision', 'fecha_entrega_esperada', 'estado')
        }),
        ('Información Financiera', {
            'fields': ('tasa_cambio', 'subtotal', 'impuestos', 'descuentos', 'total')
        }),
        ('Detalles', {
            'fields': ('condiciones_pago', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'usuario_aprobacion'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'usuario_aprobacion')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1
    fields = ('producto', 'cantidad', 'costo_unitario', 'impuesto', 'descuento', 'tipo_linea')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('numero_factura_proveedor', 'proveedor', 'empresa', 'fecha_compra', 'estado', 'total', 'monto_pagado', 'usuario_creacion')
    list_filter = ('estado', 'empresa', 'tipo_gasto', 'fecha_compra', 'fecha_registro')
    search_fields = ('numero_factura_proveedor', 'numero_ncf', 'proveedor__nombre')
    inlines = [DetalleCompraInline]
    list_select_related = ('proveedor', 'empresa', 'orden_compra', 'usuario_creacion')
    list_prefetch_related = ('detalles__producto',)
    fieldsets = (
        (None, {
            'fields': ('empresa', 'orden_compra', 'proveedor', 'tipo_gasto', 'fecha_compra', 'estado')
        }),
        ('Información Fiscal', {
            'fields': ('numero_factura_proveedor', 'numero_ncf', 'ncf_modificado')
        }),
        ('Información Financiera', {
            'fields': ('tasa_cambio', 'subtotal', 'impuestos', 'descuentos', 'total', 'monto_pagado')
        }),
        ('Retenciones DGII', {
            'fields': ('itbis_facturado', 'itbis_retenido', 'itbis_llevado_al_costo', 'isr_retenido'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_registro', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_registro', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'categoria', 'empresa', 'proveedor', 'fecha_gasto', 'total', 'estado', 'usuario_creacion')
    list_filter = ('estado', 'categoria', 'empresa', 'fecha_gasto')
    search_fields = ('descripcion', 'categoria', 'numero_factura', 'proveedor__nombre')
    list_select_related = ('proveedor', 'empresa', 'usuario_creacion')
    fieldsets = (
        (None, {
            'fields': ('empresa', 'proveedor', 'descripcion', 'categoria', 'fecha_gasto', 'estado')
        }),
        ('Información Fiscal', {
            'fields': ('numero_factura', 'numero_ncf')
        }),
        ('Información Financiera', {
            'fields': ('tasa_cambio', 'subtotal', 'impuestos', 'total')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)

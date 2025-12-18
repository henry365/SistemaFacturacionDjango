from django.contrib import admin
from .models import (
    Almacen, InventarioProducto, MovimientoInventario,
    ReservaStock, Lote, AlertaInventario,
    TransferenciaInventario, DetalleTransferencia,
    AjusteInventario, DetalleAjusteInventario,
    ConteoFisico, DetalleConteoFisico
)


# ========== ADMIN DE ALMACEN ==========

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'direccion')
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activo')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'direccion')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE INVENTARIO PRODUCTO ==========

@admin.register(InventarioProducto)
class InventarioProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'cantidad_disponible', 'costo_promedio', 'stock_minimo', 'stock_maximo', 'fecha_creacion')
    list_filter = ('almacen', 'metodo_valoracion', 'fecha_creacion')
    search_fields = ('producto__nombre', 'producto__codigo_sku', 'almacen__nombre')
    readonly_fields = ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('producto', 'almacen')
        }),
        ('Stock', {
            'fields': ('cantidad_disponible', 'costo_promedio', 'costo_unitario_actual')
        }),
        ('Control de Stock', {
            'fields': ('stock_minimo', 'stock_maximo', 'punto_reorden')
        }),
        ('Valoración', {
            'fields': ('metodo_valoracion',)
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE MOVIMIENTO INVENTARIO ==========

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'tipo_movimiento', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo_movimiento', 'almacen', 'fecha', 'tipo_documento_origen')
    search_fields = ('producto__nombre', 'producto__codigo_sku', 'referencia', 'almacen__nombre', 'usuario__username')
    readonly_fields = ('uuid', 'idempotency_key', 'fecha', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('producto', 'almacen', 'tipo_movimiento')
        }),
        ('Cantidades', {
            'fields': ('cantidad', 'costo_unitario')
        }),
        ('Trazabilidad', {
            'fields': ('lote', 'numero_serie', 'numero_lote_proveedor')
        }),
        ('Referencia', {
            'fields': ('referencia', 'tipo_documento_origen', 'documento_origen_id')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha', 'usuario', 'notas', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE RESERVA STOCK ==========

@admin.register(ReservaStock)
class ReservaStockAdmin(admin.ModelAdmin):
    list_display = ('inventario', 'cantidad_reservada', 'estado', 'fecha_reserva', 'fecha_vencimiento', 'usuario')
    list_filter = ('estado', 'fecha_reserva', 'fecha_vencimiento')
    search_fields = ('referencia', 'inventario__producto__nombre', 'usuario__username')
    readonly_fields = ('uuid', 'fecha_reserva', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('inventario', 'cantidad_reservada', 'estado')
        }),
        ('Referencia', {
            'fields': ('referencia', 'fecha_vencimiento')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'usuario', 'notas', 'fecha_reserva', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE LOTE ==========

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('codigo_lote', 'producto', 'almacen', 'cantidad_disponible', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'almacen', 'fecha_vencimiento', 'fecha_ingreso')
    search_fields = ('codigo_lote', 'numero_lote', 'producto__nombre', 'producto__codigo_sku')
    readonly_fields = ('uuid', 'fecha_ingreso', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('producto', 'almacen', 'codigo_lote', 'numero_lote')
        }),
        ('Fechas', {
            'fields': ('fecha_fabricacion', 'fecha_vencimiento', 'fecha_ingreso')
        }),
        ('Cantidades y Costos', {
            'fields': ('cantidad_inicial', 'cantidad_disponible', 'costo_unitario')
        }),
        ('Estado y Referencias', {
            'fields': ('estado', 'proveedor', 'compra')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'notas', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE ALERTA INVENTARIO ==========

@admin.register(AlertaInventario)
class AlertaInventarioAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'prioridad', 'inventario', 'lote', 'resuelta', 'fecha_alerta')
    list_filter = ('tipo', 'prioridad', 'resuelta', 'fecha_alerta')
    search_fields = ('mensaje', 'inventario__producto__nombre', 'lote__codigo_lote')
    readonly_fields = ('uuid', 'fecha_alerta', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo', 'prioridad', 'mensaje')
        }),
        ('Referencias', {
            'fields': ('inventario', 'lote')
        }),
        ('Resolución', {
            'fields': ('resuelta', 'fecha_resuelta', 'usuario_resolucion')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'fecha_alerta', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE TRANSFERENCIA INVENTARIO ==========

class DetalleTransferenciaInline(admin.TabularInline):
    model = DetalleTransferencia
    extra = 1
    fields = ('producto', 'lote', 'cantidad_solicitada', 'cantidad_enviada', 'cantidad_recibida', 'costo_unitario', 'observaciones')


@admin.register(TransferenciaInventario)
class TransferenciaInventarioAdmin(admin.ModelAdmin):
    list_display = ('numero_transferencia', 'almacen_origen', 'almacen_destino', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud', 'fecha_envio', 'fecha_recepcion')
    search_fields = ('numero_transferencia', 'almacen_origen__nombre', 'almacen_destino__nombre', 'motivo')
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_solicitud', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    inlines = [DetalleTransferenciaInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_transferencia', 'almacen_origen', 'almacen_destino', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_envio', 'fecha_recepcion')
        }),
        ('Usuarios', {
            'fields': ('usuario_solicitante', 'usuario_receptor')
        }),
        ('Detalles', {
            'fields': ('motivo',)
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_solicitante = request.user
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE AJUSTE INVENTARIO ==========

class DetalleAjusteInventarioInline(admin.TabularInline):
    model = DetalleAjusteInventario
    extra = 1
    fields = ('producto', 'lote', 'cantidad_anterior', 'cantidad_nueva', 'diferencia', 'costo_unitario', 'observaciones')
    readonly_fields = ('diferencia',)


@admin.register(AjusteInventario)
class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'almacen', 'tipo_ajuste', 'estado', 'fecha_ajuste', 'usuario_solicitante')
    list_filter = ('estado', 'tipo_ajuste', 'almacen', 'fecha_ajuste')
    search_fields = ('motivo', 'almacen__nombre', 'usuario_solicitante__username')
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_aprobacion', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    inlines = [DetalleAjusteInventarioInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('almacen', 'tipo_ajuste', 'motivo', 'fecha_ajuste', 'estado')
        }),
        ('Aprobación', {
            'fields': ('usuario_solicitante', 'usuario_aprobador', 'fecha_aprobacion', 'observaciones_aprobacion')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_solicitante = request.user
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


# ========== ADMIN DE CONTEO FÍSICO ==========

class DetalleConteoFisicoInline(admin.TabularInline):
    model = DetalleConteoFisico
    extra = 1
    fields = ('producto', 'lote', 'cantidad_sistema', 'cantidad_fisica', 'diferencia', 'observaciones', 'contado_por')
    readonly_fields = ('diferencia',)


@admin.register(ConteoFisico)
class ConteoFisicoAdmin(admin.ModelAdmin):
    list_display = ('numero_conteo', 'almacen', 'tipo_conteo', 'estado', 'fecha_conteo', 'usuario_responsable')
    list_filter = ('estado', 'tipo_conteo', 'almacen', 'fecha_conteo')
    search_fields = ('numero_conteo', 'almacen__nombre', 'usuario_responsable__username', 'observaciones')
    readonly_fields = ('uuid', 'idempotency_key', 'fecha_inicio', 'fecha_fin', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion')
    inlines = [DetalleConteoFisicoInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_conteo', 'almacen', 'tipo_conteo', 'estado', 'fecha_conteo')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Responsable', {
            'fields': ('usuario_responsable', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('uuid', 'idempotency_key', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_responsable = request.user
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)


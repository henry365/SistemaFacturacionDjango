"""
Modelos para movimientos de inventario, lotes y reservas.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from productos.models import Producto
import uuid

from ..constants import (
    ERROR_CANTIDAD_CERO, ERROR_CANTIDAD_NEGATIVA, ERROR_COSTO_NEGATIVO,
    ERROR_PRODUCTO_NO_PERTENECE_EMPRESA, ERROR_ALMACEN_NO_PERTENECE_EMPRESA,
    ERROR_LOTE_NO_PERTENECE_EMPRESA, ERROR_LOTE_NO_CORRESPONDE_PRODUCTO,
    ERROR_STOCK_INSUFICIENTE, TIPOS_MOVIMIENTO_SALIDA,
)


class MovimientoInventario(models.Model):
    """Registro de movimientos de inventario."""

    TIPO_MOVIMIENTO_CHOICES = (
        ('ENTRADA_COMPRA', 'Entrada por Compra'),
        ('ENTRADA_AJUSTE', 'Entrada por Ajuste'),
        ('SALIDA_VENTA', 'Salida por Venta'),
        ('SALIDA_AJUSTE', 'Salida por Ajuste'),
        ('TRANSFERENCIA_ENTRADA', 'Transferencia (Entrada)'),
        ('TRANSFERENCIA_SALIDA', 'Transferencia (Salida)'),
        ('DEVOLUCION_CLIENTE', 'Devolución de Cliente'),
        ('DEVOLUCION_PROVEEDOR', 'Devolución a Proveedor'),
        ('AJUSTE_INVENTARIO', 'Ajuste de Inventario'),
        ('AJUSTE_DIFERENCIA', 'Ajuste por Diferencia'),
        ('AJUSTE_DETERIORO', 'Ajuste por Deterioro'),
        ('AJUSTE_ROBO', 'Ajuste por Robo/Pérdida'),
        ('AJUSTE_DONACION', 'Ajuste por Donación'),
        ('AJUSTE_MUESTRA', 'Ajuste por Muestra'),
        ('AJUSTE_PRODUCCION', 'Ajuste por Producción'),
        ('AJUSTE_DESECHO', 'Ajuste por Desecho'),
    )

    TIPO_DOCUMENTO_CHOICES = (
        ('COMPRA', 'Compra'),
        ('FACTURA', 'Factura'),
        ('AJUSTE', 'Ajuste'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('DEVOLUCION', 'Devolución'),
        ('CONTEO', 'Conteo Físico'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='movimientos_inventario',
        null=True,
        blank=True
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    almacen = models.ForeignKey('inventario.Almacen', on_delete=models.PROTECT)
    tipo_movimiento = models.CharField(max_length=30, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    fecha = models.DateTimeField(auto_now_add=True, help_text="Fecha del movimiento")
    referencia = models.CharField(max_length=100, blank=True, null=True)

    # Trazabilidad
    lote = models.ForeignKey('Lote', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos')
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    numero_lote_proveedor = models.CharField(max_length=100, blank=True, null=True)

    tipo_documento_origen = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES, blank=True, null=True)
    documento_origen_id = models.IntegerField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos_realizados'
    )
    notas = models.TextField(blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario_modificados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['producto', 'almacen', '-fecha']),
            models.Index(fields=['tipo_movimiento', '-fecha']),
            models.Index(fields=['empresa', '-fecha']),
        ]
        permissions = [
            ('gestionar_movimientoinventario', 'Puede gestionar movimientos'),
            ('ver_kardex', 'Puede ver Kardex'),
        ]

    def clean(self):
        """Validaciones de negocio para MovimientoInventario."""
        from .almacen import InventarioProducto
        errors = {}

        # Validar cantidad positiva
        if self.cantidad is not None and self.cantidad <= 0:
            errors['cantidad'] = ERROR_CANTIDAD_CERO

        # Validar costo no negativo
        if self.costo_unitario is not None and self.costo_unitario < 0:
            errors['costo_unitario'] = ERROR_COSTO_NEGATIVO

        # Validar que producto y almacen pertenezcan a la empresa
        if self.producto and self.almacen and self.empresa:
            if hasattr(self.producto, 'empresa') and self.producto.empresa and self.producto.empresa != self.empresa:
                errors['producto'] = ERROR_PRODUCTO_NO_PERTENECE_EMPRESA

            if self.almacen.empresa and self.almacen.empresa != self.empresa:
                errors['almacen'] = ERROR_ALMACEN_NO_PERTENECE_EMPRESA

        # Validar lote
        if self.lote:
            if self.empresa and self.lote.empresa and self.lote.empresa != self.empresa:
                errors['lote'] = ERROR_LOTE_NO_PERTENECE_EMPRESA
            if self.producto and self.lote.producto != self.producto:
                errors['lote'] = ERROR_LOTE_NO_CORRESPONDE_PRODUCTO

        # Validar stock para salidas (solo si no hay otros errores)
        if not errors and self.tipo_movimiento in TIPOS_MOVIMIENTO_SALIDA:
            try:
                inventario = InventarioProducto.objects.get(
                    producto=self.producto,
                    almacen=self.almacen
                )
                if inventario.cantidad_disponible < self.cantidad:
                    errors['cantidad'] = ERROR_STOCK_INSUFICIENTE.format(
                        disponible=inventario.cantidad_disponible,
                        solicitado=self.cantidad
                    )
            except InventarioProducto.DoesNotExist:
                errors['producto'] = "No existe inventario para este producto en este almacén"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'producto', 'almacen', 'tipo_movimiento', 'cantidad', 'costo_unitario', 'lote']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.producto} - {self.cantidad}"


class ReservaStock(models.Model):
    """Reserva de stock para cotizaciones o pedidos pendientes."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('VENCIDA', 'Vencida'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='reservas_stock',
        null=True,
        blank=True
    )
    inventario = models.ForeignKey(
        'inventario.InventarioProducto',
        on_delete=models.PROTECT,
        related_name='reservas'
    )
    cantidad_reservada = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    referencia = models.CharField(max_length=100, help_text="ID de Cotización, Factura, etc.")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservas_realizadas'
    )
    notas = models.TextField(blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservas_stock_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservas_stock_modificadas',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Reserva de Stock'
        verbose_name_plural = 'Reservas de Stock'
        ordering = ['-fecha_reserva']
        indexes = [
            models.Index(fields=['estado', '-fecha_reserva']),
            models.Index(fields=['empresa', 'estado']),
        ]
        permissions = [
            ('gestionar_reservastock', 'Puede gestionar reservas de stock'),
        ]

    def clean(self):
        """Validaciones de negocio para ReservaStock."""
        errors = {}

        if self.cantidad_reservada is not None and self.cantidad_reservada <= 0:
            errors['cantidad_reservada'] = ERROR_CANTIDAD_CERO

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'inventario', 'cantidad_reservada', 'estado']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} - {self.inventario.producto} - {self.cantidad_reservada}"


class Lote(models.Model):
    """Lote de productos para control de trazabilidad y vencimiento."""

    ESTADO_CHOICES = (
        ('DISPONIBLE', 'Disponible'),
        ('BLOQUEADO', 'Bloqueado'),
        ('VENCIDO', 'Vencido'),
        ('AGOTADO', 'Agotado'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='lotes',
        null=True,
        blank=True
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='lotes')
    almacen = models.ForeignKey('inventario.Almacen', on_delete=models.PROTECT, related_name='lotes')

    codigo_lote = models.CharField(max_length=100, help_text="Código de lote/serie")
    numero_lote = models.CharField(max_length=100, blank=True, null=True)
    fecha_fabricacion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    cantidad_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_disponible = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.SET_NULL, null=True, blank=True)
    compra = models.ForeignKey('compras.Compra', on_delete=models.SET_NULL, null=True, blank=True)

    notas = models.TextField(blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lotes_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lotes_modificados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        unique_together = ('empresa', 'producto', 'almacen', 'codigo_lote')
        indexes = [
            models.Index(fields=['fecha_vencimiento']),
            models.Index(fields=['estado']),
            models.Index(fields=['codigo_lote']),
            models.Index(fields=['empresa', 'producto']),
        ]
        permissions = [
            ('gestionar_lote', 'Puede gestionar lotes'),
        ]

    def clean(self):
        """Validaciones de negocio para Lote."""
        errors = {}

        if self.cantidad_inicial is not None and self.cantidad_inicial < 0:
            errors['cantidad_inicial'] = ERROR_CANTIDAD_NEGATIVA

        if self.cantidad_disponible is not None and self.cantidad_disponible < 0:
            errors['cantidad_disponible'] = ERROR_CANTIDAD_NEGATIVA

        if self.costo_unitario is not None and self.costo_unitario < 0:
            errors['costo_unitario'] = ERROR_COSTO_NEGATIVO

        # Validar que producto y almacen pertenezcan a la empresa
        if self.producto and self.almacen and self.empresa:
            if hasattr(self.producto, 'empresa') and self.producto.empresa and self.producto.empresa != self.empresa:
                errors['producto'] = ERROR_PRODUCTO_NO_PERTENECE_EMPRESA

            if self.almacen.empresa and self.almacen.empresa != self.empresa:
                errors['almacen'] = ERROR_ALMACEN_NO_PERTENECE_EMPRESA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'producto', 'almacen', 'cantidad_inicial', 'cantidad_disponible', 'costo_unitario']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def esta_vencido(self):
        if self.fecha_vencimiento:
            return timezone.now().date() > self.fecha_vencimiento
        return False

    def dias_para_vencer(self):
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - timezone.now().date()
            return delta.days
        return None

    def __str__(self):
        return f"Lote {self.codigo_lote} - {self.producto}"


class AlertaInventario(models.Model):
    """Alertas generadas por condiciones de inventario."""

    TIPO_CHOICES = (
        ('STOCK_BAJO', 'Stock Bajo Mínimo'),
        ('STOCK_AGOTADO', 'Stock Agotado'),
        ('VENCIMIENTO_PROXIMO', 'Vencimiento Próximo'),
        ('VENCIMIENTO_VENCIDO', 'Producto Vencido'),
        ('STOCK_EXCESIVO', 'Stock Excesivo'),
    )

    PRIORIDAD_CHOICES = (
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='alertas_inventario',
        null=True,
        blank=True
    )
    inventario = models.ForeignKey(
        'inventario.InventarioProducto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, null=True, blank=True, related_name='alertas')

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='MEDIA')
    mensaje = models.TextField()
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    fecha_resuelta = models.DateTimeField(null=True, blank=True)
    resuelta = models.BooleanField(default=False)
    usuario_resolucion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_resueltas'
    )

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='alertas_inventario_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='alertas_inventario_modificadas',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Alerta de Inventario'
        verbose_name_plural = 'Alertas de Inventario'
        ordering = ['-fecha_alerta']
        indexes = [
            models.Index(fields=['resuelta', '-fecha_alerta']),
            models.Index(fields=['tipo', 'resuelta']),
            models.Index(fields=['empresa', 'resuelta']),
        ]
        permissions = [
            ('gestionar_alertainventario', 'Puede gestionar alertas de inventario'),
        ]

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.prioridad} - {self.fecha_alerta}"

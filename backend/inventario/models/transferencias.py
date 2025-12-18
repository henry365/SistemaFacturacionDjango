"""
Modelos para transferencias de inventario entre almacenes.
"""
from django.db import models
from django.conf import settings
from productos.models import Producto
import uuid


class TransferenciaInventario(models.Model):
    """Transferencia de productos entre almacenes."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('EN_TRANSITO', 'En Tránsito'),
        ('RECIBIDA_PARCIAL', 'Recibida Parcialmente'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='transferencias_inventario',
        null=True,
        blank=True
    )
    almacen_origen = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='transferencias_salida'
    )
    almacen_destino = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='transferencias_entrada'
    )

    numero_transferencia = models.CharField(max_length=50)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    motivo = models.TextField(blank=True, null=True)

    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transferencias_solicitadas'
    )
    usuario_receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferencias_recibidas'
    )

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transferencias_inventario_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transferencias_inventario_modificadas',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Transferencia de Inventario'
        verbose_name_plural = 'Transferencias de Inventario'
        ordering = ['-fecha_solicitud']
        unique_together = ('empresa', 'numero_transferencia')

    def __str__(self):
        return f"Transferencia {self.numero_transferencia} - {self.almacen_origen} → {self.almacen_destino}"


class DetalleTransferencia(models.Model):
    """Detalle de productos en una transferencia."""

    transferencia = models.ForeignKey(
        TransferenciaInventario,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_enviada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cantidad_recibida = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de Transferencia'
        verbose_name_plural = 'Detalles de Transferencias'

    def __str__(self):
        return f"{self.transferencia.numero_transferencia} - {self.producto} - {self.cantidad_solicitada}"

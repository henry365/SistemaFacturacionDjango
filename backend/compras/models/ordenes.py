"""
Modelos para órdenes de compra y sus detalles.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from proveedores.models import Proveedor
from productos.models import Producto
import uuid


class OrdenCompra(models.Model):
    """Orden de compra a un proveedor."""

    ESTADO_CHOICES = (
        ('BORRADOR', 'Borrador'),
        ('APROBADA', 'Aprobada'),
        ('ENVIADA', 'Enviada al Proveedor'),
        ('RECIBIDA_PARCIAL', 'Recibida Parcialmente'),
        ('RECIBIDA_TOTAL', 'Recibida Totalmente'),
        ('CANCELADA', 'Cancelada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='ordenes_compra',
        null=True,
        blank=True,
        db_index=True
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, db_index=True)
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_entrega_esperada = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR', db_index=True)

    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    condiciones_pago = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuentos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_compra_creadas',
        null=True,
        blank=True
    )
    usuario_aprobacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_compra_aprobadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_compra_modificadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['estado', '-fecha_emision']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})

        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})

        if self.subtotal < 0:
            raise ValidationError({'subtotal': 'El subtotal no puede ser negativo.'})

        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'})

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRITICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'proveedor', 'estado', 'total']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()
        super().save(*args, **kwargs)

    @property
    def estado_display(self):
        return self.get_estado_display()

    def __str__(self):
        return f"OC #{self.id} - {self.proveedor.nombre} - {self.fecha_emision} ({self.get_estado_display()})"


class DetalleOrdenCompra(models.Model):
    """Detalle de productos en una orden de compra."""

    TIPO_LINEA_CHOICES = (
        ('ALMACENABLE', 'Inventario'),
        ('GASTO', 'Gasto Directo'),
        ('ACTIVO', 'Activo Fijo'),
    )

    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_recibida = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tipo_linea = models.CharField(max_length=20, choices=TIPO_LINEA_CHOICES, default='ALMACENABLE')

    class Meta:
        indexes = [
            models.Index(fields=['orden', 'producto']),
        ]

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

        if self.cantidad_recibida < 0:
            raise ValidationError({'cantidad_recibida': 'La cantidad recibida no puede ser negativa.'})

        if self.cantidad_recibida > self.cantidad:
            raise ValidationError({'cantidad_recibida': 'La cantidad recibida no puede ser mayor que la cantidad solicitada.'})

        if self.costo_unitario < 0:
            raise ValidationError({'costo_unitario': 'El costo unitario no puede ser negativo.'})

        if self.descuento < 0:
            raise ValidationError({'descuento': 'El descuento no puede ser negativo.'})

        if self.impuesto < 0:
            raise ValidationError({'impuesto': 'El impuesto no puede ser negativo.'})

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRITICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return (self.cantidad * self.costo_unitario) - self.descuento + self.impuesto

    @property
    def tipo_linea_display(self):
        return self.get_tipo_linea_display()

    def __str__(self):
        return f"{self.orden} - {self.producto.nombre} x{self.cantidad}"

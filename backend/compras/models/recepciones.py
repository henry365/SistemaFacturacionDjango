"""
Modelos para recepciones de compra y devoluciones a proveedores.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from proveedores.models import Proveedor
from productos.models import Producto
import uuid


class RecepcionCompra(models.Model):
    """Recepción de mercancía de una orden de compra."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Parcialmente Recibida'),
        ('COMPLETA', 'Completamente Recibida'),
        ('CANCELADA', 'Cancelada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='recepciones_compra',
        db_index=True
    )
    orden_compra = models.ForeignKey(
        'compras.OrdenCompra',
        on_delete=models.PROTECT,
        related_name='recepciones',
        db_index=True
    )
    almacen = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='recepciones_compra',
        db_index=True
    )

    numero_recepcion = models.CharField(max_length=20, unique=True, editable=False)
    fecha_recepcion = models.DateField(db_index=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)
    observaciones = models.TextField(blank=True)

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recepciones_compra_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recepciones_compra_modificadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Recepción de Compra'
        verbose_name_plural = 'Recepciones de Compra'
        ordering = ['-fecha_recepcion']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['orden_compra', 'estado']),
            models.Index(fields=['empresa', 'fecha_recepcion']),
        ]

    def clean(self):
        if self.orden_compra and self.empresa and self.orden_compra.empresa != self.empresa:
            raise ValidationError({'orden_compra': 'La orden de compra debe pertenecer a la misma empresa.'})

        if self.almacen and self.empresa and self.almacen.empresa != self.empresa:
            raise ValidationError({'almacen': 'El almacén debe pertenecer a la misma empresa.'})

        if self.orden_compra and self.orden_compra.estado not in ['APROBADA', 'ENVIADA', 'RECIBIDA_PARCIAL']:
            raise ValidationError({'orden_compra': 'La orden de compra debe estar aprobada o enviada para poder recibir mercancía.'})

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRITICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'orden_compra', 'almacen', 'estado']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        if not self.numero_recepcion:
            from django.db.models import Max
            ultimo = RecepcionCompra.objects.filter(empresa=self.empresa).aggregate(Max('id'))['id__max'] or 0
            self.numero_recepcion = f"REC-{self.empresa_id:04d}-{(ultimo + 1):06d}"
        super().save(*args, **kwargs)

    @property
    def estado_display(self):
        return self.get_estado_display()

    def __str__(self):
        return f"{self.numero_recepcion} - OC #{self.orden_compra_id} ({self.get_estado_display()})"


class DetalleRecepcion(models.Model):
    """Detalle de productos recibidos en una recepción de compra."""

    recepcion = models.ForeignKey(RecepcionCompra, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    detalle_orden = models.ForeignKey(
        'compras.DetalleOrdenCompra',
        on_delete=models.PROTECT,
        related_name='recepciones',
        db_index=True
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)

    cantidad_ordenada = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_recibida = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_rechazada = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True, related_name='recepciones')
    numero_lote = models.CharField(max_length=50, blank=True, null=True, help_text="Número de lote del proveedor")
    fecha_vencimiento = models.DateField(blank=True, null=True)

    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Detalle de Recepción'
        verbose_name_plural = 'Detalles de Recepción'
        indexes = [
            models.Index(fields=['recepcion', 'producto']),
        ]

    def clean(self):
        if self.cantidad_recibida < 0:
            raise ValidationError({'cantidad_recibida': 'La cantidad recibida no puede ser negativa.'})

        if self.cantidad_rechazada < 0:
            raise ValidationError({'cantidad_rechazada': 'La cantidad rechazada no puede ser negativa.'})

        if (self.cantidad_recibida + self.cantidad_rechazada) > self.cantidad_ordenada:
            raise ValidationError('La suma de cantidad recibida y rechazada no puede exceder la cantidad ordenada.')

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRITICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recepcion.numero_recepcion} - {self.producto.nombre} ({self.cantidad_recibida}/{self.cantidad_ordenada})"


class DevolucionProveedor(models.Model):
    """Devolución de mercancía a proveedores."""

    ESTADO_CHOICES = (
        ('BORRADOR', 'Borrador'),
        ('CONFIRMADA', 'Confirmada'),
        ('ENVIADA', 'Enviada al Proveedor'),
        ('ACEPTADA', 'Aceptada por Proveedor'),
        ('CANCELADA', 'Cancelada'),
    )

    MOTIVO_CHOICES = (
        ('DEFECTO', 'Producto Defectuoso'),
        ('ERROR', 'Error en Pedido'),
        ('GARANTIA', 'Garantía'),
        ('CADUCADO', 'Producto Caducado'),
        ('DANADO', 'Producto Dañado'),
        ('OTRO', 'Otro'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='devoluciones_proveedor',
        db_index=True
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='devoluciones', db_index=True)
    compra = models.ForeignKey(
        'compras.Compra',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devoluciones',
        db_index=True
    )

    numero_devolucion = models.CharField(max_length=20, unique=True, editable=False)
    fecha = models.DateField(db_index=True)
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES, default='DEFECTO')
    descripcion_motivo = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR', db_index=True)

    # Totales
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    genera_nota_credito = models.BooleanField(default=True, help_text="Si es True, genera ajuste en CxP")

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='devoluciones_proveedor_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='devoluciones_proveedor_modificadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Devolución a Proveedor'
        verbose_name_plural = 'Devoluciones a Proveedores'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['empresa', 'fecha']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})

        if self.compra and self.compra.empresa != self.empresa:
            raise ValidationError({'compra': 'La compra debe pertenecer a la misma empresa.'})

        if self.compra and self.compra.proveedor != self.proveedor:
            raise ValidationError({'compra': 'La compra debe ser del mismo proveedor.'})

        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRITICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            # Excluir campos calculados de validación para evitar problemas con decimales
            campos_criticos = ['empresa', 'proveedor', 'compra', 'estado']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        if not self.numero_devolucion:
            from django.db.models import Max
            ultimo = DevolucionProveedor.objects.filter(empresa=self.empresa).aggregate(Max('id'))['id__max'] or 0
            self.numero_devolucion = f"DEV-{self.empresa_id:04d}-{(ultimo + 1):06d}"
        super().save(*args, **kwargs)

    def calcular_totales(self):
        from decimal import Decimal, ROUND_HALF_UP
        detalles = self.detalles.all()
        subtotal = sum(d.cantidad * d.costo_unitario for d in detalles)
        impuestos = sum(d.impuesto for d in detalles)
        # Redondear a 2 decimales para cumplir con el modelo
        self.subtotal = Decimal(subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.impuestos = Decimal(impuestos).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.total = self.subtotal + self.impuestos
        self.save(update_fields=['subtotal', 'impuestos', 'total'])

    @property
    def estado_display(self):
        return self.get_estado_display()

    @property
    def motivo_display(self):
        return self.get_motivo_display()

    def __str__(self):
        return f"{self.numero_devolucion} - {self.proveedor.nombre} ({self.get_estado_display()})"


class DetalleDevolucionProveedor(models.Model):
    """Detalle de productos devueltos a un proveedor."""

    devolucion = models.ForeignKey(DevolucionProveedor, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)

    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True)
    almacen = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='devoluciones_proveedor',
        db_index=True
    )

    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Detalle de Devolución'
        verbose_name_plural = 'Detalles de Devolución'
        indexes = [
            models.Index(fields=['devolucion', 'producto']),
        ]

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

        if self.costo_unitario < 0:
            raise ValidationError({'costo_unitario': 'El costo unitario no puede ser negativo.'})

        if self.almacen and self.devolucion.empresa and self.almacen.empresa != self.devolucion.empresa:
            raise ValidationError({'almacen': 'El almacén debe pertenecer a la misma empresa.'})

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
        return self.cantidad * self.costo_unitario

    @property
    def total(self):
        return self.subtotal + self.impuesto

    def __str__(self):
        return f"{self.devolucion.numero_devolucion} - {self.producto.nombre} x{self.cantidad}"

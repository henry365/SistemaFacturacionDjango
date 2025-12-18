"""
Modelos para compras, detalles de compra y gastos operativos.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from proveedores.models import Proveedor
from productos.models import Producto
import uuid


class Compra(models.Model):
    """Registro de una compra a un proveedor."""

    ESTADO_CHOICES = (
        ('REGISTRADA', 'Registrada'),
        ('CXP', 'En Cuentas por Pagar'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    )

    TIPO_GASTO_CHOICES = (
        ('01', '01 - Gastos de Personal'),
        ('02', '02 - Gastos por Trabajos, Suministros y Servicios'),
        ('03', '03 - Arrendamientos'),
        ('04', '04 - Gastos de Activos Fijos'),
        ('05', '05 - Gastos de Representación'),
        ('06', '06 - Otras Deducciones Admitidas'),
        ('07', '07 - Gastos Financieros'),
        ('08', '08 - Gastos Extraordinarios'),
        ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
        ('10', '10 - Adquisiciones de Activos'),
        ('11', '11 - Gastos de Seguros'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='compras',
        null=True,
        blank=True,
        db_index=True
    )
    orden_compra = models.ForeignKey(
        'compras.OrdenCompra',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compras_relacionadas',
        db_index=True
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, db_index=True)

    tipo_gasto = models.CharField(
        max_length=2,
        choices=TIPO_GASTO_CHOICES,
        default='02',
        db_index=True,
        help_text="Tipo de Bienes y Servicios (DGII 606)"
    )
    fecha_compra = models.DateField(help_text="Fecha de la factura del proveedor", db_index=True)
    numero_factura_proveedor = models.CharField(max_length=50, db_index=True)
    numero_ncf = models.CharField(max_length=20, blank=True, null=True, help_text="Número de Comprobante Fiscal")
    ncf_modificado = models.CharField(max_length=20, blank=True, null=True, help_text="NCF afectado por Nota de Crédito/Débito")

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='REGISTRADA', db_index=True)

    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    # Totales
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Campos DGII
    itbis_facturado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    itbis_retenido = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    itbis_llevado_al_costo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    isr_retenido = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Retención de Renta")

    descuentos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_pagado = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Campos de auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='compras_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='compras_modificadas',
        null=True,
        blank=True
    )
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        unique_together = ('empresa', 'proveedor', 'numero_factura_proveedor')
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['empresa', 'fecha_compra']),
            models.Index(fields=['estado', '-fecha_registro']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})

        if self.orden_compra and self.orden_compra.empresa != self.empresa:
            raise ValidationError({'orden_compra': 'La orden de compra debe pertenecer a la misma empresa.'})

        if self.numero_factura_proveedor:
            self.numero_factura_proveedor = self.numero_factura_proveedor.strip()
            if not self.numero_factura_proveedor:
                raise ValidationError({'numero_factura_proveedor': 'El número de factura no puede estar vacío.'})

        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})

        if self.monto_pagado < 0:
            raise ValidationError({'monto_pagado': 'El monto pagado no puede ser negativo.'})

        if self.monto_pagado > self.total:
            raise ValidationError({'monto_pagado': 'El monto pagado no puede ser mayor que el total.'})

        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'})

    @property
    def estado_display(self):
        return self.get_estado_display()

    @property
    def tipo_gasto_display(self):
        return self.get_tipo_gasto_display()

    def __str__(self):
        return f"Compra {self.numero_factura_proveedor} - {self.proveedor.nombre} ({self.get_estado_display()})"


class DetalleCompra(models.Model):
    """Detalle de productos en una compra."""

    TIPO_LINEA_CHOICES = (
        ('ALMACENABLE', 'Inventario'),
        ('GASTO', 'Gasto Directo'),
        ('ACTIVO', 'Activo Fijo'),
    )

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tipo_linea = models.CharField(max_length=20, choices=TIPO_LINEA_CHOICES, default='ALMACENABLE')

    class Meta:
        indexes = [
            models.Index(fields=['compra', 'producto']),
        ]

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

        if self.costo_unitario < 0:
            raise ValidationError({'costo_unitario': 'El costo unitario no puede ser negativo.'})

        if self.descuento < 0:
            raise ValidationError({'descuento': 'El descuento no puede ser negativo.'})

        if self.impuesto < 0:
            raise ValidationError({'impuesto': 'El impuesto no puede ser negativo.'})

        # Auto-detectar tipo basado en producto
        if not self.pk and self.producto:
            if self.producto.tipo_producto == 'ALMACENABLE':
                self.tipo_linea = 'ALMACENABLE'
            elif self.producto.tipo_producto == 'ACTIVO_FIJO':
                self.tipo_linea = 'ACTIVO'
            else:
                self.tipo_linea = 'GASTO'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def tipo_linea_display(self):
        return self.get_tipo_linea_display()

    def __str__(self):
        return f"{self.compra} - {self.producto.nombre} x{self.cantidad}"


class Gasto(models.Model):
    """Gastos operativos que no implican inventario."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO', 'Pagado'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='gastos',
        null=True,
        blank=True,
        db_index=True
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        help_text="Opcional, ej: Edesur"
    )
    descripcion = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100, db_index=True, help_text="Ej: Servicios Públicos, Nómina, Mantenimiento")
    fecha_gasto = models.DateField(db_index=True)
    numero_factura = models.CharField(max_length=50, blank=True, null=True)
    numero_ncf = models.CharField(max_length=20, blank=True, null=True)

    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gastos_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gastos_modificados',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha_gasto']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['empresa', 'categoria']),
            models.Index(fields=['empresa', 'fecha_gasto']),
            models.Index(fields=['estado', '-fecha_gasto']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})

        if self.descripcion:
            self.descripcion = self.descripcion.strip()
            if not self.descripcion:
                raise ValidationError({'descripcion': 'La descripción no puede estar vacía.'})

        if self.categoria:
            self.categoria = self.categoria.strip()
            if not self.categoria:
                raise ValidationError({'categoria': 'La categoría no puede estar vacía.'})

        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})

        if self.subtotal < 0:
            raise ValidationError({'subtotal': 'El subtotal no puede ser negativo.'})

        if self.impuestos < 0:
            raise ValidationError({'impuestos': 'Los impuestos no pueden ser negativos.'})

        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'})

    @property
    def estado_display(self):
        return self.get_estado_display()

    def __str__(self):
        return f"{self.descripcion} - {self.fecha_gasto} ({self.get_estado_display()})"

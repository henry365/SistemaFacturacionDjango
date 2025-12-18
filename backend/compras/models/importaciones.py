"""
Modelos para liquidaciones de importación y retenciones fiscales.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from proveedores.models import Proveedor
import uuid


class LiquidacionImportacion(models.Model):
    """Liquidación de gastos de importación para compras internacionales."""

    ESTADO_CHOICES = (
        ('BORRADOR', 'Borrador'),
        ('LIQUIDADA', 'Liquidada'),
        ('CANCELADA', 'Cancelada'),
    )

    INCOTERM_CHOICES = (
        ('FOB', 'FOB - Free On Board'),
        ('CIF', 'CIF - Cost, Insurance and Freight'),
        ('EXW', 'EXW - Ex Works'),
        ('FCA', 'FCA - Free Carrier'),
        ('CFR', 'CFR - Cost and Freight'),
        ('DAP', 'DAP - Delivered at Place'),
        ('DDP', 'DDP - Delivered Duty Paid'),
    )

    METODO_PRORRATEO_CHOICES = (
        ('VALOR', 'Por Valor FOB'),
        ('PESO', 'Por Peso'),
        ('VOLUMEN', 'Por Volumen'),
        ('UNIDADES', 'Por Unidades'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='liquidaciones_importacion',
        db_index=True
    )
    compra = models.ForeignKey(
        'compras.Compra',
        on_delete=models.PROTECT,
        related_name='liquidaciones',
        db_index=True
    )

    numero_liquidacion = models.CharField(max_length=20, unique=True, editable=False)
    fecha = models.DateField(db_index=True)
    incoterm = models.CharField(max_length=3, choices=INCOTERM_CHOICES, default='FOB')
    metodo_prorrateo = models.CharField(max_length=10, choices=METODO_PRORRATEO_CHOICES, default='VALOR')

    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    # Totales
    total_fob = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Valor FOB de la mercancía")
    total_gastos = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Total de gastos de importación")
    total_cif = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Costo total nacionalizado")

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR', db_index=True)
    observaciones = models.TextField(blank=True)

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='liquidaciones_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='liquidaciones_modificadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Liquidación de Importación'
        verbose_name_plural = 'Liquidaciones de Importación'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['compra', 'estado']),
            models.Index(fields=['empresa', 'fecha']),
        ]

    def clean(self):
        if self.compra and self.empresa and self.compra.empresa != self.empresa:
            raise ValidationError({'compra': 'La compra debe pertenecer a la misma empresa.'})

        if self.compra and not self.compra.proveedor.es_internacional:
            raise ValidationError({'compra': 'La liquidación de importación solo aplica para proveedores internacionales.'})

        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'})

    def save(self, *args, **kwargs):
        if not self.numero_liquidacion:
            from django.db.models import Max
            ultimo = LiquidacionImportacion.objects.filter(empresa=self.empresa).aggregate(Max('id'))['id__max'] or 0
            self.numero_liquidacion = f"LIQ-{self.empresa_id:04d}-{(ultimo + 1):06d}"
        super().save(*args, **kwargs)

    def calcular_totales(self):
        self.total_gastos = sum(g.monto for g in self.gastos.all())
        self.total_cif = self.total_fob + self.total_gastos
        self.save(update_fields=['total_gastos', 'total_cif'])

    @property
    def estado_display(self):
        return self.get_estado_display()

    @property
    def incoterm_display(self):
        return self.get_incoterm_display()

    def __str__(self):
        return f"{self.numero_liquidacion} - Compra {self.compra.numero_factura_proveedor} ({self.get_estado_display()})"


class GastoImportacion(models.Model):
    """Gastos adicionales de una importación."""

    TIPO_GASTO_CHOICES = (
        ('FLETE', 'Flete Internacional'),
        ('SEGURO', 'Seguro de Carga'),
        ('ADUANA', 'Gastos de Aduana'),
        ('IMPUESTOS', 'Impuestos de Importación'),
        ('TRANSPORTE', 'Transporte Local'),
        ('ALMACENAJE', 'Almacenaje'),
        ('AGENTE', 'Comisión Agente Aduanal'),
        ('OTROS', 'Otros Gastos'),
    )

    liquidacion = models.ForeignKey(LiquidacionImportacion, on_delete=models.CASCADE, related_name='gastos', db_index=True)
    tipo = models.CharField(max_length=20, choices=TIPO_GASTO_CHOICES)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=14, decimal_places=2)

    proveedor_gasto = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos_importacion',
        help_text="Proveedor del servicio (naviera, agente, etc.)"
    )
    numero_factura = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'Gasto de Importación'
        verbose_name_plural = 'Gastos de Importación'
        indexes = [
            models.Index(fields=['liquidacion', 'tipo']),
        ]

    def clean(self):
        if self.monto < 0:
            raise ValidationError({'monto': 'El monto no puede ser negativo.'})

    @property
    def tipo_display(self):
        return self.get_tipo_display()

    def __str__(self):
        return f"{self.liquidacion.numero_liquidacion} - {self.get_tipo_display()}: {self.monto}"


class TipoRetencion(models.Model):
    """Catálogo de tipos de retenciones fiscales."""

    CATEGORIA_CHOICES = (
        ('ISR', 'Impuesto Sobre la Renta'),
        ('ITBIS', 'ITBIS Retenido'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='tipos_retencion',
        db_index=True,
        null=True,
        blank=True
    )
    codigo = models.CharField(max_length=10, help_text="Código DGII (ej: 01, 02)")
    nombre = models.CharField(max_length=100, help_text="Ej: ISR Personas Físicas, ITBIS 30%")
    categoria = models.CharField(max_length=10, choices=CATEGORIA_CHOICES, db_index=True)
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de retención (ej: 10.00 para 10%)"
    )
    aplica_a_persona_fisica = models.BooleanField(
        default=False,
        help_text="Si aplica automáticamente a proveedores persona física"
    )
    aplica_a_persona_juridica = models.BooleanField(
        default=False,
        help_text="Si aplica automáticamente a proveedores persona jurídica"
    )
    activo = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tipo de Retención'
        verbose_name_plural = 'Tipos de Retención'
        ordering = ['categoria', 'codigo']
        unique_together = ('empresa', 'codigo')

    def clean(self):
        if self.porcentaje is not None and (self.porcentaje < 0 or self.porcentaje > 100):
            raise ValidationError({'porcentaje': 'El porcentaje debe estar entre 0 y 100.'})

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.porcentaje}%)"


class RetencionCompra(models.Model):
    """Retenciones aplicadas a una compra específica."""

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='retenciones_compra',
        db_index=True,
        null=True,
        blank=True
    )
    compra = models.ForeignKey(
        'compras.Compra',
        on_delete=models.CASCADE,
        related_name='retenciones',
        db_index=True
    )
    tipo_retencion = models.ForeignKey(
        TipoRetencion,
        on_delete=models.PROTECT,
        related_name='retenciones_aplicadas'
    )
    base_imponible = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Monto sobre el cual se calcula la retención"
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje aplicado (copia del tipo al momento de aplicar)"
    )
    monto_retenido = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Monto de la retención"
    )
    fecha_aplicacion = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='retenciones_creadas',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Retención en Compra'
        verbose_name_plural = 'Retenciones en Compras'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['empresa', 'compra']),
            models.Index(fields=['tipo_retencion', 'fecha_aplicacion']),
        ]

    def clean(self):
        if self.compra and self.empresa and self.compra.empresa != self.empresa:
            raise ValidationError({'compra': 'La compra debe pertenecer a la misma empresa.'})

        if self.tipo_retencion and self.empresa and self.tipo_retencion.empresa and self.tipo_retencion.empresa != self.empresa:
            raise ValidationError({'tipo_retencion': 'El tipo de retención debe pertenecer a la misma empresa.'})

        if self.monto_retenido is not None and self.monto_retenido < 0:
            raise ValidationError({'monto_retenido': 'El monto retenido no puede ser negativo.'})

    def save(self, *args, **kwargs):
        from decimal import Decimal as Dec
        if self.monto_retenido is None or self.monto_retenido == 0:
            self.monto_retenido = (self.base_imponible * self.porcentaje) / Dec('100')
        super().save(*args, **kwargs)
        self._update_compra_totales()

    def _update_compra_totales(self):
        """Actualiza los totales de retención en la compra."""
        from django.db.models import Sum, Case, When, Value, DecimalField
        from decimal import Decimal as Dec

        totales = RetencionCompra.objects.filter(
            compra=self.compra
        ).aggregate(
            isr_total=Sum(
                Case(
                    When(tipo_retencion__categoria='ISR', then='monto_retenido'),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            ),
            itbis_total=Sum(
                Case(
                    When(tipo_retencion__categoria='ITBIS', then='monto_retenido'),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )
        )

        self.compra.isr_retenido = totales['isr_total'] or Dec('0')
        self.compra.itbis_retenido = totales['itbis_total'] or Dec('0')
        self.compra.save(update_fields=['isr_retenido', 'itbis_retenido'])

    def __str__(self):
        return f"{self.compra.numero_factura_proveedor} - {self.tipo_retencion.nombre}: {self.monto_retenido}"

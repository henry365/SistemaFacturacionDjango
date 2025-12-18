"""
Modelos para Cuentas por Cobrar (CxC)

Django 6.0: Usa GeneratedField para monto_pendiente
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class CuentaPorCobrar(models.Model):
    """
    Representa una deuda de un cliente.
    Se genera a partir de una Factura de venta a credito.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Cobro Parcial'),
        ('COBRADA', 'Cobrada'),
        ('VENCIDA', 'Vencida'),
        ('ANULADA', 'Anulada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='cuentas_por_cobrar',
        db_index=True
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='cuentas_por_cobrar',
        db_index=True
    )
    factura = models.OneToOneField(
        'ventas.Factura',
        on_delete=models.PROTECT,
        related_name='cuenta_por_cobrar',
        db_index=True,
        help_text="Factura de venta origen"
    )

    numero_documento = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Numero de factura"
    )
    fecha_documento = models.DateField(help_text="Fecha de la factura")
    fecha_vencimiento = models.DateField(db_index=True, help_text="Fecha limite de cobro")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    monto_original = models.DecimalField(max_digits=14, decimal_places=2, help_text="Monto total de la factura")
    monto_cobrado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_pendiente = GeneratedField(
        expression=F('monto_original') - F('monto_cobrado'),
        output_field=models.DecimalField(max_digits=14, decimal_places=2),
        db_persist=True,
        help_text="Saldo pendiente (calculado automáticamente)"
    )

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)
    observaciones = models.TextField(blank=True, null=True)

    # Auditoria
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cxc_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cxc_modificadas'
    )

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['-fecha_vencimiento']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['empresa', 'fecha_vencimiento']),
        ]

    def clean(self):
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        if self.monto_original and self.monto_original < 0:
            raise ValidationError({'monto_original': 'El monto no puede ser negativo.'})
        if self.monto_pendiente and self.monto_pendiente < 0:
            raise ValidationError({'monto_pendiente': 'El monto pendiente no puede ser negativo.'})

    def actualizar_estado(self):
        """Actualiza el estado basado en el monto pendiente"""
        from datetime import date
        if self.monto_pendiente <= 0:
            self.estado = 'COBRADA'
        elif self.monto_cobrado > 0:
            self.estado = 'PARCIAL'
        elif self.fecha_vencimiento and self.fecha_vencimiento < date.today():
            self.estado = 'VENCIDA'
        else:
            self.estado = 'PENDIENTE'

    def __str__(self):
        return f"CxC {self.numero_documento} - {self.cliente.nombre} ({self.get_estado_display()})"


class CobroCliente(models.Model):
    """
    Representa un cobro/recibo de ingreso de un cliente.
    Puede distribuirse entre multiples CuentaPorCobrar.
    """
    METODO_PAGO_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('TARJETA', 'Tarjeta'),
        ('OTRO', 'Otro'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='cobros_clientes',
        db_index=True
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='pagos_realizados',
        db_index=True
    )

    numero_recibo = models.CharField(max_length=50, unique=True, db_index=True)
    fecha_cobro = models.DateField(db_index=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, db_index=True)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Numero de transferencia, cheque, etc.")
    observaciones = models.TextField(blank=True, null=True)

    # Auditoria
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cobros_clientes_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cobros_clientes_modificados'
    )

    class Meta:
        verbose_name = 'Cobro de Cliente'
        verbose_name_plural = 'Cobros de Clientes'
        ordering = ['-fecha_cobro']
        indexes = [
            models.Index(fields=['empresa', 'fecha_cobro']),
            models.Index(fields=['cliente', 'fecha_cobro']),
        ]

    def clean(self):
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        if self.monto and self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})

    def __str__(self):
        return f"Cobro {self.numero_recibo} - {self.cliente.nombre} ({self.monto})"


class DetalleCobroCliente(models.Model):
    """
    Distribucion del cobro entre diferentes CuentaPorCobrar.
    Permite que un cobro cubra multiples facturas pendientes.
    """
    cobro = models.ForeignKey(
        CobroCliente,
        on_delete=models.CASCADE,
        related_name='detalles',
        db_index=True
    )
    cuenta_por_cobrar = models.ForeignKey(
        CuentaPorCobrar,
        on_delete=models.PROTECT,
        related_name='cobros_aplicados',
        db_index=True
    )
    monto_aplicado = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Cobro a Cliente'
        verbose_name_plural = 'Detalles de Cobro a Cliente'
        unique_together = ('cobro', 'cuenta_por_cobrar')

    def clean(self):
        if self.monto_aplicado and self.monto_aplicado <= 0:
            raise ValidationError({'monto_aplicado': 'El monto aplicado debe ser mayor a cero.'})
        if self.cuenta_por_cobrar and self.monto_aplicado:
            if self.monto_aplicado > self.cuenta_por_cobrar.monto_pendiente:
                raise ValidationError({
                    'monto_aplicado': f'El monto aplicado no puede exceder el saldo pendiente ({self.cuenta_por_cobrar.monto_pendiente}).'
                })

    def __str__(self):
        return f"{self.cobro.numero_recibo} -> {self.cuenta_por_cobrar.numero_documento} ({self.monto_aplicado})"

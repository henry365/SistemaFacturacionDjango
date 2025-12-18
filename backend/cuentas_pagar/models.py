"""
Modelos para Cuentas por Pagar (CxP)

Django 6.0: Usa GeneratedField para monto_pendiente
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class CuentaPorPagar(models.Model):
    """
    Representa una deuda con un proveedor.
    Se genera a partir de una Compra confirmada.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
        ('ANULADA', 'Anulada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='cuentas_por_pagar',
        db_index=True
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.PROTECT,
        related_name='cuentas_por_pagar',
        db_index=True
    )
    compra = models.OneToOneField(
        'compras.Compra',
        on_delete=models.PROTECT,
        related_name='cuenta_por_pagar',
        db_index=True,
        help_text="Factura de compra origen"
    )

    numero_documento = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Numero de factura del proveedor"
    )
    fecha_documento = models.DateField(help_text="Fecha de la factura")
    fecha_vencimiento = models.DateField(db_index=True, help_text="Fecha limite de pago")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    monto_original = models.DecimalField(max_digits=14, decimal_places=2, help_text="Monto total de la factura")
    monto_pagado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_pendiente = GeneratedField(
        expression=F('monto_original') - F('monto_pagado'),
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
        related_name='cxp_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cxp_modificadas'
    )

    class Meta:
        verbose_name = 'Cuenta por Pagar'
        verbose_name_plural = 'Cuentas por Pagar'
        ordering = ['-fecha_vencimiento']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['empresa', 'fecha_vencimiento']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})
        if self.monto_original and self.monto_original < 0:
            raise ValidationError({'monto_original': 'El monto no puede ser negativo.'})
        if self.monto_pendiente and self.monto_pendiente < 0:
            raise ValidationError({'monto_pendiente': 'El monto pendiente no puede ser negativo.'})

    def actualizar_estado(self):
        """Actualiza el estado basado en el monto pendiente"""
        from datetime import date
        if self.monto_pendiente <= 0:
            self.estado = 'PAGADA'
        elif self.monto_pagado > 0:
            self.estado = 'PARCIAL'
        elif self.fecha_vencimiento and self.fecha_vencimiento < date.today():
            self.estado = 'VENCIDA'
        else:
            self.estado = 'PENDIENTE'

    def __str__(self):
        return f"CxP {self.numero_documento} - {self.proveedor.nombre} ({self.get_estado_display()})"


class PagoProveedor(models.Model):
    """
    Representa un pago realizado a un proveedor.
    Puede distribuirse entre multiples CuentaPorPagar.
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
        related_name='pagos_proveedores',
        db_index=True
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.PROTECT,
        related_name='pagos_recibidos',
        db_index=True
    )

    numero_pago = models.CharField(max_length=50, unique=True, db_index=True)
    fecha_pago = models.DateField(db_index=True)
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
        related_name='pagos_proveedores_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pagos_proveedores_modificados'
    )

    class Meta:
        verbose_name = 'Pago a Proveedor'
        verbose_name_plural = 'Pagos a Proveedores'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['empresa', 'fecha_pago']),
            models.Index(fields=['proveedor', 'fecha_pago']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})
        if self.monto and self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})

    def __str__(self):
        return f"Pago {self.numero_pago} - {self.proveedor.nombre} ({self.monto})"


class DetallePagoProveedor(models.Model):
    """
    Distribucion del pago entre diferentes CuentaPorPagar.
    Permite que un pago cubra multiples facturas pendientes.
    """
    pago = models.ForeignKey(
        PagoProveedor,
        on_delete=models.CASCADE,
        related_name='detalles',
        db_index=True
    )
    cuenta_por_pagar = models.ForeignKey(
        CuentaPorPagar,
        on_delete=models.PROTECT,
        related_name='pagos_aplicados',
        db_index=True
    )
    monto_aplicado = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Pago a Proveedor'
        verbose_name_plural = 'Detalles de Pago a Proveedor'
        unique_together = ('pago', 'cuenta_por_pagar')

    def clean(self):
        if self.monto_aplicado and self.monto_aplicado <= 0:
            raise ValidationError({'monto_aplicado': 'El monto aplicado debe ser mayor a cero.'})
        if self.cuenta_por_pagar and self.monto_aplicado:
            if self.monto_aplicado > self.cuenta_por_pagar.monto_pendiente:
                raise ValidationError({
                    'monto_aplicado': f'El monto aplicado no puede exceder el saldo pendiente ({self.cuenta_por_pagar.monto_pendiente}).'
                })

    def __str__(self):
        return f"{self.pago.numero_pago} -> {self.cuenta_por_pagar.numero_documento} ({self.monto_aplicado})"

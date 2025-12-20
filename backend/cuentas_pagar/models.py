"""
Modelos para Cuentas por Pagar (CxP)

Django 6.0: Usa GeneratedField para monto_pendiente
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

from .constants import (
    ESTADO_CXP_CHOICES, ESTADO_CXP_PENDIENTE, ESTADO_CXP_PARCIAL,
    ESTADO_CXP_PAGADA, ESTADO_CXP_VENCIDA, ESTADO_CXP_ANULADA,
    ESTADOS_CXP_TERMINALES, ESTADOS_CXP_PAGABLES,
    METODO_PAGO_CHOICES, METODOS_REQUIEREN_REFERENCIA,
    ERROR_PROVEEDOR_EMPRESA, ERROR_COMPRA_EMPRESA, ERROR_MONTO_NEGATIVO,
    ERROR_MONTO_PENDIENTE_NEGATIVO, ERROR_MONTO_MAYOR_CERO,
    ERROR_MONTO_APLICADO_MAYOR_CERO, ERROR_MONTO_EXCEDE_PENDIENTE,
    ERROR_REFERENCIA_REQUERIDA, ERROR_FECHA_VENCIMIENTO_PASADA,
    ERROR_MONTO_PAGADO_EXCEDE, ERROR_PAGO_EMPRESA
)


class CuentaPorPagar(models.Model):
    """
    Representa una deuda con un proveedor.
    Se genera a partir de una Compra confirmada.
    """
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

    estado = models.CharField(max_length=20, choices=ESTADO_CXP_CHOICES, default=ESTADO_CXP_PENDIENTE, db_index=True)
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
        blank=True,
        related_name='cxp_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cxp_modificadas'
    )

    class Meta:
        verbose_name = 'Cuenta por Pagar'
        verbose_name_plural = 'Cuentas por Pagar'
        ordering = ['-fecha_vencimiento']
        unique_together = ('empresa', 'proveedor', 'numero_documento')
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['empresa', 'fecha_vencimiento']),
        ]

    def clean(self):
        errors = {}

        # Validar que el proveedor pertenece a la empresa
        if self.proveedor and self.empresa and self.proveedor.empresa_id != self.empresa_id:
            errors['proveedor'] = ERROR_PROVEEDOR_EMPRESA

        # Validar que la compra pertenece a la empresa
        if self.compra and self.empresa and self.compra.empresa_id != self.empresa_id:
            errors['compra'] = ERROR_COMPRA_EMPRESA

        # Validar monto original
        if self.monto_original is not None and self.monto_original < 0:
            errors['monto_original'] = ERROR_MONTO_NEGATIVO

        # Validar monto pagado
        if self.monto_pagado is not None and self.monto_pagado < 0:
            errors['monto_pagado'] = ERROR_MONTO_NEGATIVO

        # Validar que monto pagado no exceda monto original
        if self.monto_original is not None and self.monto_pagado is not None:
            if self.monto_pagado > self.monto_original:
                errors['monto_pagado'] = ERROR_MONTO_PAGADO_EXCEDE

        # Validar fecha de vencimiento
        if self.fecha_documento and self.fecha_vencimiento:
            if self.fecha_vencimiento < self.fecha_documento:
                errors['fecha_vencimiento'] = ERROR_FECHA_VENCIMIENTO_PASADA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'proveedor', 'compra', 'monto_original', 'monto_pagado']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def actualizar_estado(self):
        """Actualiza el estado basado en el monto pendiente"""
        from datetime import date

        if self.estado in ESTADOS_CXP_TERMINALES:
            return

        # Refrescar para obtener monto_pendiente calculado
        self.refresh_from_db()

        if self.monto_pendiente <= 0:
            self.estado = ESTADO_CXP_PAGADA
        elif self.monto_pagado > 0:
            self.estado = ESTADO_CXP_PARCIAL
        elif self.fecha_vencimiento and self.fecha_vencimiento < date.today():
            self.estado = ESTADO_CXP_VENCIDA
        else:
            self.estado = ESTADO_CXP_PENDIENTE

    def __str__(self):
        return f"CxP {self.numero_documento} - {self.proveedor.nombre} ({self.get_estado_display()})"


class PagoProveedor(models.Model):
    """
    Representa un pago realizado a un proveedor.
    Puede distribuirse entre multiples CuentaPorPagar.
    """
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
        blank=True,
        related_name='pagos_proveedores_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        errors = {}

        # Validar que el proveedor pertenece a la empresa
        if self.proveedor and self.empresa and self.proveedor.empresa_id != self.empresa_id:
            errors['proveedor'] = ERROR_PROVEEDOR_EMPRESA

        # Validar monto
        if self.monto is not None and self.monto <= 0:
            errors['monto'] = ERROR_MONTO_MAYOR_CERO

        # Validar referencia requerida según método de pago
        if self.metodo_pago in METODOS_REQUIEREN_REFERENCIA:
            if not self.referencia or not self.referencia.strip():
                errors['referencia'] = ERROR_REFERENCIA_REQUERIDA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'proveedor', 'monto', 'metodo_pago', 'referencia']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pago {self.numero_pago} - {self.proveedor.nombre} ({self.monto})"


class DetallePagoProveedor(models.Model):
    """
    Distribucion del pago entre diferentes CuentaPorPagar.
    Permite que un pago cubra multiples facturas pendientes.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='detalles_pagos_proveedores',
        db_index=True,
        null=True,
        blank=True
    )
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

    # Auditoria
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_pagos_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_pagos_modificados'
    )

    class Meta:
        verbose_name = 'Detalle de Pago a Proveedor'
        verbose_name_plural = 'Detalles de Pago a Proveedor'
        unique_together = ('pago', 'cuenta_por_pagar')
        indexes = [
            models.Index(fields=['empresa', 'pago']),
        ]

    def clean(self):
        errors = {}

        # Validar monto aplicado
        if self.monto_aplicado is not None and self.monto_aplicado <= 0:
            errors['monto_aplicado'] = ERROR_MONTO_APLICADO_MAYOR_CERO

        # Validar que no excede el monto pendiente
        if self.cuenta_por_pagar and self.monto_aplicado:
            # Excluir el monto actual si estamos actualizando
            monto_pendiente = self.cuenta_por_pagar.monto_pendiente
            if self.pk:
                # Si es una actualización, sumamos el monto anterior al pendiente
                try:
                    original = DetallePagoProveedor.objects.get(pk=self.pk)
                    monto_pendiente += original.monto_aplicado
                except DetallePagoProveedor.DoesNotExist:
                    pass
            if self.monto_aplicado > monto_pendiente:
                errors['monto_aplicado'] = f'{ERROR_MONTO_EXCEDE_PENDIENTE} ({monto_pendiente}).'

        # Validar que el pago pertenece a la misma empresa
        if self.pago and self.empresa and self.pago.empresa_id != self.empresa_id:
            errors['pago'] = ERROR_PAGO_EMPRESA

        # Validar que la cuenta por pagar pertenece a la misma empresa
        if self.cuenta_por_pagar and self.empresa:
            if self.cuenta_por_pagar.empresa_id != self.empresa_id:
                errors['cuenta_por_pagar'] = ERROR_PROVEEDOR_EMPRESA

        # Validar que la cuenta por pagar está en estado pagable
        if self.cuenta_por_pagar:
            if self.cuenta_por_pagar.estado not in ESTADOS_CXP_PAGABLES:
                if not self.pk:  # Solo en creación
                    errors['cuenta_por_pagar'] = f'La cuenta por pagar no está en estado pagable ({self.cuenta_por_pagar.estado}).'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto-asignar empresa desde el pago si no está establecida
        if not self.empresa_id and self.pago_id:
            self.empresa_id = self.pago.empresa_id

        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'pago', 'cuenta_por_pagar', 'monto_aplicado']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pago.numero_pago} -> {self.cuenta_por_pagar.numero_documento} ({self.monto_aplicado})"

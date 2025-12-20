"""
Modelos para Cuentas por Cobrar (CxC)

Django 6.0: Usa GeneratedField para monto_pendiente
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

from .constants import (
    ESTADO_CXC_CHOICES, ESTADO_CXC_PENDIENTE, ESTADO_CXC_PARCIAL,
    ESTADO_CXC_COBRADA, ESTADO_CXC_VENCIDA, ESTADO_CXC_ANULADA,
    ESTADOS_CXC_TERMINALES,
    METODO_PAGO_CHOICES, METODOS_REQUIEREN_REFERENCIA,
    ERROR_CLIENTE_EMPRESA, ERROR_MONTO_NEGATIVO, ERROR_MONTO_PENDIENTE_NEGATIVO,
    ERROR_MONTO_MAYOR_CERO, ERROR_MONTO_APLICADO_MAYOR_CERO,
    ERROR_MONTO_EXCEDE_PENDIENTE, ERROR_REFERENCIA_REQUERIDA,
    ERROR_FECHA_VENCIMIENTO_PASADA, ERROR_FACTURA_EMPRESA, ERROR_COBRO_EMPRESA, ERROR_MONTO_COBRADO_EXCEDE, ERROR_FECHA_FUTURA
)


class CuentaPorCobrar(models.Model):
    """
    Representa una deuda de un cliente.
    Se genera a partir de una Factura de venta a credito.
    """
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

    estado = models.CharField(max_length=20, choices=ESTADO_CXC_CHOICES, default=ESTADO_CXC_PENDIENTE, db_index=True)
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
        related_name='cxc_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        errors = {}

        # Validar que el cliente pertenece a la empresa
        if self.cliente and self.empresa and self.cliente.empresa_id != self.empresa_id:
            errors['cliente'] = ERROR_CLIENTE_EMPRESA

        # Validar que la factura pertenece a la empresa
        if self.factura and self.empresa and self.factura.empresa_id != self.empresa_id:
            errors['factura'] = ERROR_FACTURA_EMPRESA

        # Validar monto original
        if self.monto_original is not None and self.monto_original < 0:
            errors['monto_original'] = ERROR_MONTO_NEGATIVO

        # Validar monto cobrado
        if self.monto_cobrado is not None and self.monto_cobrado < 0:
            errors['monto_cobrado'] = ERROR_MONTO_NEGATIVO

        # Validar que monto cobrado no exceda monto original
        if self.monto_original is not None and self.monto_cobrado is not None:
            if self.monto_cobrado > self.monto_original:
                errors['monto_cobrado'] = ERROR_MONTO_COBRADO_EXCEDE

        # Validar que fecha_documento no sea futura
        from datetime import date as date_class
        if self.fecha_documento and self.fecha_documento > date_class.today():
            errors['fecha_documento'] = ERROR_FECHA_FUTURA

        # Validar fecha de vencimiento
        if self.fecha_documento and self.fecha_vencimiento:
            if self.fecha_vencimiento < self.fecha_documento:
                errors['fecha_vencimiento'] = ERROR_FECHA_VENCIMIENTO_PASADA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'cliente', 'factura', 'monto_original', 'monto_cobrado']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def actualizar_estado(self):
        """Actualiza el estado basado en el monto pendiente"""
        from datetime import date

        if self.estado in ESTADOS_CXC_TERMINALES:
            return

        # Refrescar para obtener monto_pendiente calculado
        self.refresh_from_db()

        if self.monto_pendiente <= 0:
            self.estado = ESTADO_CXC_COBRADA
        elif self.monto_cobrado > 0:
            self.estado = ESTADO_CXC_PARCIAL
        elif self.fecha_vencimiento and self.fecha_vencimiento < date.today():
            self.estado = ESTADO_CXC_VENCIDA
        else:
            self.estado = ESTADO_CXC_PENDIENTE

    def __str__(self):
        return f"CxC {self.numero_documento} - {self.cliente.nombre} ({self.get_estado_display()})"


class CobroCliente(models.Model):
    """
    Representa un cobro/recibo de ingreso de un cliente.
    Puede distribuirse entre multiples CuentaPorCobrar.
    """
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
        blank=True,
        related_name='cobros_clientes_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        errors = {}

        # Validar que el cliente pertenece a la empresa
        if self.cliente and self.empresa and self.cliente.empresa_id != self.empresa_id:
            errors['cliente'] = ERROR_CLIENTE_EMPRESA

        # Validar monto
        if self.monto is not None and self.monto <= 0:
            errors['monto'] = ERROR_MONTO_MAYOR_CERO

        # Validar referencia requerida según método de pago
        if self.metodo_pago in METODOS_REQUIEREN_REFERENCIA:
            if not self.referencia or not self.referencia.strip():
                errors['referencia'] = ERROR_REFERENCIA_REQUERIDA

        # Validar que fecha_cobro no sea futura
        from datetime import date as date_class
        if self.fecha_cobro and self.fecha_cobro > date_class.today():
            errors['fecha_cobro'] = ERROR_FECHA_FUTURA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'cliente', 'monto', 'metodo_pago', 'referencia', 'fecha_cobro']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cobro {self.numero_recibo} - {self.cliente.nombre} ({self.monto})"


class DetalleCobroCliente(models.Model):
    """
    Distribucion del cobro entre diferentes CuentaPorCobrar.
    Permite que un cobro cubra multiples facturas pendientes.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='detalles_cobros_clientes',
        db_index=True,
        null=True,
        blank=True
    )
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

    # Auditoria
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_cobros_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_cobros_modificados'
    )

    class Meta:
        verbose_name = 'Detalle de Cobro a Cliente'
        verbose_name_plural = 'Detalles de Cobro a Cliente'
        unique_together = ('cobro', 'cuenta_por_cobrar')
        indexes = [
            models.Index(fields=['empresa', 'cobro']),
        ]

    def clean(self):
        errors = {}

        # Validar monto aplicado
        if self.monto_aplicado is not None and self.monto_aplicado <= 0:
            errors['monto_aplicado'] = ERROR_MONTO_APLICADO_MAYOR_CERO

        # Validar que no excede el monto pendiente
        if self.cuenta_por_cobrar and self.monto_aplicado:
            # Excluir el monto actual si estamos actualizando
            monto_pendiente = self.cuenta_por_cobrar.monto_pendiente
            if self.pk:
                # Si es una actualización, sumamos el monto anterior al pendiente
                try:
                    original = DetalleCobroCliente.objects.get(pk=self.pk)
                    monto_pendiente += original.monto_aplicado
                except DetalleCobroCliente.DoesNotExist:
                    pass
            if self.monto_aplicado > monto_pendiente:
                errors['monto_aplicado'] = f'{ERROR_MONTO_EXCEDE_PENDIENTE} ({monto_pendiente}).'

        # Validar que el cobro pertenece a la misma empresa
        if self.cobro and self.empresa and self.cobro.empresa_id != self.empresa_id:
            errors['cobro'] = ERROR_COBRO_EMPRESA

        # Validar que la cuenta por cobrar pertenece a la misma empresa
        if self.cuenta_por_cobrar and self.empresa:
            if self.cuenta_por_cobrar.empresa_id != self.empresa_id:
                errors['cuenta_por_cobrar'] = ERROR_CLIENTE_EMPRESA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto-asignar empresa desde el cobro si no está establecida
        if not self.empresa_id and self.cobro_id:
            self.empresa_id = self.cobro.empresa_id

        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'cobro', 'cuenta_por_cobrar', 'monto_aplicado']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cobro.numero_recibo} -> {self.cuenta_por_cobrar.numero_documento} ({self.monto_aplicado})"

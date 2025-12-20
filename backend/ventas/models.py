"""
Modelos para Ventas

Django 6.0: Usa GeneratedField para DetalleFactura.importe
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
from clientes.models import Cliente
from productos.models import Producto
from vendedores.models import Vendedor
import uuid

from .constants import (
    ESTADO_COTIZACION_CHOICES, ESTADO_COTIZACION_PENDIENTE,
    ESTADO_FACTURA_CHOICES, ESTADO_FACTURA_PENDIENTE_PAGO,
    TIPO_VENTA_CHOICES, TIPO_VENTA_CONTADO, TIPO_VENTA_CREDITO,
    ESTADO_LISTA_CHOICES, ESTADO_LISTA_PENDIENTE,
    PRIORIDAD_CHOICES, PRIORIDAD_NORMAL,
    METODO_PAGO_CHOICES,
    TASA_CAMBIO_DEFAULT, TOTAL_DEFAULT, MONTO_DEFAULT,
    ERROR_CLIENTE_EMPRESA, ERROR_VENDEDOR_EMPRESA,
    ERROR_COTIZACION_EMPRESA, ERROR_FACTURA_EMPRESA,
    ERROR_TOTAL_NEGATIVO, ERROR_MONTO_NEGATIVO, ERROR_MONTO_MAYOR_CERO,
    ERROR_MONTO_PENDIENTE_NEGATIVO, ERROR_MONTO_PENDIENTE_MAYOR_TOTAL,
    ERROR_TASA_CAMBIO_INVALIDA, ERROR_CANTIDAD_INVALIDA,
    ERROR_PRECIO_NEGATIVO, ERROR_DESCUENTO_NEGATIVO,
    ERROR_ITBIS_NEGATIVO, ERROR_IMPUESTO_NEGATIVO,
    ERROR_LIMITE_CREDITO_EXCEDIDO, ERROR_VIGENCIA_INVALIDA, ERROR_MOTIVO_VACIO,
)

class CotizacionCliente(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='cotizaciones', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    fecha = models.DateField(auto_now_add=True)
    vigencia = models.DateField(help_text="Fecha de vencimiento de la cotización")
    estado = models.CharField(max_length=20, choices=ESTADO_COTIZACION_CHOICES, default=ESTADO_COTIZACION_PENDIENTE, db_index=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=TOTAL_DEFAULT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['-fecha']),
        ]
        permissions = [
            ('gestionar_cotizacion', 'Puede gestionar cotizaciones'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.vendedor and self.empresa and self.vendedor.empresa != self.empresa:
            raise ValidationError({'vendedor': ERROR_VENDEDOR_EMPRESA})

        if self.vigencia and self.fecha and self.vigencia < self.fecha:
            raise ValidationError({'vigencia': ERROR_VIGENCIA_INVALIDA})

        if self.total < 0:
            raise ValidationError({'total': ERROR_TOTAL_NEGATIVO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'vendedor', 'vigencia', 'total', 'estado']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def estado_display(self):
        """Obtener el display del estado"""
        return self.get_estado_display()

    def __str__(self):
        return f"Cotización {self.cliente.nombre} - {self.fecha} ({self.get_estado_display()})"

class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(CotizacionCliente, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=MONTO_DEFAULT)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=MONTO_DEFAULT)

    class Meta:
        indexes = [
            models.Index(fields=['cotizacion', 'producto']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': ERROR_CANTIDAD_INVALIDA})

        if self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': ERROR_PRECIO_NEGATIVO})

        if self.descuento < 0:
            raise ValidationError({'descuento': ERROR_DESCUENTO_NEGATIVO})

        if self.impuesto < 0:
            raise ValidationError({'impuesto': ERROR_IMPUESTO_NEGATIVO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cotizacion} - {self.producto.nombre} x{self.cantidad}"

class ListaEsperaProducto(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='listas_espera', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_index=True)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_LISTA_CHOICES, default=ESTADO_LISTA_PENDIENTE, db_index=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default=PRIORIDAD_NORMAL, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notas = models.TextField(blank=True, null=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Lista de Espera'
        verbose_name_plural = 'Listas de Espera'
        ordering = ['-fecha_solicitud', 'prioridad']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['producto', 'estado']),
            models.Index(fields=['prioridad', '-fecha_solicitud']),
        ]
        permissions = [
            ('gestionar_lista_espera', 'Puede gestionar listas de espera'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.cantidad_solicitada <= 0:
            raise ValidationError({'cantidad_solicitada': ERROR_CANTIDAD_INVALIDA})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'producto', 'cantidad_solicitada', 'estado', 'prioridad']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def estado_display(self):
        """Obtener el display del estado"""
        return self.get_estado_display()
    
    @property
    def prioridad_display(self):
        """Obtener el display de la prioridad"""
        return self.get_prioridad_display()

    def __str__(self):
        return f"{self.cliente} espera {self.producto} ({self.cantidad_solicitada})"

class Factura(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='facturas', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    cotizacion = models.ForeignKey(CotizacionCliente, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True)
    numero_factura = models.CharField(max_length=50, unique=True, db_index=True, help_text="Secuencia interna única")
    ncf = models.CharField(max_length=20, blank=True, null=True, help_text="Número de Comprobante Fiscal (si aplica)")

    # Flags de Venta Informal / Sin Impuestos
    venta_sin_comprobante = models.BooleanField(default=False, help_text="Venta informal sin NCF")
    venta_sin_impuestos = models.BooleanField(default=False, help_text="No calcular ITBIS en esta venta")

    estado = models.CharField(max_length=20, choices=ESTADO_FACTURA_CHOICES, default=ESTADO_FACTURA_PENDIENTE_PAGO, db_index=True)
    tipo_venta = models.CharField(max_length=10, choices=TIPO_VENTA_CHOICES, default=TIPO_VENTA_CONTADO, db_index=True)

    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=TASA_CAMBIO_DEFAULT)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=MONTO_DEFAULT)
    itbis = models.DecimalField(max_digits=14, decimal_places=2, default=MONTO_DEFAULT)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=MONTO_DEFAULT)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=TOTAL_DEFAULT)
    monto_pendiente = models.DecimalField(max_digits=14, decimal_places=2, default=MONTO_DEFAULT)

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['numero_factura']),
        ]
        permissions = [
            ('gestionar_factura', 'Puede gestionar facturas'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.vendedor and self.empresa and self.vendedor.empresa != self.empresa:
            raise ValidationError({'vendedor': ERROR_VENDEDOR_EMPRESA})

        if self.cotizacion and self.cotizacion.empresa != self.empresa:
            raise ValidationError({'cotizacion': ERROR_COTIZACION_EMPRESA})

        if self.total < 0:
            raise ValidationError({'total': ERROR_TOTAL_NEGATIVO})

        if self.monto_pendiente < 0:
            raise ValidationError({'monto_pendiente': ERROR_MONTO_PENDIENTE_NEGATIVO})

        if self.monto_pendiente > self.total:
            raise ValidationError({'monto_pendiente': ERROR_MONTO_PENDIENTE_MAYOR_TOTAL})

        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': ERROR_TASA_CAMBIO_INVALIDA})

        # Validar límite de crédito si es venta a crédito
        if self.tipo_venta == TIPO_VENTA_CREDITO and self.cliente:
            if self.total > self.cliente.limite_credito:
                raise ValidationError({
                    'total': ERROR_LIMITE_CREDITO_EXCEDIDO.format(limite=self.cliente.limite_credito)
                })

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'cliente', 'vendedor', 'cotizacion', 'total', 'monto_pendiente',
            'tasa_cambio', 'estado', 'tipo_venta'
        ]
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def estado_display(self):
        """Obtener el display del estado"""
        return self.get_estado_display()
    
    @property
    def tipo_venta_display(self):
        """Obtener el display del tipo de venta"""
        return self.get_tipo_venta_display()

    def __str__(self):
        return f"Factura {self.numero_factura} - {self.cliente.nombre} ({self.get_estado_display()})"

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    itbis = models.DecimalField(max_digits=12, decimal_places=2, default=MONTO_DEFAULT)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=MONTO_DEFAULT)
    # Django 6.0: Importe calculado automáticamente
    importe = GeneratedField(
        expression=(F('cantidad') * F('precio_unitario')) - F('descuento') + F('itbis'),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
        help_text="Importe total (calculado automáticamente)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['factura', 'producto']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': ERROR_CANTIDAD_INVALIDA})

        if self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': ERROR_PRECIO_NEGATIVO})

        if self.descuento < 0:
            raise ValidationError({'descuento': ERROR_DESCUENTO_NEGATIVO})

        if self.itbis < 0:
            raise ValidationError({'itbis': ERROR_ITBIS_NEGATIVO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.factura} - {self.producto.nombre} x{self.cantidad}"

class PagoCaja(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='pagos_caja', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    facturas = models.ManyToManyField(Factura, related_name='pagos')  # Un pago puede cubrir varias facturas
    fecha_pago = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, db_index=True)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Pago en Caja'
        verbose_name_plural = 'Pagos en Caja'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['empresa', 'fecha_pago']),
            models.Index(fields=['cliente', 'fecha_pago']),
            models.Index(fields=['metodo_pago', '-fecha_pago']),
        ]
        permissions = [
            ('gestionar_pago_caja', 'Puede gestionar pagos en caja'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.monto <= 0:
            raise ValidationError({'monto': ERROR_MONTO_MAYOR_CERO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'monto', 'metodo_pago']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def metodo_pago_display(self):
        """Obtener el display del método de pago"""
        return self.get_metodo_pago_display()

    def __str__(self):
        return f"Pago {self.cliente.nombre} - {self.monto} ({self.get_metodo_pago_display()})"

class NotaCredito(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='notas_credito', null=True, blank=True, db_index=True)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='notas_credito', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    motivo = models.TextField()
    aplicada = models.BooleanField(default=False, db_index=True, help_text="Si ya se aplicó al saldo")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Nota de Crédito'
        verbose_name_plural = 'Notas de Crédito'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['cliente', 'aplicada']),
        ]
        permissions = [
            ('gestionar_nota_credito', 'Puede gestionar notas de crédito'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': ERROR_FACTURA_EMPRESA})

        if self.monto <= 0:
            raise ValidationError({'monto': ERROR_MONTO_MAYOR_CERO})

        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': ERROR_MOTIVO_VACIO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'factura', 'monto', 'motivo', 'aplicada']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"NC {self.cliente.nombre} - {self.monto} ({self.fecha})"

class NotaDebito(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='notas_debito', null=True, blank=True, db_index=True)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='notas_debito', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    motivo = models.TextField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Nota de Débito'
        verbose_name_plural = 'Notas de Débito'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['cliente', 'fecha']),
        ]
        permissions = [
            ('gestionar_nota_debito', 'Puede gestionar notas de débito'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': ERROR_FACTURA_EMPRESA})

        if self.monto <= 0:
            raise ValidationError({'monto': ERROR_MONTO_MAYOR_CERO})

        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': ERROR_MOTIVO_VACIO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'factura', 'monto', 'motivo']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ND {self.cliente.nombre} - {self.monto} ({self.fecha})"

class DevolucionVenta(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='devoluciones_venta', null=True, blank=True, db_index=True)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='devoluciones', db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Devolución de Venta'
        verbose_name_plural = 'Devoluciones de Venta'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['cliente', 'fecha']),
        ]
        permissions = [
            ('gestionar_devolucion_venta', 'Puede gestionar devoluciones de venta'),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': ERROR_CLIENTE_EMPRESA})

        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': ERROR_FACTURA_EMPRESA})

        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': ERROR_MOTIVO_VACIO})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar para campos críticos."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['cliente', 'factura', 'motivo']
        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Devolución {self.factura.numero_factura} - {self.cliente.nombre} ({self.fecha})"

class DetalleDevolucion(models.Model):
    devolucion = models.ForeignKey(DevolucionVenta, on_delete=models.CASCADE, related_name='detalles', db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_index=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['devolucion', 'producto']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': ERROR_CANTIDAD_INVALIDA})

    def save(self, *args, **kwargs):
        """Ejecuta full_clean antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.devolucion} - {self.producto.nombre} x{self.cantidad}"

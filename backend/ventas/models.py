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

class CotizacionCliente(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('EXPIRADA', 'Expirada'),
    )

    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='cotizaciones', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    fecha = models.DateField(auto_now_add=True)
    vigencia = models.DateField(help_text="Fecha de vencimiento de la cotización")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.vendedor and self.empresa and self.vendedor.empresa != self.empresa:
            raise ValidationError({'vendedor': 'El vendedor debe pertenecer a la misma empresa.'})
        
        if self.vigencia and self.fecha and self.vigencia < self.fecha:
            raise ValidationError({'vigencia': 'La fecha de vigencia no puede ser anterior a la fecha de creación.'})
        
        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})

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
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=['cotizacion', 'producto']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})
        
        if self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': 'El precio unitario no puede ser negativo.'})
        
        if self.descuento < 0:
            raise ValidationError({'descuento': 'El descuento no puede ser negativo.'})
        
        if self.impuesto < 0:
            raise ValidationError({'impuesto': 'El impuesto no puede ser negativo.'})

    def __str__(self):
        return f"{self.cotizacion} - {self.producto.nombre} x{self.cantidad}"

class ListaEsperaProducto(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('NOTIFICADO', 'Notificado'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    )
    PRIORIDAD_CHOICES = (
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
    )

    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='listas_espera', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_index=True)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='NORMAL', db_index=True)
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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.cantidad_solicitada <= 0:
            raise ValidationError({'cantidad_solicitada': 'La cantidad solicitada debe ser mayor a cero.'})

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
    ESTADO_CHOICES = (
        ('PENDIENTE_PAGO', 'Pendiente de Pago'),
        ('PAGADA_PARCIAL', 'Pagada Parcialmente'),
        ('PAGADA', 'Pagada'),
        ('CANCELADA', 'Cancelada'),
    )
    TIPO_VENTA_CHOICES = (
        ('CONTADO', 'Contado'),
        ('CREDITO', 'Crédito'),
    )

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
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE_PAGO', db_index=True)
    tipo_venta = models.CharField(max_length=10, choices=TIPO_VENTA_CHOICES, default='CONTADO', db_index=True)
    
    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    itbis = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_pendiente = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.vendedor and self.empresa and self.vendedor.empresa != self.empresa:
            raise ValidationError({'vendedor': 'El vendedor debe pertenecer a la misma empresa.'})
        
        if self.cotizacion and self.cotizacion.empresa != self.empresa:
            raise ValidationError({'cotizacion': 'La cotización debe pertenecer a la misma empresa.'})
        
        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo.'})
        
        if self.monto_pendiente < 0:
            raise ValidationError({'monto_pendiente': 'El monto pendiente no puede ser negativo.'})
        
        if self.monto_pendiente > self.total:
            raise ValidationError({'monto_pendiente': 'El monto pendiente no puede ser mayor que el total.'})
        
        if self.tasa_cambio <= 0:
            raise ValidationError({'tasa_cambio': 'La tasa de cambio debe ser mayor a cero.'})
        
        # Validar límite de crédito si es venta a crédito
        if self.tipo_venta == 'CREDITO' and self.cliente:
            if self.total > self.cliente.limite_credito:
                raise ValidationError({
                    'total': f'El total excede el límite de crédito del cliente ({self.cliente.limite_credito}).'
                })

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
    itbis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

        if self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': 'El precio unitario no puede ser negativo.'})

        if self.descuento < 0:
            raise ValidationError({'descuento': 'El descuento no puede ser negativo.'})

        if self.itbis < 0:
            raise ValidationError({'itbis': 'El ITBIS no puede ser negativo.'})

    def __str__(self):
        return f"{self.factura} - {self.producto.nombre} x{self.cantidad}"

class PagoCaja(models.Model):
    METODO_PAGO_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    )

    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='pagos_caja', null=True, blank=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_index=True)
    facturas = models.ManyToManyField(Factura, related_name='pagos') # Un pago puede cubrir varias facturas
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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})

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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': 'La factura debe pertenecer a la misma empresa.'})
        
        if self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})
        
        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': 'El motivo no puede estar vacío.'})

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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': 'La factura debe pertenecer a la misma empresa.'})
        
        if self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})
        
        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': 'El motivo no puede estar vacío.'})

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

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.cliente and self.empresa and self.cliente.empresa != self.empresa:
            raise ValidationError({'cliente': 'El cliente debe pertenecer a la misma empresa.'})
        
        if self.factura and self.factura.empresa != self.empresa:
            raise ValidationError({'factura': 'La factura debe pertenecer a la misma empresa.'})
        
        if self.motivo:
            self.motivo = self.motivo.strip()
            if not self.motivo:
                raise ValidationError({'motivo': 'El motivo no puede estar vacío.'})

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
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

    def __str__(self):
        return f"{self.devolucion} - {self.producto.nombre} x{self.cantidad}"

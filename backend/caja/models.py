from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Caja(models.Model):
    """
    Representa un punto de venta físico o lógico.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cajas_creadas', null=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'

    def __str__(self):
        return self.nombre

class SesionCaja(models.Model):
    """
    Representa un turno o sesión de caja (Apertura y Cierre).
    """
    ESTADO_CHOICES = (
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
        ('ARQUEADA', 'Arqueada'), # Proceso de verificación final
    )

    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='sesiones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sesiones_caja')
    
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    monto_apertura = models.DecimalField(max_digits=14, decimal_places=2, help_text="Monto inicial en efectivo")
    
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_cierre_sistema = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Calculado por el sistema")
    monto_cierre_usuario = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Declarado por el cajero")
    diferencia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ABIERTA')
    observaciones = models.TextField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Sesión {self.id} - {self.caja} - {self.usuario}"

    def cerrar_sesion(self, monto_usuario):
        self.fecha_cierre = timezone.now()
        self.monto_cierre_usuario = monto_usuario
        self.diferencia = self.monto_cierre_usuario - self.monto_cierre_sistema
        self.estado = 'CERRADA'
        self.save()

class MovimientoCaja(models.Model):
    """
    Entradas y salidas de dinero de la caja (Ventas, Retiros, Depósitos, Gastos Menores).
    """
    TIPO_MOVIMIENTO_CHOICES = (
        ('VENTA', 'Venta (Cobro)'),
        ('INGRESO_MANUAL', 'Ingreso Manual'),
        ('RETIRO_MANUAL', 'Retiro Manual'),
        ('GASTO_MENOR', 'Gasto Menor'),
        ('APERTURA', 'Monto Apertura'),
        ('CIERRE', 'Retiro por Cierre'),
    )
    
    sesion = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="ID Factura, Recibo, etc.")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.monto}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar monto sistema en la sesión si es necesario
        # (Lógica simplificada, idealmente usar signals o métodos de servicio)

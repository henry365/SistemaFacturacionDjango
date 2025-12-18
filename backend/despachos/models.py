from django.db import models
from django.conf import settings
from clientes.models import Cliente
from ventas.models import Factura
from inventario.models import Almacen
from productos.models import Producto
import uuid


class Despacho(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('EN_PREPARACION', 'En Preparación'),
        ('PARCIAL', 'Parcial'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    )

    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='despachos', null=True, blank=True)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='despachos')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='despachos')
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_despacho = models.DateTimeField(null=True, blank=True, help_text="Fecha efectiva del despacho")
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='despachos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    # Información de entrega
    direccion_entrega = models.TextField(blank=True, null=True)
    transportista = models.CharField(max_length=200, blank=True, null=True)
    numero_guia = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    # Auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='despachos_creados', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='despachos_modificados', null=True, blank=True)
    usuario_despacho = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='despachos_realizados', null=True, blank=True)

    class Meta:
        verbose_name = 'Despacho'
        verbose_name_plural = 'Despachos'
        ordering = ['-fecha']

    def __str__(self):
        return f"Despacho {self.id} - Factura {self.factura.numero_factura}"


class DetalleDespacho(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cantidad en factura")
    cantidad_despachada = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Cantidad efectivamente despachada")
    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    # Mantener cantidad para compatibilidad
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Detalle de Despacho'
        verbose_name_plural = 'Detalles de Despachos'

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_despachada}/{self.cantidad_solicitada}"

    def save(self, *args, **kwargs):
        # Mantener cantidad sincronizada con cantidad_despachada
        self.cantidad = self.cantidad_despachada
        super().save(*args, **kwargs)

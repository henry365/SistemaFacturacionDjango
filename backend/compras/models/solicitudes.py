"""
Modelos para solicitudes de cotización a proveedores.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from proveedores.models import Proveedor
import uuid


class SolicitudCotizacionProveedor(models.Model):
    """Solicitud de cotización enviada a un proveedor."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADA', 'Enviada'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='solicitudes_cotizacion',
        null=True,
        blank=True,
        db_index=True
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_index=True)
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', db_index=True)
    detalles = models.TextField(help_text="Descripción de productos/servicios solicitados")

    # Campos de auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitudes_compra_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitudes_compra_modificadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Solicitud de Cotización'
        verbose_name_plural = 'Solicitudes de Cotización'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['-fecha_solicitud']),
        ]

    def clean(self):
        if self.proveedor and self.empresa and self.proveedor.empresa != self.empresa:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa.'})

        if self.detalles:
            self.detalles = self.detalles.strip()
            if not self.detalles:
                raise ValidationError({'detalles': 'Los detalles no pueden estar vacíos.'})

    @property
    def estado_display(self):
        return self.get_estado_display()

    def __str__(self):
        return f"Solicitud {self.proveedor.nombre} - {self.fecha_solicitud} ({self.get_estado_display()})"

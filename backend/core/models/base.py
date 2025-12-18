"""
Modelos abstractos base para el Sistema de Facturación.

Este módulo implementa el principio DRY (Don't Repeat Yourself) proporcionando
clases base que contienen campos y comportamientos comunes a múltiples modelos.

Jerarquía:
- AbstractBaseModel: uuid, fecha_creacion, fecha_actualizacion
- AbstractAuditModel: + usuario_creacion, usuario_modificacion
- AbstractMultitenantModel: + empresa (FK)
- AbstractDocumentoModel: + idempotency_key, estado
"""
import uuid
from django.db import models
from django.conf import settings


class AbstractBaseModel(models.Model):
    """
    Modelo base con campos de identificación y timestamps.

    Proporciona:
    - uuid: Identificador único universal para referencia externa/API
    - fecha_creacion: Timestamp de creación (auto)
    - fecha_actualizacion: Timestamp de última modificación (auto)
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='UUID'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name='Fecha de Actualización'
    )

    class Meta:
        abstract = True


class AbstractAuditModel(AbstractBaseModel):
    """
    Modelo base con campos de auditoría de usuario.

    Hereda de AbstractBaseModel y agrega:
    - usuario_creacion: Usuario que creó el registro
    - usuario_modificacion: Usuario que modificó por última vez
    """
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_creados',
        verbose_name='Creado por'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_modificados',
        verbose_name='Modificado por'
    )

    class Meta:
        abstract = True


class AbstractMultitenantModel(AbstractAuditModel):
    """
    Modelo base para entidades multi-tenant (por empresa).

    Hereda de AbstractAuditModel y agrega:
    - empresa: ForeignKey a la empresa propietaria del registro

    IMPORTANTE: Todos los modelos que pertenecen a una empresa deben
    heredar de esta clase para garantizar el filtrado por tenant.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s',
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Empresa'
    )

    class Meta:
        abstract = True


class AbstractDocumentoModel(AbstractMultitenantModel):
    """
    Modelo base para documentos transaccionales (facturas, compras, etc.).

    Hereda de AbstractMultitenantModel y agrega:
    - idempotency_key: Clave para operaciones idempotentes
    - Implementa la propiedad estado_display

    Subclases deben definir:
    - ESTADO_CHOICES: Tupla de opciones para el campo estado
    - estado: CharField con las opciones
    """
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Clave de Idempotencia',
        help_text='Clave única para evitar operaciones duplicadas'
    )

    class Meta:
        abstract = True

    @property
    def estado_display(self):
        """Retorna el valor legible del estado."""
        if hasattr(self, 'get_estado_display'):
            return self.get_estado_display()
        return getattr(self, 'estado', None)


class AbstractDetalleModel(models.Model):
    """
    Modelo base para líneas de detalle (DetalleFactura, DetalleCompra, etc.).

    Proporciona campos comunes para detalles de documentos:
    - cantidad
    - precio_unitario
    - descuento
    - impuesto
    """
    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Cantidad'
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio Unitario'
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Descuento'
    )
    impuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Impuesto'
    )

    class Meta:
        abstract = True

    @property
    def subtotal(self):
        """Calcula el subtotal antes de impuestos."""
        return (self.cantidad * self.precio_unitario) - self.descuento

    @property
    def total(self):
        """Calcula el total incluyendo impuestos."""
        return self.subtotal + self.impuesto

"""
Modelos para ajustes de inventario y conteos físicos.
"""
from django.db import models
from django.conf import settings
from productos.models import Producto
import uuid


class AjusteInventario(models.Model):
    """Ajuste de inventario por diversas razones."""

    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('PROCESADO', 'Procesado'),
    )

    TIPO_AJUSTE_CHOICES = (
        ('AJUSTE_INVENTARIO', 'Ajuste de Inventario'),
        ('AJUSTE_DIFERENCIA', 'Ajuste por Diferencia'),
        ('AJUSTE_DETERIORO', 'Ajuste por Deterioro'),
        ('AJUSTE_ROBO', 'Ajuste por Robo/Pérdida'),
        ('AJUSTE_DONACION', 'Ajuste por Donación'),
        ('AJUSTE_MUESTRA', 'Ajuste por Muestra'),
        ('AJUSTE_PRODUCCION', 'Ajuste por Producción'),
        ('AJUSTE_DESECHO', 'Ajuste por Desecho'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='ajustes_inventario',
        null=True,
        blank=True
    )
    almacen = models.ForeignKey('inventario.Almacen', on_delete=models.PROTECT, related_name='ajustes')
    tipo_ajuste = models.CharField(max_length=30, choices=TIPO_AJUSTE_CHOICES)
    motivo = models.TextField()
    fecha_ajuste = models.DateField()

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ajustes_solicitados'
    )
    usuario_aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ajustes_aprobados'
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    observaciones_aprobacion = models.TextField(blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ajustes_inventario_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ajustes_inventario_modificados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Ajuste de Inventario'
        verbose_name_plural = 'Ajustes de Inventario'
        ordering = ['-fecha_ajuste']

    def __str__(self):
        return f"Ajuste {self.id} - {self.tipo_ajuste} - {self.estado}"


class DetalleAjusteInventario(models.Model):
    """Detalle de productos en un ajuste de inventario."""

    ajuste = models.ForeignKey(AjusteInventario, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_nueva = models.DecimalField(max_digits=12, decimal_places=2)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, help_text="Calculado automáticamente")
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de Ajuste'
        verbose_name_plural = 'Detalles de Ajustes'

    def save(self, *args, **kwargs):
        self.diferencia = self.cantidad_nueva - self.cantidad_anterior
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ajuste.id} - {self.producto} - Diferencia: {self.diferencia}"


class ConteoFisico(models.Model):
    """Conteo físico de inventario."""

    ESTADO_CHOICES = (
        ('PLANIFICADO', 'Planificado'),
        ('EN_PROCESO', 'En Proceso'),
        ('FINALIZADO', 'Finalizado'),
        ('AJUSTADO', 'Ajustado'),
        ('CANCELADO', 'Cancelado'),
    )

    TIPO_CONTEO_CHOICES = (
        ('COMPLETO', 'Conteo Completo'),
        ('CICLICO', 'Conteo Cíclico'),
        ('SELECTIVO', 'Conteo Selectivo'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='conteos_fisicos',
        null=True,
        blank=True
    )
    almacen = models.ForeignKey('inventario.Almacen', on_delete=models.PROTECT, related_name='conteos')

    numero_conteo = models.CharField(max_length=50)
    fecha_conteo = models.DateField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PLANIFICADO')
    tipo_conteo = models.CharField(max_length=20, choices=TIPO_CONTEO_CHOICES, default='COMPLETO')

    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conteos_responsables'
    )
    observaciones = models.TextField(blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conteos_fisicos_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conteos_fisicos_modificados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Conteo Físico'
        verbose_name_plural = 'Conteos Físicos'
        ordering = ['-fecha_conteo']
        unique_together = ('empresa', 'numero_conteo')

    def __str__(self):
        return f"Conteo {self.numero_conteo} - {self.almacen} - {self.estado}"


class DetalleConteoFisico(models.Model):
    """Detalle de productos en un conteo físico."""

    conteo = models.ForeignKey(ConteoFisico, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    lote = models.ForeignKey('inventario.Lote', on_delete=models.SET_NULL, null=True, blank=True)

    cantidad_sistema = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cantidad según sistema")
    cantidad_fisica = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cantidad contada físicamente")
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, help_text="Diferencia (Físico - Sistema)")

    observaciones = models.TextField(blank=True, null=True)
    contado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Detalle de Conteo Físico'
        verbose_name_plural = 'Detalles de Conteos Físicos'

    def save(self, *args, **kwargs):
        self.diferencia = self.cantidad_fisica - self.cantidad_sistema
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.conteo.numero_conteo} - {self.producto} - Diferencia: {self.diferencia}"

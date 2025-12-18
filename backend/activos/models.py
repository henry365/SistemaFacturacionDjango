"""
Modelos para Activos Fijos

Django 6.0: Usa GeneratedField para depreciacion_acumulada
"""
from django.db import models
from django.db.models import F, GeneratedField
from django.conf import settings
from productos.models import Producto
from compras.models import Compra, DetalleCompra
import uuid


class TipoActivo(models.Model):
    """Categorias de activos fijos con su tasa de depreciacion"""
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='tipos_activo',
        db_index=True,
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    porcentaje_depreciacion_anual = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Porcentaje de depreciacion fiscal anual (ej. 25.00 para vehiculos)"
    )
    vida_util_anos = models.IntegerField(help_text="Vida util estimada en anos")
    activo = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = 'Tipo de Activo'
        verbose_name_plural = 'Tipos de Activo'
        unique_together = ('empresa', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class ActivoFijo(models.Model):
    """Registro de activos fijos de la empresa"""
    ESTADO_CHOICES = (
        ('ACTIVO', 'Activo / En Uso'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('DEPRECIADO', 'Totalmente Depreciado'),
        ('VENDIDO', 'Vendido'),
        ('DESINCORPORADO', 'Desincorporado / Danado'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='activos_fijos',
        db_index=True,
        null=True,
        blank=True
    )
    tipo_activo = models.ForeignKey(TipoActivo, on_delete=models.PROTECT, related_name='activos')

    # Origen
    producto_origen = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, help_text="Producto del catalogo base")
    compra_origen = models.ForeignKey(Compra, on_delete=models.SET_NULL, null=True, blank=True, related_name='activos_generados')
    detalle_compra_origen = models.OneToOneField(DetalleCompra, on_delete=models.SET_NULL, null=True, blank=True, related_name='activo_fijo_generado')

    # Identificacion
    codigo_interno = models.CharField(max_length=50, help_text="Codigo de etiqueta / Placa de inventario")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    serial = models.CharField(max_length=100, blank=True, null=True, help_text="Serial, VIN, Chasis, etc.")

    # Ubicacion y Responsable
    ubicacion_fisica = models.CharField(max_length=200, blank=True, null=True, help_text="Oficina, Planta, Almacen X")
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activos_asignados')

    # Valoracion
    fecha_adquisicion = models.DateField()
    valor_adquisicion = models.DecimalField(max_digits=14, decimal_places=2)
    valor_libro_actual = models.DecimalField(max_digits=14, decimal_places=2, help_text="Valor tras depreciacion acumulada")

    # Django 6.0: Depreciación acumulada calculada automáticamente
    depreciacion_acumulada = GeneratedField(
        expression=F('valor_adquisicion') - F('valor_libro_actual'),
        output_field=models.DecimalField(max_digits=14, decimal_places=2),
        db_persist=True,
        help_text="Depreciación acumulada (calculado automáticamente)"
    )

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO', db_index=True)
    especificaciones = models.JSONField(default=dict, blank=True, help_text="Detalles tecnicos adicionales (Color, Motor, Capacidad, etc.)")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activos_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activos_modificados'
    )

    class Meta:
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
        unique_together = ('empresa', 'codigo_interno')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.codigo_interno} - {self.nombre}"

    @property
    def porcentaje_depreciado(self):
        """Retorna el porcentaje de depreciacion"""
        if self.valor_adquisicion > 0:
            return round((self.depreciacion_acumulada / self.valor_adquisicion) * 100, 2)
        return 0

class Depreciacion(models.Model):
    """Registro de depreciacion periodica de activos fijos"""
    activo = models.ForeignKey(ActivoFijo, on_delete=models.CASCADE, related_name='depreciaciones')
    fecha = models.DateField(db_index=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    valor_libro_anterior = models.DecimalField(max_digits=14, decimal_places=2)
    valor_libro_nuevo = models.DecimalField(max_digits=14, decimal_places=2)
    observacion = models.CharField(max_length=255, blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='depreciaciones_creadas'
    )

    class Meta:
        verbose_name = 'Depreciacion'
        verbose_name_plural = 'Depreciaciones'
        ordering = ['-fecha']
        unique_together = ('activo', 'fecha')

    def __str__(self):
        return f"Depreciacion {self.activo.codigo_interno} - {self.fecha} ({self.monto})"

    def save(self, *args, **kwargs):
        """Actualiza el valor libro del activo al guardar"""
        super().save(*args, **kwargs)
        self.activo.valor_libro_actual = self.valor_libro_nuevo
        self.activo.save(update_fields=['valor_libro_actual', 'fecha_actualizacion'])

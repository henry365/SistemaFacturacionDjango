"""
Modelos para Activos Fijos

Django 6.0: Usa GeneratedField para depreciacion_acumulada
"""
from decimal import Decimal
from django.db import models, transaction
from django.db.models import F, GeneratedField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
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

    def clean(self):
        """Validaciones de negocio para TipoActivo"""
        errors = {}

        # Validar porcentaje de depreciacion entre 0 y 100
        if self.porcentaje_depreciacion_anual is not None:
            if self.porcentaje_depreciacion_anual < 0:
                errors['porcentaje_depreciacion_anual'] = 'El porcentaje no puede ser negativo'
            elif self.porcentaje_depreciacion_anual > 100:
                errors['porcentaje_depreciacion_anual'] = 'El porcentaje no puede ser mayor a 100'

        # Validar vida util positiva
        if self.vida_util_anos is not None and self.vida_util_anos <= 0:
            errors['vida_util_anos'] = 'La vida util debe ser mayor a 0'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
    fecha_adquisicion = models.DateField(db_index=True)
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
        blank=True,
        related_name='activos_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activos_modificados'
    )

    class Meta:
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
        unique_together = ('empresa', 'codigo_interno')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.codigo_interno} - {self.nombre}"

    def clean(self):
        """Validaciones de negocio para ActivoFijo"""
        errors = {}

        # Validar valores monetarios no negativos
        if self.valor_adquisicion is not None and self.valor_adquisicion < 0:
            errors['valor_adquisicion'] = 'El valor de adquisicion no puede ser negativo'

        if self.valor_libro_actual is not None and self.valor_libro_actual < 0:
            errors['valor_libro_actual'] = 'El valor libro no puede ser negativo'

        # Validar que valor_libro_actual <= valor_adquisicion
        if (self.valor_adquisicion is not None and
            self.valor_libro_actual is not None and
            self.valor_libro_actual > self.valor_adquisicion):
            errors['valor_libro_actual'] = 'El valor libro no puede ser mayor al valor de adquisicion'

        # Validar que fecha_adquisicion no sea futura
        if self.fecha_adquisicion is not None and self.fecha_adquisicion > timezone.now().date():
            errors['fecha_adquisicion'] = 'La fecha de adquisicion no puede ser futura'

        # Validar que tipo_activo pertenezca a la misma empresa
        if (self.empresa is not None and
            self.tipo_activo is not None and
            self.tipo_activo.empresa is not None and
            self.tipo_activo.empresa != self.empresa):
            errors['tipo_activo'] = 'El tipo de activo debe pertenecer a la misma empresa'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Solo ejecutar full_clean si no es update_fields
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)

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
        blank=True,
        related_name='depreciaciones_creadas'
    )

    class Meta:
        verbose_name = 'Depreciacion'
        verbose_name_plural = 'Depreciaciones'
        ordering = ['-fecha']
        unique_together = ('activo', 'fecha')
        indexes = [
            models.Index(fields=['activo', 'fecha'], name='activos_dep_activo_fecha_idx'),
        ]

    def __str__(self):
        return f"Depreciacion {self.activo.codigo_interno} - {self.fecha} ({self.monto})"

    def clean(self):
        """Validaciones de negocio para Depreciacion"""
        errors = {}

        # Validar que valor_libro_nuevo >= 0
        if self.valor_libro_nuevo is not None and self.valor_libro_nuevo < 0:
            errors['valor_libro_nuevo'] = 'El valor libro nuevo no puede ser negativo'

        # Validar que monto >= 0
        if self.monto is not None and self.monto < 0:
            errors['monto'] = 'El monto de depreciacion no puede ser negativo'

        # Validar consistencia: valor_libro_nuevo = valor_libro_anterior - monto
        if (self.valor_libro_nuevo is not None and
            self.valor_libro_anterior is not None and
            self.monto is not None):
            expected_nuevo = self.valor_libro_anterior - self.monto
            if abs(self.valor_libro_nuevo - expected_nuevo) > Decimal('0.01'):
                errors['valor_libro_nuevo'] = f'El valor libro nuevo debe ser {expected_nuevo} (anterior - monto)'

        # Validar que fecha >= fecha_adquisicion del activo
        if (self.activo_id is not None and
            self.fecha is not None and
            hasattr(self, 'activo') and
            self.activo.fecha_adquisicion is not None and
            self.fecha < self.activo.fecha_adquisicion):
            errors['fecha'] = 'La fecha de depreciacion no puede ser anterior a la fecha de adquisicion'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Actualiza el valor libro del activo al guardar con transaccion atomica"""
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.activo.valor_libro_actual = self.valor_libro_nuevo
            self.activo.save(update_fields=['valor_libro_actual', 'fecha_actualizacion'])

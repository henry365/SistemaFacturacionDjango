"""
Modelos para el módulo de Caja

Este módulo gestiona cajas físicas/lógicas, sesiones de caja y movimientos de efectivo.
Cumple con la Guía Inicial: multi-tenancy, auditoría, validaciones completas.
"""
import uuid as uuid_lib
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .constants import (
    ESTADO_CHOICES, ESTADO_DEFAULT, ESTADO_ABIERTA, ESTADO_CERRADA, ESTADO_ARQUEADA,
    TRANSICIONES_ESTADO,
    TIPO_MOVIMIENTO_CHOICES, TIPOS_INGRESO, TIPOS_EGRESO
)


class Caja(models.Model):
    """
    Representa un punto de venta físico o lógico.

    Cada caja pertenece a una empresa y puede tener múltiples sesiones.
    """
    # Campo de empresa (OBLIGATORIO para multi-tenancy)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='cajas',
        db_index=True,
        null=True,
        blank=True,
        help_text="Empresa a la que pertenece la caja"
    )

    # Campos de negocio
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    # Identificador único
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_modificadas'
    )

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['nombre']
        unique_together = [('empresa', 'nombre')]
        indexes = [
            models.Index(fields=['empresa', 'activa']),
            models.Index(fields=['empresa', 'nombre']),
        ]

    def __str__(self):
        return self.nombre

    def clean(self):
        """
        Validaciones de negocio para Caja.

        CRÍTICO: Este método es OBLIGATORIO y valida todas las reglas de negocio.
        """
        errors = {}

        # Validar nombre no vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = 'El nombre de la caja no puede estar vacío.'

        # Validar unicidad de nombre por empresa
        if self.nombre and self.empresa:
            qs = Caja.objects.filter(nombre=self.nombre, empresa=self.empresa)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = 'Ya existe una caja con este nombre para esta empresa.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRÍTICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'nombre']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        super().save(*args, **kwargs)

    def tiene_sesion_abierta(self):
        """Verifica si la caja tiene una sesión abierta."""
        return self.sesiones.filter(estado=ESTADO_ABIERTA).exists()

    def get_sesion_activa(self):
        """Retorna la sesión activa de la caja si existe."""
        return self.sesiones.filter(estado=ESTADO_ABIERTA).first()


class SesionCaja(models.Model):
    """
    Representa un turno o sesión de caja (Apertura y Cierre).

    Una sesión pertenece a una caja y registra el flujo de efectivo
    durante un período de tiempo específico.
    """
    # Campo de empresa (OBLIGATORIO para multi-tenancy)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='sesiones_caja',
        db_index=True,
        null=True,
        blank=True,
        help_text="Empresa a la que pertenece la sesión"
    )

    # Relaciones
    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name='sesiones'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sesiones_caja'
    )

    # Datos de apertura
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    monto_apertura = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Monto inicial en efectivo"
    )

    # Datos de cierre
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_cierre_sistema = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Calculado por el sistema"
    )
    monto_cierre_usuario = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Declarado por el cajero"
    )
    diferencia = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0')
    )

    # Estado y observaciones
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_DEFAULT,
        db_index=True
    )
    observaciones = models.TextField(blank=True, null=True)

    # Identificador único
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sesiones_caja_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sesiones_caja_modificadas'
    )

    class Meta:
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'
        ordering = ['-fecha_apertura']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['empresa', 'fecha_apertura']),
            models.Index(fields=['caja', 'estado']),
        ]

    def __str__(self):
        return f"Sesión {self.id} - {self.caja} - {self.usuario}"

    def clean(self):
        """
        Validaciones de negocio para SesionCaja.

        CRÍTICO: Estas validaciones garantizan la integridad de los datos.
        """
        errors = {}

        # ========== VALIDACIONES DE VALORES MONETARIOS ==========

        # Validar monto_apertura no negativo
        if self.monto_apertura is not None and self.monto_apertura < 0:
            errors['monto_apertura'] = 'El monto de apertura no puede ser negativo.'

        # Validar monto_cierre_usuario no negativo
        if self.monto_cierre_usuario is not None and self.monto_cierre_usuario < 0:
            errors['monto_cierre_usuario'] = 'El monto de cierre no puede ser negativo.'

        # ========== VALIDACIONES DE FECHAS ==========

        # Validar que fecha_cierre no sea anterior a fecha_apertura
        if (self.fecha_cierre is not None and
            self.fecha_apertura is not None and
            self.fecha_cierre < self.fecha_apertura):
            errors['fecha_cierre'] = 'La fecha de cierre no puede ser anterior a la fecha de apertura.'

        # ========== VALIDACIONES DE RELACIONES ==========

        # Validar que caja pertenezca a la misma empresa
        if (self.empresa is not None and
            self.caja is not None and
            hasattr(self.caja, 'empresa') and
            self.caja.empresa is not None):
            if self.caja.empresa != self.empresa:
                errors['caja'] = 'La caja debe pertenecer a la misma empresa.'

        # Validar que usuario pertenezca a la misma empresa
        if (self.empresa is not None and
            self.usuario is not None and
            hasattr(self.usuario, 'empresa') and
            self.usuario.empresa is not None):
            if self.usuario.empresa != self.empresa:
                errors['usuario'] = 'El usuario debe pertenecer a la misma empresa.'

        # ========== VALIDACIONES DE ESTADO ==========

        # Validar transiciones de estado
        if self.pk:
            try:
                estado_anterior = SesionCaja.objects.get(pk=self.pk).estado
                estados_permitidos = TRANSICIONES_ESTADO.get(estado_anterior, [])
                if (self.estado != estado_anterior and
                    self.estado not in estados_permitidos):
                    errors['estado'] = f'No se puede cambiar de {estado_anterior} a {self.estado}.'
            except SesionCaja.DoesNotExist:
                pass

        # Validar que sesión cerrada tenga fecha_cierre
        if self.estado in [ESTADO_CERRADA, ESTADO_ARQUEADA] and not self.fecha_cierre:
            errors['fecha_cierre'] = 'La sesión cerrada debe tener fecha de cierre.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRÍTICO: Siempre validar antes de guardar para garantizar integridad.
        """
        # Heredar empresa de la caja si no está definida
        if not self.empresa and self.caja and self.caja.empresa:
            self.empresa = self.caja.empresa

        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'caja', 'estado', 'monto_apertura']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        super().save(*args, **kwargs)


class MovimientoCaja(models.Model):
    """
    Entradas y salidas de dinero de la caja.

    Registra ventas, retiros, depósitos, gastos menores y otros movimientos
    de efectivo dentro de una sesión de caja.
    """
    # Campo de empresa (OBLIGATORIO para multi-tenancy)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='movimientos_caja',
        db_index=True,
        null=True,
        blank=True,
        help_text="Empresa a la que pertenece el movimiento"
    )

    # Relaciones
    sesion = models.ForeignKey(
        SesionCaja,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )

    # Datos del movimiento
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        db_index=True
    )
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID Factura, Recibo, etc."
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos_caja'
    )

    # Identificador único
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_caja_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_caja_modificados'
    )

    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'tipo_movimiento']),
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['sesion', 'tipo_movimiento']),
        ]

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.monto}"

    def clean(self):
        """
        Validaciones de negocio para MovimientoCaja.

        CRÍTICO: Estas validaciones garantizan la integridad de los datos.
        """
        errors = {}

        # ========== VALIDACIONES DE VALORES MONETARIOS ==========

        # Validar monto positivo
        if self.monto is not None and self.monto <= 0:
            errors['monto'] = 'El monto debe ser mayor a cero.'

        # ========== VALIDACIONES DE RELACIONES ==========

        # Validar que sesion pertenezca a la misma empresa
        if (self.empresa is not None and
            self.sesion is not None and
            hasattr(self.sesion, 'empresa') and
            self.sesion.empresa is not None):
            if self.sesion.empresa != self.empresa:
                errors['sesion'] = 'La sesión debe pertenecer a la misma empresa.'

        # Validar que sesion esté abierta (solo para creación)
        if self.sesion and not self.pk:
            if self.sesion.estado != ESTADO_ABIERTA:
                errors['sesion'] = 'No se pueden agregar movimientos a una sesión cerrada.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        CRÍTICO: Siempre validar antes de guardar para garantizar integridad.
        """
        # Heredar empresa de la sesion si no está definida
        if not self.empresa and self.sesion and self.sesion.empresa:
            self.empresa = self.sesion.empresa

        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'sesion', 'monto', 'tipo_movimiento']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        super().save(*args, **kwargs)

    @property
    def es_ingreso(self):
        """Indica si el movimiento es un ingreso."""
        return self.tipo_movimiento in TIPOS_INGRESO

    @property
    def es_egreso(self):
        """Indica si el movimiento es un egreso."""
        return self.tipo_movimiento in TIPOS_EGRESO

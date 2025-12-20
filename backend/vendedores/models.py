"""
Modelos para el módulo Vendedores

Este módulo contiene los modelos para gestión de vendedores,
sus datos de contacto, comisiones y relaciones con ventas.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid

from .constants import (
    COMISION_MIN,
    COMISION_MAX,
    ERROR_NOMBRE_VACIO,
    ERROR_COMISION_RANGO,
    ERROR_USUARIO_EMPRESA_DIFERENTE,
)


class Vendedor(models.Model):
    """
    Modelo para gestionar vendedores del sistema.

    Attributes:
        empresa: Empresa a la que pertenece el vendedor (multi-tenancy)
        uuid: Identificador único universal
        nombre: Nombre completo del vendedor
        cedula: Número de cédula (único por empresa)
        telefono: Teléfono de contacto
        correo: Correo electrónico
        comision_porcentaje: Porcentaje de comisión por ventas (0-100)
        usuario: Usuario del sistema asociado (opcional)
        activo: Si el vendedor está activo
    """
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='vendedores', null=True, blank=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nombre = models.CharField(max_length=200)
    cedula = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    comision_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión por ventas (0-100)"
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vendedor_perfil',
        db_index=True,
        help_text="Usuario del sistema asociado a este vendedor (opcional)"
    )
    activo = models.BooleanField(default=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vendedores_creados', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vendedores_modificados', null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['nombre']
        unique_together = ('empresa', 'cedula')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'cedula']),
            models.Index(fields=['empresa', '-fecha_creacion']),
            models.Index(fields=['empresa', 'usuario']),
        ]
        permissions = [
            ('gestionar_vendedor', 'Puede gestionar vendedores'),
        ]

    def clean(self):
        """
        Validaciones a nivel de modelo.

        Valida:
        - Nombre no vacío
        - Comisión entre 0 y 100
        - Normalización de correo
        - Usuario pertenece a la misma empresa
        """
        # Normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': ERROR_NOMBRE_VACIO})

        # Validar rango de comisión
        if self.comision_porcentaje < COMISION_MIN or self.comision_porcentaje > COMISION_MAX:
            raise ValidationError({'comision_porcentaje': ERROR_COMISION_RANGO})

        # Normalizar correo
        if self.correo:
            self.correo = self.correo.strip().lower()

        # Normalizar teléfono
        if self.telefono:
            self.telefono = self.telefono.strip()

        # Validar que usuario pertenezca a la misma empresa si ambos están asignados
        if self.usuario and self.empresa and hasattr(self.usuario, 'empresa') and self.usuario.empresa != self.empresa:
            raise ValidationError({'usuario': ERROR_USUARIO_EMPRESA_DIFERENTE})

    def save(self, *args, **kwargs):
        """
        Guarda el vendedor con validaciones.

        Ejecuta full_clean() antes de guardar para asegurar
        que todas las validaciones del modelo se cumplan.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'nombre', 'cedula', 'comision_porcentaje',
            'telefono', 'correo', 'usuario', 'empresa', 'activo'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"

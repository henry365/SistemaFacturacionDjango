"""
Modelos para el módulo Proveedores

Este módulo contiene el modelo para gestión de proveedores con
soporte para multi-tenancy y campos de auditoría.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid
import re

from .constants import (
    TIPO_IDENTIFICACION_CHOICES,
    TIPO_IDENTIFICACION_RNC,
    TIPO_CONTRIBUYENTE_CHOICES,
    TIPO_CONTRIBUYENTE_JURIDICA,
    ERROR_NOMBRE_VACIO,
    ERROR_RNC_REQUERIDO,
    ERROR_NUMERO_IDENTIFICACION_DUPLICADO,
    ERROR_RNC_FORMATO,
    REGEX_RNC,
    REGEX_TELEFONO,
    ERROR_TELEFONO_INVALIDO,
)


class Proveedor(models.Model):
    """
    Modelo principal de proveedores.

    Define proveedores con sus datos de contacto, identificación fiscal
    y tipo de contribuyente para cumplimiento DGII.
    Cada empresa tiene su propio catálogo de proveedores (multi-tenant).
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='proveedores',
        null=True,
        blank=True,
        db_index=True,
        help_text="Empresa propietaria del proveedor"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    nombre = models.CharField(max_length=200)
    tipo_identificacion = models.CharField(
        max_length=20,
        choices=TIPO_IDENTIFICACION_CHOICES,
        blank=True,
        null=True,
        db_index=True
    )
    numero_identificacion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True
    )

    tipo_contribuyente = models.CharField(
        max_length=20,
        choices=TIPO_CONTRIBUYENTE_CHOICES,
        default=TIPO_CONTRIBUYENTE_JURIDICA,
        db_index=True,
        help_text="Determina las reglas de retención (DGII)"
    )

    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    es_internacional = models.BooleanField(default=False)
    activo = models.BooleanField(default=True, db_index=True)

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='proveedores_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='proveedores_modificados',
        null=True,
        blank=True
    )
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
        unique_together = ('empresa', 'numero_identificacion')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'tipo_identificacion', 'numero_identificacion']),
            models.Index(fields=['empresa', 'tipo_contribuyente', 'activo']),
            models.Index(fields=['empresa', '-fecha_creacion']),
        ]
        permissions = [
            ('gestionar_proveedor', 'Puede gestionar proveedores'),
        ]

    def clean(self):
        """
        Validaciones de negocio para Proveedor.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # Validar y normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar que RNC requiere numero_identificacion
        if self.tipo_identificacion == TIPO_IDENTIFICACION_RNC and not self.numero_identificacion:
            errors['numero_identificacion'] = ERROR_RNC_REQUERIDO

        # Validar formato de RNC si es RNC
        if (self.tipo_identificacion == TIPO_IDENTIFICACION_RNC and
                self.numero_identificacion and
                not errors.get('numero_identificacion')):
            # Limpiar espacios y guiones del RNC para validación
            rnc_limpio = re.sub(r'[\s\-]', '', self.numero_identificacion)
            if not re.match(REGEX_RNC, rnc_limpio):
                errors['numero_identificacion'] = ERROR_RNC_FORMATO

        # Validar unicidad de numero_identificacion por empresa
        if self.numero_identificacion and self.empresa_id and not errors.get('numero_identificacion'):
            qs = Proveedor.objects.filter(
                empresa=self.empresa,
                numero_identificacion=self.numero_identificacion
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['numero_identificacion'] = ERROR_NUMERO_IDENTIFICACION_DUPLICADO

        # Validar formato de teléfono
        if self.telefono and not re.match(REGEX_TELEFONO, self.telefono):
            errors['telefono'] = ERROR_TELEFONO_INVALIDO

        # Normalizar correo
        if self.correo_electronico:
            self.correo_electronico = self.correo_electronico.strip().lower()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'nombre', 'numero_identificacion', 'tipo_identificacion',
            'tipo_contribuyente', 'telefono', 'correo_electronico',
            'activo', 'empresa'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    @property
    def tipo_identificacion_display(self):
        """Obtener el display del tipo de identificación"""
        return self.get_tipo_identificacion_display() if self.tipo_identificacion else None

    @property
    def tipo_contribuyente_display(self):
        """Obtener el display del tipo de contribuyente"""
        return self.get_tipo_contribuyente_display()

    def __str__(self):
        identificacion = f" ({self.numero_identificacion})" if self.numero_identificacion else ""
        return f"{self.nombre}{identificacion}"

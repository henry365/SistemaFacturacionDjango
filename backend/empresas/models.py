"""
Modelos para el módulo Empresas

Empresa es el modelo raíz del sistema multi-tenant.
NO tiene campo 'empresa' porque ES el modelo base.
"""
import re
import uuid
from django.db import models
from django.core.exceptions import ValidationError

from .constants import (
    LONGITUD_RNC_MIN, LONGITUD_RNC_MAX,
    LONGITUD_TELEFONO_MIN, LONGITUD_TELEFONO_MAX,
    ERROR_NOMBRE_VACIO, ERROR_RNC_VACIO, ERROR_RNC_FORMATO,
    ERROR_RNC_LONGITUD, ERROR_RNC_DUPLICADO,
    ERROR_TELEFONO_FORMATO, ERROR_TELEFONO_LONGITUD,
    ERROR_CONFIGURACION_FISCAL_INVALIDA
)


class Empresa(models.Model):
    """
    Modelo raíz del sistema multi-tenant.

    Representa una empresa/organización que usa el sistema.
    Todos los demás modelos tienen un campo 'empresa' que referencia a este modelo.
    """
    nombre = models.CharField(max_length=200)
    rnc = models.CharField(max_length=50, unique=True, db_index=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    configuracion_fiscal = models.JSONField(
        default=dict,
        blank=True,
        help_text="Secuencias de NCF y otras configuraciones fiscales"
    )
    activo = models.BooleanField(default=True, db_index=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['activo', 'nombre']),
            models.Index(fields=['-fecha_creacion']),
        ]
        permissions = [
            ('gestionar_empresa', 'Puede gestionar empresas'),
            ('actualizar_configuracion_fiscal', 'Puede actualizar configuración fiscal'),
            ('ver_estadisticas', 'Puede ver estadísticas de empresa'),
        ]

    def clean(self):
        """
        Validaciones de negocio para Empresa.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # ========== VALIDACIONES DE VALORES ==========

        # Validar nombre no vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar RNC no vacío
        if self.rnc:
            self.rnc = self.rnc.strip()
            if not self.rnc:
                errors['rnc'] = ERROR_RNC_VACIO
        else:
            errors['rnc'] = ERROR_RNC_VACIO

        # ========== VALIDACIONES DE FORMATO ==========

        # Validar formato de RNC
        if self.rnc and 'rnc' not in errors:
            # RNC puede tener formato: 123456789 o 123-45678-9
            if not re.match(r'^[\d-]+$', self.rnc):
                errors['rnc'] = ERROR_RNC_FORMATO
            else:
                rnc_sin_guiones = self.rnc.replace('-', '').replace(' ', '')
                if len(rnc_sin_guiones) < LONGITUD_RNC_MIN or len(rnc_sin_guiones) > LONGITUD_RNC_MAX:
                    errors['rnc'] = ERROR_RNC_LONGITUD

        # Validar formato de teléfono
        if self.telefono:
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', self.telefono)
            if not telefono_sin_formato.isdigit():
                errors['telefono'] = ERROR_TELEFONO_FORMATO
            elif len(telefono_sin_formato) < LONGITUD_TELEFONO_MIN or len(telefono_sin_formato) > LONGITUD_TELEFONO_MAX:
                errors['telefono'] = ERROR_TELEFONO_LONGITUD

        # ========== VALIDACIONES DE UNICIDAD ==========

        # Validar unicidad de RNC
        if self.rnc and 'rnc' not in errors:
            qs = type(self).objects.filter(rnc=self.rnc)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['rnc'] = ERROR_RNC_DUPLICADO

        # ========== VALIDACIONES DE CONSISTENCIA ==========

        # Validar que configuracion_fiscal sea dict válido
        if self.configuracion_fiscal and not isinstance(self.configuracion_fiscal, dict):
            errors['configuracion_fiscal'] = ERROR_CONFIGURACION_FISCAL_INVALIDA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['nombre', 'rnc', 'activo', 'telefono', 'configuracion_fiscal']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

import re
import uuid as uuid_lib
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from .constants import ROL_CHOICES, ROL_DEFAULT, ROL_ADMIN


class User(AbstractUser):
    """
    Modelo de usuario personalizado.

    Incluye campos adicionales para roles, empresa y auditoría.
    """
    # Identificador único
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    # Campos de negocio
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=ROL_DEFAULT, db_index=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='usuarios',
        null=True,
        blank=True,
        db_index=True,
        help_text="Empresa a la que pertenece el usuario"
    )

    # Campos de auditoría adicionales (date_joined y last_login vienen de AbstractUser)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_modificados'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']
        indexes = [
            models.Index(fields=['empresa', 'rol']),
            models.Index(fields=['is_active', 'rol']),
        ]

    def clean(self):
        """
        Validaciones de negocio para User.

        Valida:
        - Username no vacío
        - Email normalizado y único por empresa
        - Teléfono con formato válido
        """
        errors = {}

        # Validar username
        if self.username:
            self.username = self.username.strip()
            if not self.username:
                errors['username'] = 'El nombre de usuario no puede estar vacío.'

        # Validar y normalizar email
        if self.email:
            self.email = self.email.strip().lower()
            # Validar unicidad de email por empresa
            if self.empresa:
                qs = User.objects.filter(email=self.email, empresa=self.empresa)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                if qs.exists():
                    errors['email'] = 'Ya existe un usuario con este correo en la empresa.'

        # Validar teléfono
        if self.telefono:
            self.telefono = self.telefono.strip()
            if not re.match(r'^[\d\s\-\(\)\+]+$', self.telefono):
                errors['telefono'] = 'El teléfono contiene caracteres inválidos.'
            telefono_sin_formato = re.sub(r'[\s\-\(\)\+]', '', self.telefono)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                errors['telefono'] = 'El teléfono debe tener entre 10 y 15 dígitos.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.

        Maneja update_fields para evitar validaciones innecesarias en updates parciales.
        """
        # Ejecutar validaciones completas antes de guardar
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            # Incluso con update_fields, validar si se modifican campos críticos
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'rol', 'email', 'username']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        # Lógica de negocio: asignar is_staff si es admin
        if self.rol == ROL_ADMIN:
            self.is_staff = True

        super().save(*args, **kwargs)

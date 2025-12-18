from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class User(AbstractUser):
    """
    Modelo de usuario personalizado.
    Se pueden agregar campos adicionales aquí si es necesario.
    """
    ROLES = (
        ('admin', 'Administrador'),
        ('facturador', 'Facturador'),
        ('cajero', 'Cajero'),
        ('almacen', 'Almacén'),
        ('compras', 'Compras'),
        ('contabilidad', 'Contabilidad'),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES, default='facturador', db_index=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='usuarios', null=True, blank=True, db_index=True, help_text="Empresa a la que pertenece el usuario")
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']
        indexes = [
            models.Index(fields=['empresa', 'rol']),
            models.Index(fields=['is_active', 'rol']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.username:
            self.username = self.username.strip()
            if not self.username:
                raise ValidationError({'username': 'El nombre de usuario no puede estar vacío.'})
        
        if self.email:
            self.email = self.email.strip().lower()
        
        if self.telefono:
            self.telefono = self.telefono.strip()

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

    def save(self, *args, **kwargs):
        self.full_clean()  # Llamar a clean() antes de guardar
        if self.rol == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def asignar_grupo_por_rol(sender, instance, created, **kwargs):
    """
    Asigna automáticamente el usuario al grupo correspondiente a su rol.
    Si el grupo no existe, intenta crearlo (aunque deberían crearse con setup_roles).
    """
    if instance.rol:
        group_name = instance.rol # El nombre del grupo será igual al código del rol (admin, facturador, etc)
        group, _ = Group.objects.get_or_create(name=group_name)
        
        # Limpiar grupos anteriores si cambió de rol (opcional, depende de la lógica de negocio)
        # Aquí asumimos que el rol define su grupo principal.
        current_groups = instance.groups.all()
        if group not in current_groups:
            instance.groups.add(group)

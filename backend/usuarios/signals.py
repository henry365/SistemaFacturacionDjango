"""
Señales de Django para el módulo de Usuarios

Estas señales automatizan comportamientos del sistema:
- Asignación automática de grupo por rol
- Logging de cambios importantes
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


@receiver(post_save, sender='usuarios.User')
def asignar_grupo_por_rol(sender, instance, created, **kwargs):
    """
    Asigna automáticamente el usuario al grupo correspondiente a su rol.

    Si el grupo no existe, intenta crearlo (aunque deberían crearse con setup_roles).
    """
    if instance.rol:
        group_name = instance.rol
        group, group_created = Group.objects.get_or_create(name=group_name)

        if group_created:
            logger.info(f"Grupo '{group_name}' creado automáticamente")

        # Verificar si el usuario ya pertenece al grupo
        current_groups = instance.groups.all()
        if group not in current_groups:
            instance.groups.add(group)
            logger.info(
                f"Usuario {instance.username} asignado al grupo '{group_name}'"
            )


@receiver(post_save, sender='usuarios.User')
def log_usuario_creado(sender, instance, created, **kwargs):
    """
    Registra la creación de nuevos usuarios.
    """
    if created:
        empresa_nombre = instance.empresa.nombre if instance.empresa else 'Sin empresa'
        logger.info(
            f"Nuevo usuario creado: {instance.username}, "
            f"Rol: {instance.rol}, Empresa: {empresa_nombre}"
        )

"""
Señales de Django para el módulo de Clientes

Este módulo contiene las señales (signals) para automatizar comportamientos
del sistema, como logging de eventos y normalización de datos.
"""
import logging
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from .models import Cliente, CategoriaCliente

logger = logging.getLogger(__name__)


# ============================================================
# SEÑALES DE CLIENTE
# ============================================================

@receiver(pre_save, sender=Cliente)
def cliente_pre_save(sender, instance, **kwargs):
    """
    Señal pre-save para Cliente.

    Acciones:
    - Normaliza correo electrónico (minúsculas, sin espacios)
    - Normaliza teléfono (sin espacios extras)
    - Normaliza nombre (sin espacios extras)
    """
    # Normalizar correo electrónico
    if instance.correo_electronico:
        instance.correo_electronico = instance.correo_electronico.strip().lower()

    # Normalizar teléfono
    if instance.telefono:
        instance.telefono = instance.telefono.strip()

    # Normalizar nombre
    if instance.nombre:
        instance.nombre = instance.nombre.strip()


@receiver(post_save, sender=Cliente)
def cliente_post_save(sender, instance, created, **kwargs):
    """
    Señal post-save para Cliente.

    Acciones:
    - Log de creación de nuevos clientes
    - Log de actualizaciones importantes
    """
    if created:
        logger.info(
            f"Nuevo cliente creado: {instance.nombre} "
            f"({instance.numero_identificacion or 'Sin ID'}) - "
            f"Empresa: {instance.empresa.nombre if instance.empresa else 'Sin empresa'}"
        )
    else:
        logger.debug(f"Cliente actualizado: {instance.id} - {instance.nombre}")


@receiver(pre_delete, sender=Cliente)
def cliente_pre_delete(sender, instance, **kwargs):
    """
    Señal pre-delete para Cliente.

    Acciones:
    - Log de eliminación de clientes
    - Validaciones antes de eliminar (si es necesario)
    """
    logger.warning(
        f"Cliente a eliminar: {instance.id} - {instance.nombre} "
        f"({instance.numero_identificacion or 'Sin ID'})"
    )


# ============================================================
# SEÑALES DE CATEGORÍA DE CLIENTE
# ============================================================

@receiver(pre_save, sender=CategoriaCliente)
def categoria_cliente_pre_save(sender, instance, **kwargs):
    """
    Señal pre-save para CategoriaCliente.

    Acciones:
    - Normaliza nombre (sin espacios extras)
    """
    if instance.nombre:
        instance.nombre = instance.nombre.strip()


@receiver(post_save, sender=CategoriaCliente)
def categoria_cliente_post_save(sender, instance, created, **kwargs):
    """
    Señal post-save para CategoriaCliente.

    Acciones:
    - Log de creación de nuevas categorías
    - Log de cambios en descuento
    """
    if created:
        logger.info(
            f"Nueva categoría de cliente creada: {instance.nombre} - "
            f"Descuento: {instance.descuento_porcentaje}% - "
            f"Empresa: {instance.empresa.nombre if instance.empresa else 'Sin empresa'}"
        )
    else:
        logger.debug(
            f"Categoría actualizada: {instance.id} - {instance.nombre} - "
            f"Descuento: {instance.descuento_porcentaje}%"
        )


@receiver(pre_delete, sender=CategoriaCliente)
def categoria_cliente_pre_delete(sender, instance, **kwargs):
    """
    Señal pre-delete para CategoriaCliente.

    Acciones:
    - Log de eliminación de categorías
    - Verificar si hay clientes asociados
    """
    clientes_count = instance.clientes.count()
    if clientes_count > 0:
        logger.warning(
            f"Categoría a eliminar tiene {clientes_count} clientes asociados: "
            f"{instance.id} - {instance.nombre}"
        )
    else:
        logger.info(
            f"Categoría a eliminar (sin clientes): {instance.id} - {instance.nombre}"
        )

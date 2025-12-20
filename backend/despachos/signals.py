"""
Señales para el módulo de Despachos

Maneja eventos post-save para sincronización y auditoría.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Despacho, DetalleDespacho
from .constants import ESTADO_COMPLETADO, ESTADO_CANCELADO

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Despacho)
def despacho_pre_save(sender, instance, **kwargs):
    """
    Pre-save para Despacho.
    Registra cambios de estado para auditoría.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.estado != instance.estado:
                logger.info(
                    f"Despacho {instance.pk} cambio de estado: "
                    f"{old_instance.estado} -> {instance.estado}"
                )
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Despacho)
def despacho_post_save(sender, instance, created, **kwargs):
    """
    Post-save para Despacho.
    """
    if created:
        logger.info(
            f"Despacho {instance.pk} creado para factura "
            f"{instance.factura_id} por usuario {instance.usuario_creacion_id}"
        )

    # Notificar cuando se completa o cancela
    if instance.estado == ESTADO_COMPLETADO:
        logger.info(f"Despacho {instance.pk} completado")
        # Aquí se podría integrar con sistema de notificaciones
    elif instance.estado == ESTADO_CANCELADO:
        logger.info(f"Despacho {instance.pk} cancelado")


@receiver(post_save, sender=DetalleDespacho)
def detalle_despacho_post_save(sender, instance, created, **kwargs):
    """
    Post-save para DetalleDespacho.
    """
    if created:
        logger.debug(
            f"DetalleDespacho creado: Despacho {instance.despacho_id}, "
            f"Producto {instance.producto_id}, "
            f"Cantidad solicitada: {instance.cantidad_solicitada}"
        )

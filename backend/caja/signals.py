"""
Signals para el módulo de Caja

Este módulo define los signals de Django para eventos del módulo de Caja.
Los signals se registran en apps.py mediante el método ready().
"""
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import SesionCaja, MovimientoCaja
from .constants import ESTADO_CERRADA, TIPOS_NO_ELIMINABLES

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SesionCaja)
def log_sesion_estado_change(sender, instance, created, **kwargs):
    """
    Log cuando se crea o cambia el estado de una sesión.

    Args:
        sender: Modelo que envía la señal
        instance: Instancia de SesionCaja
        created: True si es un nuevo registro
    """
    if created:
        logger.info(
            f"Nueva sesión de caja creada: ID={instance.id}, "
            f"Caja={instance.caja.nombre}, Usuario={instance.usuario.username}, "
            f"Monto apertura={instance.monto_apertura}"
        )
    elif instance.estado == ESTADO_CERRADA:
        logger.info(
            f"Sesión de caja cerrada: ID={instance.id}, "
            f"Caja={instance.caja.nombre}, "
            f"Monto sistema={instance.monto_cierre_sistema}, "
            f"Monto usuario={instance.monto_cierre_usuario}, "
            f"Diferencia={instance.diferencia}"
        )


@receiver(post_save, sender=MovimientoCaja)
def log_movimiento_created(sender, instance, created, **kwargs):
    """
    Log cuando se registra un nuevo movimiento.

    Args:
        sender: Modelo que envía la señal
        instance: Instancia de MovimientoCaja
        created: True si es un nuevo registro
    """
    if created:
        logger.debug(
            f"Movimiento de caja registrado: ID={instance.id}, "
            f"Tipo={instance.tipo_movimiento}, Monto={instance.monto}, "
            f"Sesión={instance.sesion.id}, Usuario={instance.usuario.username}"
        )


@receiver(pre_delete, sender=MovimientoCaja)
def prevent_delete_protected_movements(sender, instance, **kwargs):
    """
    Previene la eliminación de movimientos protegidos (apertura).

    Args:
        sender: Modelo que envía la señal
        instance: Instancia de MovimientoCaja

    Raises:
        ProtectedError: Si se intenta eliminar un movimiento de apertura
    """
    from django.db.models import ProtectedError

    if instance.tipo_movimiento in TIPOS_NO_ELIMINABLES:
        raise ProtectedError(
            f"No se puede eliminar un movimiento de tipo {instance.tipo_movimiento}",
            [instance]
        )

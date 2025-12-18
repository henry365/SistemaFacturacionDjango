"""
Señales de Django para el módulo de Activos Fijos

Estas señales automatizan comportamientos del sistema:
- Actualización automática de estado cuando valor_libro llega a 0
- Notificaciones de activos próximos a depreciarse completamente
- Logging de cambios importantes
"""
import logging
from decimal import Decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import ActivoFijo, Depreciacion
from .constants import ESTADO_DEPRECIADO, ESTADOS_DEPRECIABLES

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ActivoFijo)
def activo_pre_save(sender, instance, **kwargs):
    """
    Señal pre-save para ActivoFijo.
    - Actualiza automáticamente el estado a DEPRECIADO si valor_libro <= 0
    """
    # Solo actuar si es un update (tiene pk)
    if instance.pk:
        # Auto-actualizar estado si valor_libro llega a 0
        if (instance.valor_libro_actual <= 0 and
            instance.estado in ESTADOS_DEPRECIABLES):
            instance.estado = ESTADO_DEPRECIADO
            logger.info(
                f"Activo {instance.codigo_interno} marcado como DEPRECIADO "
                f"automáticamente (valor_libro = {instance.valor_libro_actual})"
            )


@receiver(post_save, sender=ActivoFijo)
def activo_post_save(sender, instance, created, **kwargs):
    """
    Señal post-save para ActivoFijo.
    - Log de creación de nuevos activos
    - Alerta si activo creado con valor_libro bajo
    """
    if created:
        logger.info(
            f"Nuevo activo creado: {instance.codigo_interno} - {instance.nombre}, "
            f"Valor: {instance.valor_adquisicion}"
        )

        # Alerta si se crea con valor_libro muy bajo (menos del 10%)
        if instance.valor_libro_actual < (instance.valor_adquisicion * Decimal('0.1')):
            logger.warning(
                f"Activo {instance.codigo_interno} creado con valor libro muy bajo: "
                f"{instance.valor_libro_actual} de {instance.valor_adquisicion}"
            )


@receiver(post_save, sender=Depreciacion)
def depreciacion_post_save(sender, instance, created, **kwargs):
    """
    Señal post-save para Depreciacion.
    - Log de nuevas depreciaciones
    - Alerta cuando activo está próximo a depreciarse completamente
    """
    if created:
        activo = instance.activo
        porcentaje_restante = 0

        if activo.valor_adquisicion > 0:
            porcentaje_restante = (
                instance.valor_libro_nuevo / activo.valor_adquisicion
            ) * 100

        logger.info(
            f"Depreciación registrada para {activo.codigo_interno}: "
            f"Monto {instance.monto}, Valor libro nuevo: {instance.valor_libro_nuevo}"
        )

        # Alerta si queda menos del 10% del valor
        if 0 < porcentaje_restante < 10:
            logger.warning(
                f"Activo {activo.codigo_interno} próximo a depreciarse completamente: "
                f"Queda {porcentaje_restante:.1f}% del valor original"
            )

        # Alerta si está totalmente depreciado
        if instance.valor_libro_nuevo <= 0:
            logger.info(
                f"Activo {activo.codigo_interno} totalmente depreciado"
            )

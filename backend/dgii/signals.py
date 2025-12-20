"""
Señales para el módulo DGII

Maneja eventos para auditoría y alertas de secuencias.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import TipoComprobante, SecuenciaNCF

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TipoComprobante)
def tipo_comprobante_post_save(sender, instance, created, **kwargs):
    """
    Post-save para TipoComprobante.
    """
    if created:
        logger.info(
            f"TipoComprobante creado: {instance.codigo} - {instance.nombre} "
            f"(empresa_id={instance.empresa_id})"
        )


@receiver(pre_save, sender=SecuenciaNCF)
def secuencia_ncf_pre_save(sender, instance, **kwargs):
    """
    Pre-save para SecuenciaNCF.
    Registra cuando una secuencia está por agotarse.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # Detectar cuando se usa un NCF
            if old_instance.secuencia_actual != instance.secuencia_actual:
                disponibles = instance.secuencia_final - instance.secuencia_actual
                if disponibles <= instance.alerta_cantidad:
                    logger.warning(
                        f"ALERTA: Secuencia NCF {instance.pk} ({instance.tipo_comprobante}) "
                        f"tiene solo {disponibles} NCF disponibles"
                    )
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=SecuenciaNCF)
def secuencia_ncf_post_save(sender, instance, created, **kwargs):
    """
    Post-save para SecuenciaNCF.
    """
    if created:
        logger.info(
            f"SecuenciaNCF creada: {instance.tipo_comprobante} "
            f"({instance.secuencia_inicial}-{instance.secuencia_final}) "
            f"(empresa_id={instance.empresa_id})"
        )

    # Verificar si la secuencia se agotó
    if instance.agotada:
        logger.warning(
            f"ALERTA: Secuencia NCF {instance.pk} ({instance.tipo_comprobante}) "
            f"está AGOTADA"
        )

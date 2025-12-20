"""
Signals de Django para el módulo Cuentas por Cobrar

Este módulo define las señales para automatizar comportamientos
del sistema de cuentas por cobrar, incluyendo logging y normalización.
"""
import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente

logger = logging.getLogger(__name__)


# ============================================================
# SIGNALS DE CUENTA POR COBRAR
# ============================================================

@receiver(pre_save, sender=CuentaPorCobrar)
def cuenta_por_cobrar_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para CuentaPorCobrar.
    - Normaliza número de documento
    """
    if instance.numero_documento:
        instance.numero_documento = instance.numero_documento.strip().upper()


@receiver(post_save, sender=CuentaPorCobrar)
def cuenta_por_cobrar_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para CuentaPorCobrar.
    - Log de creación de nuevas cuentas por cobrar
    """
    if created:
        logger.info(
            f"Nueva cuenta por cobrar registrada: {instance.numero_documento} - "
            f"Cliente: {instance.cliente.nombre} - Monto: {instance.monto_original}"
        )


@receiver(pre_delete, sender=CuentaPorCobrar)
def cuenta_por_cobrar_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para CuentaPorCobrar.
    - Advertencia de eliminación
    """
    logger.warning(
        f"Eliminando cuenta por cobrar: {instance.numero_documento} - "
        f"Cliente: {instance.cliente.nombre}"
    )


# ============================================================
# SIGNALS DE COBRO CLIENTE
# ============================================================

@receiver(pre_save, sender=CobroCliente)
def cobro_cliente_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para CobroCliente.
    - Normaliza número de recibo y referencia
    """
    if instance.numero_recibo:
        instance.numero_recibo = instance.numero_recibo.strip().upper()
    if instance.referencia:
        instance.referencia = instance.referencia.strip()


@receiver(post_save, sender=CobroCliente)
def cobro_cliente_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para CobroCliente.
    - Log de creación de nuevos cobros
    """
    if created:
        logger.info(
            f"Nuevo cobro registrado: {instance.numero_recibo} - "
            f"Cliente: {instance.cliente.nombre} - Monto: {instance.monto} - "
            f"Método: {instance.metodo_pago}"
        )


@receiver(pre_delete, sender=CobroCliente)
def cobro_cliente_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para CobroCliente.
    - Advertencia de eliminación
    """
    logger.warning(
        f"Eliminando cobro: {instance.numero_recibo} - "
        f"Cliente: {instance.cliente.nombre}"
    )


# ============================================================
# SIGNALS DE DETALLE COBRO CLIENTE
# ============================================================

@receiver(post_save, sender=DetalleCobroCliente)
def detalle_cobro_cliente_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para DetalleCobroCliente.
    - Log de aplicación de cobros a cuentas por cobrar
    """
    if created:
        logger.info(
            f"Cobro {instance.cobro.numero_recibo} aplicado a "
            f"CxC {instance.cuenta_por_cobrar.numero_documento} - "
            f"Monto: {instance.monto_aplicado}"
        )


@receiver(pre_delete, sender=DetalleCobroCliente)
def detalle_cobro_cliente_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para DetalleCobroCliente.
    - Advertencia de eliminación (posible reversión de cobro)
    """
    logger.warning(
        f"Eliminando aplicación de cobro: {instance.cobro.numero_recibo} -> "
        f"CxC {instance.cuenta_por_cobrar.numero_documento} - "
        f"Monto: {instance.monto_aplicado}"
    )

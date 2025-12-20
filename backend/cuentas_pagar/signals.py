"""
Signals de Django para el módulo Cuentas por Pagar

Este módulo define las señales para automatizar comportamientos
del sistema de cuentas por pagar, incluyendo logging y normalización.
"""
import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor

logger = logging.getLogger(__name__)


# ============================================================
# SIGNALS DE CUENTA POR PAGAR
# ============================================================

@receiver(pre_save, sender=CuentaPorPagar)
def cuenta_por_pagar_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para CuentaPorPagar.
    - Normaliza número de documento
    """
    if instance.numero_documento:
        instance.numero_documento = instance.numero_documento.strip().upper()


@receiver(post_save, sender=CuentaPorPagar)
def cuenta_por_pagar_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para CuentaPorPagar.
    - Log de creación de nuevas cuentas por pagar
    """
    if created:
        logger.info(
            f"Nueva cuenta por pagar registrada: {instance.numero_documento} - "
            f"Proveedor: {instance.proveedor.nombre} - Monto: {instance.monto_original}"
        )


@receiver(pre_delete, sender=CuentaPorPagar)
def cuenta_por_pagar_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para CuentaPorPagar.
    - Advertencia de eliminación
    """
    logger.warning(
        f"Eliminando cuenta por pagar: {instance.numero_documento} - "
        f"Proveedor: {instance.proveedor.nombre}"
    )


# ============================================================
# SIGNALS DE PAGO PROVEEDOR
# ============================================================

@receiver(pre_save, sender=PagoProveedor)
def pago_proveedor_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para PagoProveedor.
    - Normaliza número de pago y referencia
    """
    if instance.numero_pago:
        instance.numero_pago = instance.numero_pago.strip().upper()
    if instance.referencia:
        instance.referencia = instance.referencia.strip()


@receiver(post_save, sender=PagoProveedor)
def pago_proveedor_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para PagoProveedor.
    - Log de creación de nuevos pagos
    """
    if created:
        logger.info(
            f"Nuevo pago registrado: {instance.numero_pago} - "
            f"Proveedor: {instance.proveedor.nombre} - Monto: {instance.monto} - "
            f"Método: {instance.metodo_pago}"
        )


@receiver(pre_delete, sender=PagoProveedor)
def pago_proveedor_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para PagoProveedor.
    - Advertencia de eliminación
    """
    logger.warning(
        f"Eliminando pago: {instance.numero_pago} - "
        f"Proveedor: {instance.proveedor.nombre}"
    )


# ============================================================
# SIGNALS DE DETALLE PAGO PROVEEDOR
# ============================================================

@receiver(post_save, sender=DetallePagoProveedor)
def detalle_pago_proveedor_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para DetallePagoProveedor.
    - Log de aplicación de pagos a cuentas por pagar
    """
    if created:
        logger.info(
            f"Pago {instance.pago.numero_pago} aplicado a "
            f"CxP {instance.cuenta_por_pagar.numero_documento} - "
            f"Monto: {instance.monto_aplicado}"
        )


@receiver(pre_delete, sender=DetallePagoProveedor)
def detalle_pago_proveedor_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para DetallePagoProveedor.
    - Advertencia de eliminación (posible reversión de pago)
    """
    logger.warning(
        f"Eliminando aplicación de pago: {instance.pago.numero_pago} -> "
        f"CxP {instance.cuenta_por_pagar.numero_documento} - "
        f"Monto: {instance.monto_aplicado}"
    )

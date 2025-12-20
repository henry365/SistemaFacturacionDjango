"""
Signals de Django para el módulo Compras

Este módulo define las señales (signals) para automatizar comportamientos
del sistema de compras, incluyendo logging, normalización y actualizaciones.
"""
import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from .models import (
    Compra, OrdenCompra, SolicitudCotizacionProveedor, Gasto,
    RecepcionCompra, DevolucionProveedor, LiquidacionImportacion,
    RetencionCompra
)

logger = logging.getLogger(__name__)


# ============================================================
# SIGNALS DE COMPRA
# ============================================================

@receiver(pre_save, sender=Compra)
def compra_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para Compra.
    - Normaliza número de factura
    """
    if instance.numero_factura_proveedor:
        instance.numero_factura_proveedor = instance.numero_factura_proveedor.strip().upper()


@receiver(post_save, sender=Compra)
def compra_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para Compra.
    - Log de creación de nuevas compras
    """
    if created:
        logger.info(
            f"Nueva compra registrada: {instance.numero_factura_proveedor} - "
            f"Proveedor: {instance.proveedor.nombre} - Total: {instance.total}"
        )


@receiver(pre_delete, sender=Compra)
def compra_pre_delete(sender, instance, **kwargs):
    """
    Signal pre-delete para Compra.
    - Advertencia de eliminación
    """
    logger.warning(
        f"Eliminando compra: {instance.numero_factura_proveedor} - "
        f"Proveedor: {instance.proveedor.nombre}"
    )


# ============================================================
# SIGNALS DE ORDEN DE COMPRA
# ============================================================

@receiver(post_save, sender=OrdenCompra)
def orden_compra_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para OrdenCompra.
    - Log de creación de nuevas órdenes
    - Log de cambios de estado
    """
    if created:
        logger.info(
            f"Nueva orden de compra creada: OC #{instance.id} - "
            f"Proveedor: {instance.proveedor.nombre}"
        )


# ============================================================
# SIGNALS DE SOLICITUD DE COTIZACION
# ============================================================

@receiver(post_save, sender=SolicitudCotizacionProveedor)
def solicitud_cotizacion_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para SolicitudCotizacionProveedor.
    - Log de creación de nuevas solicitudes
    """
    if created:
        logger.info(
            f"Nueva solicitud de cotización creada para proveedor: "
            f"{instance.proveedor.nombre}"
        )


# ============================================================
# SIGNALS DE GASTO
# ============================================================

@receiver(pre_save, sender=Gasto)
def gasto_pre_save(sender, instance, **kwargs):
    """
    Signal pre-save para Gasto.
    - Normaliza descripción y categoría
    """
    if instance.descripcion:
        instance.descripcion = instance.descripcion.strip()
    if instance.categoria:
        instance.categoria = instance.categoria.strip()


@receiver(post_save, sender=Gasto)
def gasto_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para Gasto.
    - Log de creación de nuevos gastos
    """
    if created:
        logger.info(
            f"Nuevo gasto registrado: {instance.descripcion} - "
            f"Total: {instance.total}"
        )


# ============================================================
# SIGNALS DE RECEPCION DE COMPRA
# ============================================================

@receiver(post_save, sender=RecepcionCompra)
def recepcion_compra_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para RecepcionCompra.
    - Log de creación de nuevas recepciones
    """
    if created:
        logger.info(
            f"Nueva recepción de compra: {instance.numero_recepcion} - "
            f"Orden: OC #{instance.orden_compra_id}"
        )


# ============================================================
# SIGNALS DE DEVOLUCION A PROVEEDOR
# ============================================================

@receiver(post_save, sender=DevolucionProveedor)
def devolucion_proveedor_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para DevolucionProveedor.
    - Log de creación de nuevas devoluciones
    """
    if created:
        logger.info(
            f"Nueva devolución a proveedor: {instance.numero_devolucion} - "
            f"Proveedor: {instance.proveedor.nombre}"
        )


# ============================================================
# SIGNALS DE LIQUIDACION DE IMPORTACION
# ============================================================

@receiver(post_save, sender=LiquidacionImportacion)
def liquidacion_importacion_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para LiquidacionImportacion.
    - Log de creación de nuevas liquidaciones
    """
    if created:
        logger.info(
            f"Nueva liquidación de importación: {instance.numero_liquidacion} - "
            f"Compra: {instance.compra.numero_factura_proveedor}"
        )


# ============================================================
# SIGNALS DE RETENCION EN COMPRA
# ============================================================

@receiver(post_save, sender=RetencionCompra)
def retencion_compra_post_save(sender, instance, created, **kwargs):
    """
    Signal post-save para RetencionCompra.
    - Log de creación de nuevas retenciones
    """
    if created:
        logger.info(
            f"Nueva retención aplicada a compra {instance.compra.numero_factura_proveedor}: "
            f"{instance.tipo_retencion.nombre} - Monto: {instance.monto_retenido}"
        )

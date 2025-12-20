"""
Servicios de negocio para el módulo Cuentas por Pagar

Este módulo implementa la lógica de negocio separada de las vistas,
siguiendo los principios SRP (Single Responsibility Principle) y SoC (Separation of Concerns).
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List, Dict, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from .constants import (
    ESTADO_CXP_PENDIENTE, ESTADO_CXP_PARCIAL, ESTADO_CXP_PAGADA,
    ESTADO_CXP_VENCIDA, ESTADO_CXP_ANULADA,
    ESTADOS_CXP_PAGABLES, ESTADOS_CXP_TERMINALES,
    ERROR_CXP_NO_PAGABLE, ERROR_TOTAL_EXCEDE_PAGO,
    ERROR_MONTO_EXCEDE_PENDIENTE, ERROR_PAGO_EMPRESA
)

logger = logging.getLogger(__name__)


class CuentaPorPagarService:
    """
    Servicio para gestionar Cuentas por Pagar.
    """

    @staticmethod
    def crear_desde_compra(compra, usuario=None):
        """
        Crea una CuentaPorPagar a partir de una compra confirmada.

        Args:
            compra: Compra confirmada a crédito
            usuario: Usuario que realiza la operación

        Returns:
            CuentaPorPagar creada
        """
        cxp = CuentaPorPagar(
            empresa=compra.empresa,
            proveedor=compra.proveedor,
            compra=compra,
            numero_documento=compra.numero_factura_proveedor,
            fecha_documento=compra.fecha,
            fecha_vencimiento=compra.fecha_vencimiento,
            monto_original=compra.total,
            estado=ESTADO_CXP_PENDIENTE,
        )
        if usuario:
            cxp.usuario_creacion = usuario
        cxp.save()

        logger.info(
            f"CxP creada desde compra {compra.numero_factura_proveedor} - "
            f"Proveedor: {compra.proveedor.nombre} - Monto: {compra.total}"
        )
        return cxp

    @staticmethod
    def actualizar_estado(cxp: CuentaPorPagar) -> str:
        """
        Actualiza el estado de una CxP basado en montos y fechas.

        Args:
            cxp: Cuenta por pagar a actualizar

        Returns:
            Nuevo estado
        """
        estado_anterior = cxp.estado

        if cxp.estado in ESTADOS_CXP_TERMINALES:
            return cxp.estado

        # Refrescar para obtener monto_pendiente calculado
        cxp.refresh_from_db()

        if cxp.monto_pendiente <= 0:
            cxp.estado = ESTADO_CXP_PAGADA
        elif cxp.monto_pagado > 0:
            cxp.estado = ESTADO_CXP_PARCIAL
        elif cxp.fecha_vencimiento and cxp.fecha_vencimiento < date.today():
            cxp.estado = ESTADO_CXP_VENCIDA
        else:
            cxp.estado = ESTADO_CXP_PENDIENTE

        if cxp.estado != estado_anterior:
            cxp.save(update_fields=['estado'])
            logger.info(
                f"CxP {cxp.numero_documento} cambió de {estado_anterior} a {cxp.estado}"
            )

        return cxp.estado

    @staticmethod
    def anular(cxp: CuentaPorPagar, usuario=None, motivo: str = None):
        """
        Anula una cuenta por pagar.

        Args:
            cxp: Cuenta por pagar a anular
            usuario: Usuario que realiza la operación
            motivo: Motivo de la anulación

        Returns:
            CuentaPorPagar anulada

        Raises:
            ValidationError: Si la CxP no puede ser anulada
        """
        if cxp.estado == ESTADO_CXP_ANULADA:
            return cxp  # Idempotencia

        if cxp.monto_pagado > 0:
            raise ValidationError(
                "No se puede anular una cuenta por pagar con pagos aplicados."
            )

        cxp.estado = ESTADO_CXP_ANULADA
        if motivo:
            cxp.observaciones = f"{cxp.observaciones or ''}\nAnulada: {motivo}".strip()
        if usuario:
            cxp.usuario_modificacion = usuario
        cxp.save()

        logger.warning(f"CxP {cxp.numero_documento} anulada. Motivo: {motivo}")
        return cxp

    @staticmethod
    def obtener_vencidas(empresa) -> List[CuentaPorPagar]:
        """
        Obtiene todas las CxP vencidas de una empresa.

        Args:
            empresa: Empresa a consultar

        Returns:
            Lista de CxP vencidas
        """
        return list(CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=[ESTADO_CXP_PENDIENTE, ESTADO_CXP_PARCIAL],
            fecha_vencimiento__lt=date.today()
        ).select_related('proveedor'))

    @staticmethod
    def marcar_vencidas(empresa) -> int:
        """
        Marca como vencidas todas las CxP pendientes con fecha de vencimiento pasada.

        Args:
            empresa: Empresa a procesar

        Returns:
            Cantidad de CxP marcadas como vencidas
        """
        cxp_vencidas = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=[ESTADO_CXP_PENDIENTE, ESTADO_CXP_PARCIAL],
            fecha_vencimiento__lt=date.today()
        )
        count = cxp_vencidas.update(estado=ESTADO_CXP_VENCIDA)

        if count > 0:
            logger.info(f"Marcadas {count} CxP como vencidas para empresa {empresa.nombre}")

        return count

    @staticmethod
    def resumen_por_proveedor(empresa) -> List[Dict]:
        """
        Obtiene un resumen de CxP pendientes por proveedor.

        Args:
            empresa: Empresa a consultar

        Returns:
            Lista de diccionarios con resumen por proveedor
        """
        from django.db.models import Sum, Count

        return list(CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXP_PAGABLES
        ).values(
            'proveedor__id', 'proveedor__nombre'
        ).annotate(
            total_pendiente=Sum('monto_pendiente'),
            cantidad_facturas=Count('id')
        ).order_by('-total_pendiente'))


class PagoProveedorService:
    """
    Servicio para gestionar Pagos a Proveedores.
    """

    @staticmethod
    @transaction.atomic
    def aplicar_pago(
        pago: PagoProveedor,
        detalles: List[Dict],
        usuario=None
    ) -> PagoProveedor:
        """
        Aplica un pago a múltiples cuentas por pagar.

        Args:
            pago: Pago a aplicar
            detalles: Lista de {cuenta_por_pagar_id, monto_aplicado}
            usuario: Usuario que realiza la operación

        Returns:
            Pago con detalles aplicados

        Raises:
            ValidationError: Si hay errores en la aplicación
        """
        total_aplicado = sum(
            Decimal(str(d['monto_aplicado'])) for d in detalles
        )

        if total_aplicado > pago.monto:
            raise ValidationError(ERROR_TOTAL_EXCEDE_PAGO)

        for detalle in detalles:
            cuenta = CuentaPorPagar.objects.select_for_update().get(
                id=detalle['cuenta_por_pagar_id']
            )
            monto = Decimal(str(detalle['monto_aplicado'])).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

            # Validaciones
            if cuenta.empresa_id != pago.empresa_id:
                raise ValidationError(ERROR_PAGO_EMPRESA)

            if cuenta.estado not in ESTADOS_CXP_PAGABLES:
                raise ValidationError(
                    f"{ERROR_CXP_NO_PAGABLE} ({cuenta.numero_documento})"
                )

            if monto > cuenta.monto_pendiente:
                raise ValidationError(
                    f"{ERROR_MONTO_EXCEDE_PENDIENTE} "
                    f"({cuenta.numero_documento}: {cuenta.monto_pendiente})"
                )

            # Crear detalle
            DetallePagoProveedor.objects.create(
                pago=pago,
                cuenta_por_pagar=cuenta,
                monto_aplicado=monto,
                empresa=pago.empresa
            )

            # Actualizar cuenta por pagar
            cuenta.monto_pagado += monto
            cuenta.save(update_fields=['monto_pagado'])

            # Actualizar estado
            CuentaPorPagarService.actualizar_estado(cuenta)

        logger.info(
            f"Pago {pago.numero_pago} aplicado: {len(detalles)} cuentas, "
            f"total {total_aplicado}"
        )

        pago.refresh_from_db()
        return pago

    @staticmethod
    @transaction.atomic
    def reversar_pago(pago: PagoProveedor, usuario=None, motivo: str = None):
        """
        Reversa un pago y restaura las cuentas por pagar.

        Args:
            pago: Pago a reversar
            usuario: Usuario que realiza la operación
            motivo: Motivo de la reversión

        Returns:
            Pago reversado

        Raises:
            ValidationError: Si el pago no puede ser reversado
        """
        detalles = pago.detalles.select_related('cuenta_por_pagar').all()

        for detalle in detalles:
            cuenta = detalle.cuenta_por_pagar
            cuenta.monto_pagado -= detalle.monto_aplicado
            cuenta.save(update_fields=['monto_pagado'])
            CuentaPorPagarService.actualizar_estado(cuenta)

        # Eliminar detalles
        pago.detalles.all().delete()

        if motivo:
            pago.observaciones = f"{pago.observaciones or ''}\nReversado: {motivo}".strip()
        if usuario:
            pago.usuario_modificacion = usuario
        pago.save()

        logger.warning(
            f"Pago {pago.numero_pago} reversado. "
            f"Detalles eliminados: {len(detalles)}. Motivo: {motivo}"
        )

        return pago

    @staticmethod
    def obtener_monto_disponible(pago: PagoProveedor) -> Decimal:
        """
        Calcula el monto disponible para aplicar de un pago.

        Args:
            pago: Pago a consultar

        Returns:
            Monto disponible
        """
        from django.db.models import Sum

        aplicado = pago.detalles.aggregate(
            total=Sum('monto_aplicado')
        )['total'] or Decimal('0')

        return pago.monto - aplicado

    @staticmethod
    def validar_referencia(metodo_pago: str, referencia: Optional[str]) -> bool:
        """
        Valida si la referencia es requerida según el método de pago.

        Args:
            metodo_pago: Método de pago
            referencia: Referencia proporcionada

        Returns:
            True si es válido
        """
        from .constants import METODOS_REQUIEREN_REFERENCIA

        if metodo_pago in METODOS_REQUIEREN_REFERENCIA:
            return bool(referencia and referencia.strip())
        return True

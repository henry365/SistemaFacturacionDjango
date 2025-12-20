"""
Servicios de negocio para el módulo Cuentas por Cobrar

Este módulo implementa la lógica de negocio separada de las vistas,
siguiendo los principios SRP (Single Responsibility Principle) y SoC (Separation of Concerns).
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List, Dict, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from .constants import (
    ESTADO_CXC_PENDIENTE, ESTADO_CXC_PARCIAL, ESTADO_CXC_COBRADA,
    ESTADO_CXC_VENCIDA, ESTADO_CXC_ANULADA,
    ESTADOS_CXC_COBRABLES, ESTADOS_CXC_TERMINALES,
    ERROR_CXC_NO_COBRABLE, ERROR_TOTAL_EXCEDE_COBRO,
    ERROR_MONTO_EXCEDE_PENDIENTE, ERROR_COBRO_EMPRESA
)

logger = logging.getLogger(__name__)


class CuentaPorCobrarService:
    """
    Servicio para gestionar Cuentas por Cobrar.
    """

    @staticmethod
    def crear_desde_factura(factura, usuario=None):
        """
        Crea una CuentaPorCobrar a partir de una factura de venta.

        Args:
            factura: Factura de venta a crédito
            usuario: Usuario que realiza la operación

        Returns:
            CuentaPorCobrar creada
        """
        cxc = CuentaPorCobrar(
            empresa=factura.empresa,
            cliente=factura.cliente,
            factura=factura,
            numero_documento=factura.numero,
            fecha_documento=factura.fecha,
            fecha_vencimiento=factura.fecha_vencimiento,
            monto_original=factura.total,
            estado=ESTADO_CXC_PENDIENTE,
        )
        if usuario:
            cxc.usuario_creacion = usuario
        cxc.save()

        logger.info(
            f"CxC creada desde factura {factura.numero} - "
            f"Cliente: {factura.cliente.nombre} - Monto: {factura.total}"
        )
        return cxc

    @staticmethod
    def actualizar_estado(cxc: CuentaPorCobrar) -> str:
        """
        Actualiza el estado de una CxC basado en montos y fechas.

        Args:
            cxc: Cuenta por cobrar a actualizar

        Returns:
            Nuevo estado
        """
        estado_anterior = cxc.estado

        if cxc.estado in ESTADOS_CXC_TERMINALES:
            return cxc.estado

        # Refrescar para obtener monto_pendiente calculado
        cxc.refresh_from_db()

        if cxc.monto_pendiente <= 0:
            cxc.estado = ESTADO_CXC_COBRADA
        elif cxc.monto_cobrado > 0:
            cxc.estado = ESTADO_CXC_PARCIAL
        elif cxc.fecha_vencimiento and cxc.fecha_vencimiento < date.today():
            cxc.estado = ESTADO_CXC_VENCIDA
        else:
            cxc.estado = ESTADO_CXC_PENDIENTE

        if cxc.estado != estado_anterior:
            cxc.save(update_fields=['estado'])
            logger.info(
                f"CxC {cxc.numero_documento} cambió de {estado_anterior} a {cxc.estado}"
            )

        return cxc.estado

    @staticmethod
    def anular(cxc: CuentaPorCobrar, usuario=None, motivo: str = None):
        """
        Anula una cuenta por cobrar.

        Args:
            cxc: Cuenta por cobrar a anular
            usuario: Usuario que realiza la operación
            motivo: Motivo de la anulación

        Returns:
            CuentaPorCobrar anulada

        Raises:
            ValidationError: Si la CxC no puede ser anulada
        """
        if cxc.estado == ESTADO_CXC_ANULADA:
            return cxc  # Idempotencia

        if cxc.monto_cobrado > 0:
            raise ValidationError(
                "No se puede anular una cuenta por cobrar con cobros aplicados."
            )

        cxc.estado = ESTADO_CXC_ANULADA
        if motivo:
            cxc.observaciones = f"{cxc.observaciones or ''}\nAnulada: {motivo}".strip()
        if usuario:
            cxc.usuario_modificacion = usuario
        cxc.save()

        logger.warning(f"CxC {cxc.numero_documento} anulada. Motivo: {motivo}")
        return cxc

    @staticmethod
    def obtener_vencidas(empresa) -> List[CuentaPorCobrar]:
        """
        Obtiene todas las CxC vencidas de una empresa.

        Args:
            empresa: Empresa a consultar

        Returns:
            Lista de CxC vencidas
        """
        return list(CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=[ESTADO_CXC_PENDIENTE, ESTADO_CXC_PARCIAL],
            fecha_vencimiento__lt=date.today()
        ).select_related('cliente'))

    @staticmethod
    def marcar_vencidas(empresa) -> int:
        """
        Marca como vencidas todas las CxC pendientes con fecha de vencimiento pasada.

        Args:
            empresa: Empresa a procesar

        Returns:
            Cantidad de CxC marcadas como vencidas
        """
        cxc_vencidas = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=[ESTADO_CXC_PENDIENTE, ESTADO_CXC_PARCIAL],
            fecha_vencimiento__lt=date.today()
        )
        count = cxc_vencidas.update(estado=ESTADO_CXC_VENCIDA)

        if count > 0:
            logger.info(f"Marcadas {count} CxC como vencidas para empresa {empresa.nombre}")

        return count

    @staticmethod
    def resumen_por_cliente(empresa) -> List[Dict]:
        """
        Obtiene un resumen de CxC pendientes por cliente.

        Args:
            empresa: Empresa a consultar

        Returns:
            Lista de diccionarios con resumen por cliente
        """
        from django.db.models import Sum, Count

        return list(CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXC_COBRABLES
        ).values(
            'cliente__id', 'cliente__nombre'
        ).annotate(
            total_pendiente=Sum('monto_pendiente'),
            cantidad_facturas=Count('id')
        ).order_by('-total_pendiente'))


class CobroClienteService:
    """
    Servicio para gestionar Cobros de Clientes.
    """

    @staticmethod
    @transaction.atomic
    def aplicar_cobro(
        cobro: CobroCliente,
        detalles: List[Dict],
        usuario=None
    ) -> CobroCliente:
        """
        Aplica un cobro a múltiples cuentas por cobrar.

        Args:
            cobro: Cobro a aplicar
            detalles: Lista de {cuenta_por_cobrar_id, monto_aplicado}
            usuario: Usuario que realiza la operación

        Returns:
            Cobro con detalles aplicados

        Raises:
            ValidationError: Si hay errores en la aplicación
        """
        total_aplicado = sum(
            Decimal(str(d['monto_aplicado'])) for d in detalles
        )

        if total_aplicado > cobro.monto:
            raise ValidationError(ERROR_TOTAL_EXCEDE_COBRO)

        for detalle in detalles:
            cuenta = CuentaPorCobrar.objects.select_for_update().get(
                id=detalle['cuenta_por_cobrar_id']
            )
            monto = Decimal(str(detalle['monto_aplicado'])).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

            # Validaciones
            if cuenta.empresa_id != cobro.empresa_id:
                raise ValidationError(ERROR_COBRO_EMPRESA)

            if cuenta.estado not in ESTADOS_CXC_COBRABLES:
                raise ValidationError(
                    f"{ERROR_CXC_NO_COBRABLE} ({cuenta.numero_documento})"
                )

            if monto > cuenta.monto_pendiente:
                raise ValidationError(
                    f"{ERROR_MONTO_EXCEDE_PENDIENTE} "
                    f"({cuenta.numero_documento}: {cuenta.monto_pendiente})"
                )

            # Crear detalle
            DetalleCobroCliente.objects.create(
                cobro=cobro,
                cuenta_por_cobrar=cuenta,
                monto_aplicado=monto,
                empresa=cobro.empresa
            )

            # Actualizar cuenta por cobrar
            cuenta.monto_cobrado += monto
            cuenta.save(update_fields=['monto_cobrado'])

            # Actualizar estado
            CuentaPorCobrarService.actualizar_estado(cuenta)

        logger.info(
            f"Cobro {cobro.numero_recibo} aplicado: {len(detalles)} cuentas, "
            f"total {total_aplicado}"
        )

        cobro.refresh_from_db()
        return cobro

    @staticmethod
    @transaction.atomic
    def reversar_cobro(cobro: CobroCliente, usuario=None, motivo: str = None):
        """
        Reversa un cobro y restaura las cuentas por cobrar.

        Args:
            cobro: Cobro a reversar
            usuario: Usuario que realiza la operación
            motivo: Motivo de la reversión

        Returns:
            Cobro reversado

        Raises:
            ValidationError: Si el cobro no puede ser reversado
        """
        detalles = cobro.detalles.select_related('cuenta_por_cobrar').all()

        for detalle in detalles:
            cuenta = detalle.cuenta_por_cobrar
            cuenta.monto_cobrado -= detalle.monto_aplicado
            cuenta.save(update_fields=['monto_cobrado'])
            CuentaPorCobrarService.actualizar_estado(cuenta)

        # Eliminar detalles
        cobro.detalles.all().delete()

        if motivo:
            cobro.observaciones = f"{cobro.observaciones or ''}\nReversado: {motivo}".strip()
        if usuario:
            cobro.usuario_modificacion = usuario
        cobro.save()

        logger.warning(
            f"Cobro {cobro.numero_recibo} reversado. "
            f"Detalles eliminados: {len(detalles)}. Motivo: {motivo}"
        )

        return cobro

    @staticmethod
    def obtener_monto_disponible(cobro: CobroCliente) -> Decimal:
        """
        Calcula el monto disponible para aplicar de un cobro.

        Args:
            cobro: Cobro a consultar

        Returns:
            Monto disponible
        """
        from django.db.models import Sum

        aplicado = cobro.detalles.aggregate(
            total=Sum('monto_aplicado')
        )['total'] or Decimal('0')

        return cobro.monto - aplicado

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

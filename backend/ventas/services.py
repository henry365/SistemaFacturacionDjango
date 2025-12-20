"""
Servicios para el módulo Ventas

Este módulo centraliza la lógica de negocio para operaciones
complejas relacionadas con ventas, facturas, pagos y más.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count

from .models import (
    Factura, DetalleFactura, CotizacionCliente, PagoCaja,
    NotaCredito, NotaDebito, DevolucionVenta, ListaEsperaProducto
)
from .constants import (
    ESTADO_FACTURA_PAGADA, ESTADO_FACTURA_PAGADA_PARCIAL,
    ESTADO_COTIZACION_APROBADA, ESTADO_LISTA_NOTIFICADO,
    ERROR_MONTO_NEGATIVO, ERROR_MONTO_PENDIENTE_MAYOR_TOTAL
)

logger = logging.getLogger(__name__)


class ServicioFactura:
    """Servicio para operaciones complejas con facturas."""

    @staticmethod
    def calcular_totales(factura: Factura) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calcula subtotal, ITBIS y total de una factura basado en sus detalles.

        Args:
            factura: Factura para calcular totales

        Returns:
            Tuple (subtotal, itbis, total)
        """
        detalles = factura.detalles.all()

        subtotal = sum(
            (detalle.cantidad * detalle.precio_unitario - detalle.descuento)
            for detalle in detalles
        )

        itbis = sum(detalle.itbis for detalle in detalles)
        total = subtotal + itbis - factura.descuento

        logger.info(f"Totales calculados para factura {factura.numero_factura}: subtotal={subtotal}, itbis={itbis}, total={total}")

        return Decimal(str(subtotal)), Decimal(str(itbis)), Decimal(str(total))

    @staticmethod
    def obtener_estadisticas_factura(factura: Factura) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una factura.

        Args:
            factura: Factura para obtener estadísticas

        Returns:
            Diccionario con estadísticas
        """
        detalles = factura.detalles.all()
        total_items = detalles.count()
        total_cantidad = detalles.aggregate(total=Sum('cantidad'))['total'] or Decimal('0')

        return {
            'total_items': total_items,
            'total_cantidad': float(total_cantidad),
            'subtotal': float(factura.subtotal),
            'itbis': float(factura.itbis),
            'descuento': float(factura.descuento),
            'total': float(factura.total),
            'monto_pendiente': float(factura.monto_pendiente),
            'estado': factura.estado,
            'tipo_venta': factura.tipo_venta,
        }

    @staticmethod
    def obtener_historial_pagos(factura: Factura) -> List[Dict[str, Any]]:
        """
        Obtiene historial de pagos de una factura.

        Args:
            factura: Factura para obtener pagos

        Returns:
            Lista de pagos
        """
        pagos = factura.pagos.all().order_by('-fecha_pago')

        return [{
            'id': p.id,
            'fecha_pago': p.fecha_pago,
            'monto': float(p.monto),
            'metodo_pago': p.metodo_pago,
            'referencia': p.referencia,
        } for p in pagos]

    @staticmethod
    def buscar_facturas(
        empresa_id: int,
        estado: Optional[str] = None,
        cliente_id: Optional[int] = None,
        tipo_venta: Optional[str] = None
    ) -> List[Factura]:
        """
        Busca facturas con filtros.

        Args:
            empresa_id: ID de la empresa
            estado: Estado de la factura (opcional)
            cliente_id: ID del cliente (opcional)
            tipo_venta: Tipo de venta (opcional)

        Returns:
            Lista de facturas
        """
        qs = Factura.objects.filter(empresa_id=empresa_id)

        if estado:
            qs = qs.filter(estado=estado)
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if tipo_venta:
            qs = qs.filter(tipo_venta=tipo_venta)

        return list(qs.order_by('-fecha'))


class ServicioCotizacion:
    """Servicio para operaciones complejas con cotizaciones."""

    @staticmethod
    def obtener_estadisticas_cotizacion(cotizacion: CotizacionCliente) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una cotización.

        Args:
            cotizacion: Cotización para obtener estadísticas

        Returns:
            Diccionario con estadísticas
        """
        detalles = cotizacion.detalles.all()
        total_items = detalles.count()
        total_cantidad = detalles.aggregate(total=Sum('cantidad'))['total'] or Decimal('0')

        return {
            'total_items': total_items,
            'total_cantidad': float(total_cantidad),
            'total': float(cotizacion.total),
            'estado': cotizacion.estado,
            'vigencia': cotizacion.vigencia,
        }

    @staticmethod
    def convertir_a_factura(
        cotizacion: CotizacionCliente,
        numero_factura: str,
        usuario
    ) -> Optional[Factura]:
        """
        Convierte una cotización aprobada en factura.

        Args:
            cotizacion: Cotización a convertir
            numero_factura: Número de la factura
            usuario: Usuario que realiza la conversión

        Returns:
            Factura creada o None si falla
        """
        if cotizacion.estado != ESTADO_COTIZACION_APROBADA:
            logger.warning(f"Cotización {cotizacion.id} no está aprobada, no se puede convertir")
            return None

        try:
            with transaction.atomic():
                factura = Factura.objects.create(
                    empresa=cotizacion.empresa,
                    cliente=cotizacion.cliente,
                    vendedor=cotizacion.vendedor,
                    cotizacion=cotizacion,
                    numero_factura=numero_factura,
                    total=cotizacion.total,
                    monto_pendiente=cotizacion.total,
                    usuario=usuario
                )

                # Copiar detalles
                for detalle in cotizacion.detalles.all():
                    DetalleFactura.objects.create(
                        factura=factura,
                        producto=detalle.producto,
                        cantidad=detalle.cantidad,
                        precio_unitario=detalle.precio_unitario,
                        descuento=detalle.descuento,
                        itbis=detalle.impuesto
                    )

                logger.info(f"Cotización {cotizacion.id} convertida a factura {numero_factura}")
                return factura

        except Exception as e:
            logger.error(f"Error convirtiendo cotización {cotizacion.id}: {e}")
            return None


class ServicioPago:
    """Servicio para operaciones de pagos."""

    @staticmethod
    def registrar_pago(
        factura: Factura,
        monto: Decimal,
        metodo_pago: str,
        usuario,
        referencia: Optional[str] = None
    ) -> Tuple[Optional[PagoCaja], Optional[str]]:
        """
        Registra un pago para una factura.

        Args:
            factura: Factura a pagar
            monto: Monto del pago
            metodo_pago: Método de pago
            usuario: Usuario que registra el pago
            referencia: Referencia del pago (opcional)

        Returns:
            Tuple (pago creado, mensaje de error)
        """
        if monto <= 0:
            return None, ERROR_MONTO_NEGATIVO

        if monto > factura.monto_pendiente:
            return None, ERROR_MONTO_PENDIENTE_MAYOR_TOTAL

        try:
            with transaction.atomic():
                pago = PagoCaja.objects.create(
                    empresa=factura.empresa,
                    cliente=factura.cliente,
                    monto=monto,
                    metodo_pago=metodo_pago,
                    referencia=referencia,
                    usuario=usuario
                )
                pago.facturas.add(factura)

                # Actualizar factura
                factura.monto_pendiente -= monto
                if factura.monto_pendiente == 0:
                    factura.estado = ESTADO_FACTURA_PAGADA
                else:
                    factura.estado = ESTADO_FACTURA_PAGADA_PARCIAL
                factura.save()

                logger.info(f"Pago {pago.id} registrado para factura {factura.numero_factura}: {monto}")
                return pago, None

        except Exception as e:
            logger.error(f"Error registrando pago: {e}")
            return None, str(e)


class ServicioListaEspera:
    """Servicio para operaciones de lista de espera."""

    @staticmethod
    def obtener_estadisticas_lista(empresa_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la lista de espera.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Diccionario con estadísticas
        """
        listas = ListaEsperaProducto.objects.filter(empresa_id=empresa_id)

        stats = listas.values('estado').annotate(count=Count('id'))
        por_estado = {s['estado']: s['count'] for s in stats}

        return {
            'total': listas.count(),
            'por_estado': por_estado,
        }

    @staticmethod
    def notificar_disponibilidad(lista_espera: ListaEsperaProducto) -> bool:
        """
        Marca una entrada de lista de espera como notificada.

        Args:
            lista_espera: Entrada de lista de espera

        Returns:
            True si se actualizó correctamente
        """
        try:
            lista_espera.estado = ESTADO_LISTA_NOTIFICADO
            lista_espera.save()
            logger.info(f"Lista de espera {lista_espera.id} marcada como notificada")
            return True
        except Exception as e:
            logger.error(f"Error notificando lista de espera: {e}")
            return False


class ServicioNotasCredito:
    """Servicio para operaciones de notas de crédito."""

    @staticmethod
    def aplicar_nota_credito(nota: NotaCredito, factura: Factura) -> Tuple[bool, Optional[str]]:
        """
        Aplica una nota de crédito a una factura.

        Args:
            nota: Nota de crédito a aplicar
            factura: Factura destino

        Returns:
            Tuple (éxito, mensaje de error)
        """
        if nota.aplicada:
            return False, "La nota de crédito ya fue aplicada."

        if nota.monto > factura.monto_pendiente:
            return False, "El monto de la nota excede el monto pendiente de la factura."

        try:
            with transaction.atomic():
                factura.monto_pendiente -= nota.monto
                if factura.monto_pendiente == 0:
                    factura.estado = ESTADO_FACTURA_PAGADA
                elif factura.monto_pendiente < factura.total:
                    factura.estado = ESTADO_FACTURA_PAGADA_PARCIAL
                factura.save()

                nota.factura = factura
                nota.aplicada = True
                nota.save()

                logger.info(f"Nota de crédito {nota.id} aplicada a factura {factura.numero_factura}")
                return True, None

        except Exception as e:
            logger.error(f"Error aplicando nota de crédito: {e}")
            return False, str(e)

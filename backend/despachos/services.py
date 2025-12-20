"""
Servicios de negocio para el módulo de Despachos

Separa la lógica de negocio de las vistas para cumplir con los principios
SRP (Single Responsibility Principle) y SoC (Separation of Concerns).
"""
import logging
from decimal import Decimal
from typing import Optional, Tuple, List, Dict
from django.db import transaction
from django.utils import timezone

from .models import Despacho, DetalleDespacho
from .constants import (
    ESTADO_PENDIENTE, ESTADO_EN_PREPARACION, ESTADO_PARCIAL,
    ESTADO_COMPLETADO, ESTADO_CANCELADO,
    ESTADOS_DESPACHABLES, ESTADOS_CANCELABLES, ESTADOS_TERMINALES,
    ERROR_SOLO_PENDIENTES_PREPARAR, ERROR_ESTADO_NO_PERMITE_DESPACHAR,
    ERROR_YA_COMPLETADO, ERROR_NO_COMPLETAR_CANCELADO,
    ERROR_NO_CANCELAR_COMPLETADO, ERROR_YA_CANCELADO,
    ERROR_STOCK_INSUFICIENTE, ERROR_DESPACHO_FALLIDO
)

logger = logging.getLogger(__name__)


class DespachoService:
    """Servicio para gestionar operaciones de negocio de Despachos"""

    @staticmethod
    def preparar(despacho: Despacho, usuario) -> Tuple[Optional[Despacho], Optional[str]]:
        """
        Marca un despacho como en preparación.

        IDEMPOTENTE: Si ya está en preparación, retorna el despacho sin cambios.

        Args:
            despacho: Instancia de Despacho
            usuario: Usuario que realiza la operación

        Returns:
            Tuple[Despacho, None] en éxito, Tuple[None, error] en fallo
        """
        # Idempotencia: si ya está en preparación, retornamos éxito
        if despacho.estado == ESTADO_EN_PREPARACION:
            logger.info(f"Despacho {despacho.id} ya está en preparación (idempotente)")
            return despacho, None

        if despacho.estado != ESTADO_PENDIENTE:
            return None, ERROR_SOLO_PENDIENTES_PREPARAR

        try:
            despacho.estado = ESTADO_EN_PREPARACION
            despacho.usuario_modificacion = usuario
            despacho.save(update_fields=['estado', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(f"Despacho {despacho.id} marcado como en preparación por {usuario}")
            return despacho, None

        except Exception as e:
            logger.error(f"Error preparando despacho {despacho.id}: {e}")
            return None, str(e)

    @staticmethod
    @transaction.atomic
    def procesar_despacho(
        despacho: Despacho,
        detalles_data: List[Dict],
        usuario,
        observaciones: str = ''
    ) -> Tuple[Optional[Despacho], Optional[str]]:
        """
        Procesa el despacho de productos.

        IDEMPOTENTE: Usa get_or_create para detalles, actualizaciones incrementales.

        Args:
            despacho: Instancia de Despacho
            detalles_data: Lista de dicts con {producto_id, cantidad}
            usuario: Usuario que realiza la operación
            observaciones: Observaciones opcionales

        Returns:
            Tuple[Despacho, None] en éxito, Tuple[None, error] en fallo
        """
        if despacho.estado not in ESTADOS_DESPACHABLES:
            return None, ERROR_ESTADO_NO_PERMITE_DESPACHAR

        try:
            # Refrescar para evitar condiciones de carrera
            despacho.refresh_from_db()

            # Procesar cada detalle
            for detalle_data in detalles_data:
                producto_id = detalle_data['producto_id']
                cantidad = Decimal(str(detalle_data['cantidad']))

                # Buscar o crear detalle
                detalle, created = DetalleDespacho.objects.get_or_create(
                    despacho=despacho,
                    producto_id=producto_id,
                    defaults={
                        'cantidad_solicitada': cantidad,
                        'cantidad_despachada': cantidad,
                        'usuario_creacion': usuario
                    }
                )

                if not created:
                    # Actualizar cantidad despachada (incrementalmente)
                    nueva_cantidad = detalle.cantidad_despachada + cantidad
                    # Validar que no exceda la cantidad solicitada
                    if nueva_cantidad > detalle.cantidad_solicitada:
                        nueva_cantidad = detalle.cantidad_solicitada
                    detalle.cantidad_despachada = nueva_cantidad
                    detalle.usuario_modificacion = usuario
                    detalle.save()

            # Actualizar despacho
            despacho.fecha_despacho = timezone.now()
            despacho.usuario_despacho = usuario
            despacho.usuario_modificacion = usuario

            if observaciones:
                despacho.observaciones = observaciones

            # Determinar estado basado en totales
            nuevo_estado = DespachoService._calcular_estado(despacho)
            despacho.estado = nuevo_estado

            despacho.save()

            logger.info(
                f"Despacho {despacho.id} procesado por {usuario}, "
                f"nuevo estado: {nuevo_estado}"
            )
            return despacho, None

        except Exception as e:
            logger.error(f"Error procesando despacho {despacho.id}: {e}")
            return None, ERROR_DESPACHO_FALLIDO

    @staticmethod
    def _calcular_estado(despacho: Despacho) -> str:
        """Calcula el estado basado en las cantidades despachadas"""
        detalles = despacho.detalles.all()

        if not detalles.exists():
            return despacho.estado

        total_solicitado = sum(d.cantidad_solicitada for d in detalles)
        total_despachado = sum(d.cantidad_despachada for d in detalles)

        if total_despachado >= total_solicitado:
            return ESTADO_COMPLETADO
        elif total_despachado > 0:
            return ESTADO_PARCIAL
        else:
            return despacho.estado

    @staticmethod
    def completar(despacho: Despacho, usuario) -> Tuple[Optional[Despacho], Optional[str]]:
        """
        Marca un despacho como completado.

        IDEMPOTENTE: Si ya está completado, retorna el despacho sin cambios.

        Args:
            despacho: Instancia de Despacho
            usuario: Usuario que realiza la operación

        Returns:
            Tuple[Despacho, None] en éxito, Tuple[None, error] en fallo
        """
        # Idempotencia
        if despacho.estado == ESTADO_COMPLETADO:
            logger.info(f"Despacho {despacho.id} ya está completado (idempotente)")
            return despacho, None

        if despacho.estado == ESTADO_CANCELADO:
            return None, ERROR_NO_COMPLETAR_CANCELADO

        try:
            despacho.estado = ESTADO_COMPLETADO
            despacho.fecha_despacho = timezone.now()
            despacho.usuario_despacho = usuario
            despacho.usuario_modificacion = usuario
            despacho.save()

            logger.info(f"Despacho {despacho.id} completado por {usuario}")
            return despacho, None

        except Exception as e:
            logger.error(f"Error completando despacho {despacho.id}: {e}")
            return None, str(e)

    @staticmethod
    def cancelar(
        despacho: Despacho,
        usuario,
        observaciones: str = ''
    ) -> Tuple[Optional[Despacho], Optional[str]]:
        """
        Cancela un despacho.

        IDEMPOTENTE: Si ya está cancelado, retorna el despacho sin cambios.

        Args:
            despacho: Instancia de Despacho
            usuario: Usuario que realiza la operación
            observaciones: Motivo de cancelación

        Returns:
            Tuple[Despacho, None] en éxito, Tuple[None, error] en fallo
        """
        # Idempotencia
        if despacho.estado == ESTADO_CANCELADO:
            logger.info(f"Despacho {despacho.id} ya está cancelado (idempotente)")
            return despacho, None

        if despacho.estado == ESTADO_COMPLETADO:
            return None, ERROR_NO_CANCELAR_COMPLETADO

        if despacho.estado not in ESTADOS_CANCELABLES:
            return None, f"No se puede cancelar un despacho en estado {despacho.estado}"

        try:
            despacho.estado = ESTADO_CANCELADO
            despacho.usuario_modificacion = usuario

            if observaciones:
                despacho.observaciones = observaciones

            despacho.save()

            logger.info(f"Despacho {despacho.id} cancelado por {usuario}")
            return despacho, None

        except Exception as e:
            logger.error(f"Error cancelando despacho {despacho.id}: {e}")
            return None, str(e)

    @staticmethod
    def obtener_resumen(despacho: Despacho) -> Dict:
        """
        Obtiene un resumen del estado del despacho.

        Args:
            despacho: Instancia de Despacho

        Returns:
            Dict con resumen de cantidades
        """
        detalles = despacho.detalles.all()

        total_solicitado = sum(d.cantidad_solicitada for d in detalles)
        total_despachado = sum(d.cantidad_despachada for d in detalles)
        porcentaje = (
            (total_despachado / total_solicitado * 100)
            if total_solicitado > 0 else Decimal('0')
        )

        return {
            'total_productos': detalles.count(),
            'total_solicitado': str(total_solicitado),
            'total_despachado': str(total_despachado),
            'porcentaje_completado': str(porcentaje.quantize(Decimal('0.01'))),
            'estado': despacho.estado,
            'es_completo': total_despachado >= total_solicitado
        }

    @staticmethod
    def obtener_pendientes_por_almacen(empresa, almacen_id: int) -> List[Despacho]:
        """
        Obtiene despachos pendientes para un almacén.

        Args:
            empresa: Instancia de Empresa
            almacen_id: ID del almacén

        Returns:
            QuerySet de despachos pendientes
        """
        return Despacho.objects.filter(
            empresa=empresa,
            almacen_id=almacen_id,
            estado__in=[ESTADO_PENDIENTE, ESTADO_EN_PREPARACION, ESTADO_PARCIAL]
        ).select_related('factura', 'cliente').order_by('fecha_creacion')

    @staticmethod
    def obtener_estadisticas(empresa) -> Dict:
        """
        Obtiene estadísticas de despachos.

        Args:
            empresa: Instancia de Empresa

        Returns:
            Dict con estadísticas
        """
        from django.db.models import Count

        stats = Despacho.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            cantidad=Count('id')
        )

        result = {
            'pendientes': 0,
            'en_preparacion': 0,
            'parciales': 0,
            'completados': 0,
            'cancelados': 0,
            'total': 0
        }

        for s in stats:
            estado = s['estado'].lower()
            if estado in result:
                result[estado] = s['cantidad']
            result['total'] += s['cantidad']

        return result

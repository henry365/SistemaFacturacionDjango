"""
Servicios de negocio para el módulo de Activos Fijos

Este módulo contiene la lógica de negocio separada de las vistas,
facilitando la testabilidad y mantenibilidad.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

# Constante para redondeo monetario a 2 decimales
DECIMAL_PLACES = Decimal('0.01')

from .models import ActivoFijo, Depreciacion, TipoActivo
from .constants import (
    ESTADO_DEPRECIADO,
    ESTADOS_DEPRECIABLES,
    MESES_POR_ANO,
    TOLERANCIA_DECIMAL,
)

logger = logging.getLogger(__name__)


class DepreciacionService:
    """
    Servicio para gestionar la depreciación de activos fijos.
    """

    @staticmethod
    def puede_depreciar(activo: ActivoFijo) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un activo puede ser depreciado.

        Args:
            activo: Instancia de ActivoFijo

        Returns:
            Tuple (puede_depreciar, mensaje_error)
        """
        if activo.estado not in ESTADOS_DEPRECIABLES:
            return False, f'El activo debe estar en estado {ESTADOS_DEPRECIABLES} para depreciarse'

        if activo.valor_libro_actual <= 0:
            return False, 'El activo ya está totalmente depreciado'

        return True, None

    @staticmethod
    def calcular_depreciacion_mensual(
        activo: ActivoFijo,
        metodo: str = 'linea_recta'
    ) -> Decimal:
        """
        Calcula el monto de depreciación mensual para un activo.

        Args:
            activo: Instancia de ActivoFijo
            metodo: 'linea_recta' o 'saldos_decrecientes'

        Returns:
            Monto de depreciación mensual
        """
        tasa_mensual = (
            activo.tipo_activo.porcentaje_depreciacion_anual
            / Decimal(str(MESES_POR_ANO))
            / Decimal('100')
        )

        if metodo == 'linea_recta':
            # Depreciación constante basada en valor de adquisición
            monto = activo.valor_adquisicion * tasa_mensual
        elif metodo == 'saldos_decrecientes':
            # Depreciación basada en valor libro actual
            monto = activo.valor_libro_actual * tasa_mensual
        else:
            raise ValueError(f'Método de depreciación no válido: {metodo}')

        # Redondear a 2 decimales para precisión monetaria
        monto = monto.quantize(DECIMAL_PLACES, rounding=ROUND_HALF_UP)

        # No depreciar más del valor libro actual
        return min(monto, activo.valor_libro_actual)

    @classmethod
    def registrar_depreciacion(
        cls,
        activo: ActivoFijo,
        fecha,
        usuario,
        observacion: str = '',
        metodo: str = 'linea_recta'
    ) -> Tuple[Optional[Depreciacion], Optional[str]]:
        """
        Registra una depreciación para un activo.

        Args:
            activo: Instancia de ActivoFijo
            fecha: Fecha de la depreciación
            usuario: Usuario que registra
            observacion: Comentario opcional
            metodo: Método de depreciación

        Returns:
            Tuple (depreciacion, mensaje_error)
        """
        # Verificar si puede depreciarse
        puede, error = cls.puede_depreciar(activo)
        if not puede:
            return None, error

        # Verificar que no exista depreciación para esa fecha
        if Depreciacion.objects.filter(activo=activo, fecha=fecha).exists():
            return None, 'Ya existe una depreciación para esta fecha'

        # Calcular monto
        monto = cls.calcular_depreciacion_mensual(activo, metodo)

        valor_libro_anterior = activo.valor_libro_actual
        valor_libro_nuevo = valor_libro_anterior - monto

        try:
            with transaction.atomic():
                depreciacion = Depreciacion.objects.create(
                    activo=activo,
                    fecha=fecha,
                    monto=monto,
                    valor_libro_anterior=valor_libro_anterior,
                    valor_libro_nuevo=valor_libro_nuevo,
                    observacion=observacion,
                    usuario_creacion=usuario
                )

                # Actualizar estado si está totalmente depreciado
                if valor_libro_nuevo <= 0:
                    activo.refresh_from_db()
                    activo.estado = ESTADO_DEPRECIADO
                    activo.save(update_fields=['estado'])

                logger.info(
                    f"Depreciación registrada: Activo {activo.codigo_interno}, "
                    f"Monto {monto}, Usuario {usuario.username}"
                )

                return depreciacion, None

        except ValidationError as e:
            logger.error(f"Error al registrar depreciación: {e}")
            return None, str(e)

    @staticmethod
    def calcular_proyeccion_depreciacion(
        activo: ActivoFijo,
        meses: int = 12,
        metodo: str = 'linea_recta'
    ) -> list:
        """
        Calcula una proyección de depreciaciones futuras.

        Args:
            activo: Instancia de ActivoFijo
            meses: Número de meses a proyectar
            metodo: Método de depreciación

        Returns:
            Lista de diccionarios con proyección mensual
        """
        proyeccion = []
        valor_libro = activo.valor_libro_actual

        tasa_mensual = (
            activo.tipo_activo.porcentaje_depreciacion_anual
            / Decimal(str(MESES_POR_ANO))
            / Decimal('100')
        )

        for mes in range(1, meses + 1):
            if valor_libro <= 0:
                break

            if metodo == 'linea_recta':
                monto = activo.valor_adquisicion * tasa_mensual
            else:
                monto = valor_libro * tasa_mensual

            # Redondear a 2 decimales para precisión monetaria
            monto = monto.quantize(DECIMAL_PLACES, rounding=ROUND_HALF_UP)
            monto = min(monto, valor_libro)
            valor_libro_nuevo = (valor_libro - monto).quantize(
                DECIMAL_PLACES, rounding=ROUND_HALF_UP
            )

            proyeccion.append({
                'mes': mes,
                'monto_depreciacion': monto,
                'valor_libro_inicial': valor_libro,
                'valor_libro_final': valor_libro_nuevo,
            })

            valor_libro = valor_libro_nuevo

        return proyeccion


class ActivoFijoService:
    """
    Servicio para gestionar activos fijos.
    """

    @staticmethod
    def cambiar_estado(
        activo: ActivoFijo,
        nuevo_estado: str,
        usuario,
        validar_transicion: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Cambia el estado de un activo con validación de transiciones.

        Args:
            activo: Instancia de ActivoFijo
            nuevo_estado: Nuevo estado a asignar
            usuario: Usuario que realiza el cambio
            validar_transicion: Si validar transiciones permitidas

        Returns:
            Tuple (exito, mensaje_error)
        """
        from .constants import ESTADOS_VALIDOS

        if nuevo_estado not in ESTADOS_VALIDOS:
            return False, f'Estado inválido. Opciones: {ESTADOS_VALIDOS}'

        # Transiciones no permitidas
        if validar_transicion:
            # No se puede volver a ACTIVO si está VENDIDO o DESINCORPORADO
            if (activo.estado in ['VENDIDO', 'DESINCORPORADO'] and
                nuevo_estado == 'ACTIVO'):
                return False, f'No se puede cambiar de {activo.estado} a ACTIVO'

        estado_anterior = activo.estado
        activo.estado = nuevo_estado
        activo.usuario_modificacion = usuario
        activo.save()

        logger.info(
            f"Cambio de estado: Activo {activo.codigo_interno}, "
            f"{estado_anterior} -> {nuevo_estado}, Usuario {usuario.username}"
        )

        return True, None

    @staticmethod
    def calcular_valor_residual(activo: ActivoFijo) -> Decimal:
        """
        Calcula el valor residual de un activo basado en su vida útil.

        Args:
            activo: Instancia de ActivoFijo

        Returns:
            Valor residual estimado
        """
        # Valor residual típico es 10% del valor de adquisición
        return activo.valor_adquisicion * Decimal('0.10')

    @staticmethod
    def obtener_resumen_por_empresa(empresa) -> dict:
        """
        Obtiene un resumen de activos por empresa.

        Args:
            empresa: Instancia de Empresa

        Returns:
            Diccionario con totales y estadísticas
        """
        from django.db.models import Sum, Count, Avg

        activos = ActivoFijo.objects.filter(empresa=empresa)

        return activos.aggregate(
            total_activos=Count('id'),
            valor_adquisicion_total=Sum('valor_adquisicion'),
            valor_libro_total=Sum('valor_libro_actual'),
            depreciacion_promedio=Avg('depreciacion_acumulada'),
        )

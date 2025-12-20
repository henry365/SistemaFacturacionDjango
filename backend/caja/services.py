"""
Servicios de negocio para el módulo de Caja

Este módulo contiene la lógica de negocio separada de las vistas,
facilitando la testabilidad y mantenibilidad.

Todos los métodos son IDEMPOTENTES según la Guía Inicial.
"""
import logging
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Caja, SesionCaja, MovimientoCaja
from .constants import (
    ESTADO_ABIERTA, ESTADO_CERRADA, ESTADO_ARQUEADA,
    TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR,
    TIPO_APERTURA, TIPO_CIERRE,
    TIPOS_INGRESO, TIPOS_EGRESO, TIPOS_NO_ELIMINABLES, TIPOS_NO_EDITABLES
)

logger = logging.getLogger(__name__)


class CajaService:
    """
    Servicio para gestionar Cajas.
    """

    @staticmethod
    def activar_caja(
        caja: Caja,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Activa una caja.

        IDEMPOTENTE: Verifica si ya está activa antes de operar.

        Args:
            caja: Caja a activar
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if caja.activa:
            logger.info(f"Caja '{caja.nombre}' ya está activa")
            return True, None  # Ya está activa (idempotente)

        caja.activa = True
        caja.usuario_modificacion = ejecutado_por
        caja.save(update_fields=['activa', 'usuario_modificacion', 'fecha_actualizacion'])

        logger.info(f"Caja '{caja.nombre}' activada por {ejecutado_por.username}")
        return True, None

    @staticmethod
    def desactivar_caja(
        caja: Caja,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Desactiva una caja.

        IDEMPOTENTE: Verifica si ya está inactiva antes de operar.

        Args:
            caja: Caja a desactivar
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if not caja.activa:
            logger.info(f"Caja '{caja.nombre}' ya está inactiva")
            return True, None  # Ya está inactiva (idempotente)

        # Validar que no tenga sesión abierta
        if caja.tiene_sesion_abierta():
            return False, 'No se puede desactivar una caja con sesión abierta'

        caja.activa = False
        caja.usuario_modificacion = ejecutado_por
        caja.save(update_fields=['activa', 'usuario_modificacion', 'fecha_actualizacion'])

        logger.warning(f"Caja '{caja.nombre}' desactivada por {ejecutado_por.username}")
        return True, None


class SesionCajaService:
    """
    Servicio para gestionar Sesiones de Caja.
    """

    @staticmethod
    def abrir_sesion(
        caja: Caja,
        monto_apertura: Decimal,
        usuario,
        observaciones: str = None
    ) -> Tuple[Optional[SesionCaja], Optional[str]]:
        """
        Abre una nueva sesión de caja.

        IDEMPOTENTE: Verifica si ya hay una sesión abierta.

        Args:
            caja: Caja donde abrir la sesión
            monto_apertura: Monto inicial en efectivo
            usuario: Usuario que abre la sesión
            observaciones: Observaciones opcionales

        Returns:
            Tuple (sesion, mensaje_error)
        """
        # Validar que la caja esté activa
        if not caja.activa:
            return None, 'La caja no está activa'

        # IDEMPOTENCIA: Verificar si ya hay sesión abierta
        sesion_activa = caja.get_sesion_activa()
        if sesion_activa:
            if sesion_activa.usuario == usuario:
                logger.info(
                    f"Sesión ya abierta en caja '{caja.nombre}' por el mismo usuario"
                )
                return sesion_activa, None  # Retornar sesión existente (idempotente)
            return None, 'Ya existe una sesión abierta en esta caja'

        # Validar monto de apertura
        if monto_apertura is None or monto_apertura < 0:
            return None, 'El monto de apertura no puede ser negativo'

        try:
            with transaction.atomic():
                sesion = SesionCaja.objects.create(
                    caja=caja,
                    empresa=caja.empresa,
                    usuario=usuario,
                    monto_apertura=monto_apertura,
                    estado=ESTADO_ABIERTA,
                    observaciones=observaciones,
                    usuario_creacion=usuario
                )

                # Registrar movimiento de apertura
                MovimientoCaja.objects.create(
                    sesion=sesion,
                    empresa=caja.empresa,
                    tipo_movimiento=TIPO_APERTURA,
                    monto=monto_apertura,
                    descripcion='Monto de apertura de caja',
                    usuario=usuario,
                    usuario_creacion=usuario
                )

            logger.info(
                f"Sesión {sesion.id} abierta en caja '{caja.nombre}' "
                f"por {usuario.username} con monto {monto_apertura}"
            )
            return sesion, None

        except Exception as e:
            logger.error(f"Error abriendo sesión en caja '{caja.nombre}': {e}")
            return None, str(e)

    @staticmethod
    def cerrar_sesion(
        sesion: SesionCaja,
        monto_cierre_usuario: Decimal,
        ejecutado_por,
        observaciones: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Cierra una sesión de caja.

        IDEMPOTENTE: Verifica si ya está cerrada antes de operar.

        Args:
            sesion: Sesión a cerrar
            monto_cierre_usuario: Monto declarado por el cajero
            ejecutado_por: Usuario que cierra la sesión
            observaciones: Observaciones opcionales

        Returns:
            Tuple (exito, mensaje_error)
        """
        # IDEMPOTENCIA: Verificar si ya está cerrada
        if sesion.estado in [ESTADO_CERRADA, ESTADO_ARQUEADA]:
            logger.info(f"Sesión {sesion.id} ya está cerrada")
            return True, None  # Ya está cerrada (idempotente)

        if sesion.estado != ESTADO_ABIERTA:
            return False, f'No se puede cerrar una sesión en estado {sesion.estado}'

        # Validar monto de cierre
        if monto_cierre_usuario is None or monto_cierre_usuario < 0:
            return False, 'El monto de cierre no puede ser negativo'

        try:
            with transaction.atomic():
                # Calcular monto de cierre del sistema
                monto_sistema = SesionCajaService.calcular_saldo_sesion(sesion)

                # Calcular diferencia
                diferencia = monto_cierre_usuario - monto_sistema

                # IMPORTANTE: Crear movimiento de cierre ANTES de cambiar estado
                # (porque la validación no permite movimientos en sesión cerrada)
                MovimientoCaja.objects.create(
                    sesion=sesion,
                    empresa=sesion.empresa,
                    tipo_movimiento=TIPO_CIERRE,
                    monto=monto_cierre_usuario,
                    descripcion='Retiro por cierre de caja',
                    usuario=ejecutado_por,
                    usuario_creacion=ejecutado_por
                )

                # Actualizar sesión (DESPUÉS de crear el movimiento)
                sesion.estado = ESTADO_CERRADA
                sesion.fecha_cierre = timezone.now()
                sesion.monto_cierre_sistema = monto_sistema
                sesion.monto_cierre_usuario = monto_cierre_usuario
                sesion.diferencia = diferencia
                sesion.usuario_modificacion = ejecutado_por

                if observaciones:
                    sesion.observaciones = (sesion.observaciones or '') + f'\n{observaciones}'

                sesion.save()

            logger.info(
                f"Sesión {sesion.id} cerrada por {ejecutado_por.username}. "
                f"Sistema: {monto_sistema}, Usuario: {monto_cierre_usuario}, "
                f"Diferencia: {diferencia}"
            )
            return True, None

        except Exception as e:
            logger.error(f"Error cerrando sesión {sesion.id}: {e}")
            return False, str(e)

    @staticmethod
    def arquear_sesion(
        sesion: SesionCaja,
        ejecutado_por,
        observaciones: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Marca una sesión como arqueada (auditada/verificada).

        IDEMPOTENTE: Verifica si ya está arqueada antes de operar.

        Args:
            sesion: Sesión a arquear
            ejecutado_por: Usuario que realiza el arqueo
            observaciones: Observaciones del arqueo

        Returns:
            Tuple (exito, mensaje_error)
        """
        # IDEMPOTENCIA: Verificar si ya está arqueada
        if sesion.estado == ESTADO_ARQUEADA:
            logger.info(f"Sesión {sesion.id} ya está arqueada")
            return True, None  # Ya está arqueada (idempotente)

        if sesion.estado != ESTADO_CERRADA:
            return False, 'Solo se pueden arquear sesiones cerradas'

        try:
            sesion.estado = ESTADO_ARQUEADA
            sesion.usuario_modificacion = ejecutado_por

            if observaciones:
                sesion.observaciones = (sesion.observaciones or '') + f'\nArqueo: {observaciones}'

            sesion.save(update_fields=[
                'estado', 'observaciones', 'usuario_modificacion', 'fecha_actualizacion'
            ])

            logger.info(f"Sesión {sesion.id} arqueada por {ejecutado_por.username}")
            return True, None

        except Exception as e:
            logger.error(f"Error arqueando sesión {sesion.id}: {e}")
            return False, str(e)

    @staticmethod
    def calcular_saldo_sesion(sesion: SesionCaja) -> Decimal:
        """
        Calcula el saldo actual de una sesión.

        Args:
            sesion: Sesión de caja

        Returns:
            Saldo calculado (ingresos - egresos)
        """
        movimientos = sesion.movimientos.exclude(tipo_movimiento=TIPO_CIERRE)

        # Sumar ingresos
        ingresos = movimientos.filter(
            tipo_movimiento__in=TIPOS_INGRESO
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

        # Sumar egresos
        egresos = movimientos.filter(
            tipo_movimiento__in=TIPOS_EGRESO
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

        return ingresos - egresos

    @staticmethod
    def obtener_resumen_sesion(sesion: SesionCaja) -> Dict[str, Any]:
        """
        Obtiene un resumen detallado de una sesión.

        Args:
            sesion: Sesión de caja

        Returns:
            Diccionario con resumen de la sesión
        """
        movimientos = sesion.movimientos.all()

        resumen = {
            'sesion_id': sesion.id,
            'caja': sesion.caja.nombre,
            'usuario': sesion.usuario.username,
            'estado': sesion.estado,
            'fecha_apertura': sesion.fecha_apertura,
            'fecha_cierre': sesion.fecha_cierre,
            'monto_apertura': sesion.monto_apertura,
            'monto_cierre_sistema': sesion.monto_cierre_sistema,
            'monto_cierre_usuario': sesion.monto_cierre_usuario,
            'diferencia': sesion.diferencia,
            'saldo_actual': SesionCajaService.calcular_saldo_sesion(sesion),
            'total_movimientos': movimientos.count(),
            'movimientos_por_tipo': {},
        }

        # Agrupar movimientos por tipo
        for tipo, _ in [
            (TIPO_VENTA, 'Ventas'),
            (TIPO_INGRESO_MANUAL, 'Ingresos manuales'),
            (TIPO_RETIRO_MANUAL, 'Retiros manuales'),
            (TIPO_GASTO_MENOR, 'Gastos menores'),
        ]:
            tipo_movs = movimientos.filter(tipo_movimiento=tipo)
            resumen['movimientos_por_tipo'][tipo] = {
                'cantidad': tipo_movs.count(),
                'total': tipo_movs.aggregate(total=Sum('monto'))['total'] or Decimal('0')
            }

        return resumen


class MovimientoCajaService:
    """
    Servicio para gestionar Movimientos de Caja.
    """

    @staticmethod
    def registrar_movimiento(
        sesion: SesionCaja,
        tipo_movimiento: str,
        monto: Decimal,
        descripcion: str,
        usuario,
        referencia: str = None
    ) -> Tuple[Optional[MovimientoCaja], Optional[str]]:
        """
        Registra un nuevo movimiento en una sesión de caja.

        Args:
            sesion: Sesión de caja
            tipo_movimiento: Tipo de movimiento
            monto: Monto del movimiento
            descripcion: Descripción del movimiento
            usuario: Usuario que registra
            referencia: Referencia opcional (factura, recibo, etc.)

        Returns:
            Tuple (movimiento, mensaje_error)
        """
        # Validar que la sesión esté abierta
        if sesion.estado != ESTADO_ABIERTA:
            return None, 'No se pueden agregar movimientos a una sesión cerrada'

        # Validar monto positivo
        if monto is None or monto <= 0:
            return None, 'El monto debe ser mayor a cero'

        # Validar tipo de movimiento
        tipos_validos = [TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR]
        if tipo_movimiento not in tipos_validos:
            return None, f'Tipo de movimiento inválido. Use: {tipos_validos}'

        try:
            movimiento = MovimientoCaja.objects.create(
                sesion=sesion,
                empresa=sesion.empresa,
                tipo_movimiento=tipo_movimiento,
                monto=monto,
                descripcion=descripcion,
                referencia=referencia,
                usuario=usuario,
                usuario_creacion=usuario
            )

            logger.info(
                f"Movimiento {movimiento.id} registrado: {tipo_movimiento} "
                f"por {monto} en sesión {sesion.id}"
            )
            return movimiento, None

        except Exception as e:
            logger.error(f"Error registrando movimiento en sesión {sesion.id}: {e}")
            return None, str(e)

    @staticmethod
    def registrar_venta(
        sesion: SesionCaja,
        monto: Decimal,
        usuario,
        referencia: str = None,
        descripcion: str = 'Cobro de venta'
    ) -> Tuple[Optional[MovimientoCaja], Optional[str]]:
        """
        Registra un cobro de venta (atajo para movimiento de tipo VENTA).

        Args:
            sesion: Sesión de caja
            monto: Monto cobrado
            usuario: Usuario que registra
            referencia: Referencia (ID de factura, etc.)
            descripcion: Descripción opcional

        Returns:
            Tuple (movimiento, mensaje_error)
        """
        return MovimientoCajaService.registrar_movimiento(
            sesion=sesion,
            tipo_movimiento=TIPO_VENTA,
            monto=monto,
            descripcion=descripcion,
            usuario=usuario,
            referencia=referencia
        )

    @staticmethod
    def registrar_gasto_menor(
        sesion: SesionCaja,
        monto: Decimal,
        descripcion: str,
        usuario,
        referencia: str = None
    ) -> Tuple[Optional[MovimientoCaja], Optional[str]]:
        """
        Registra un gasto menor.

        Args:
            sesion: Sesión de caja
            monto: Monto del gasto
            descripcion: Descripción del gasto
            usuario: Usuario que registra
            referencia: Referencia opcional

        Returns:
            Tuple (movimiento, mensaje_error)
        """
        return MovimientoCajaService.registrar_movimiento(
            sesion=sesion,
            tipo_movimiento=TIPO_GASTO_MENOR,
            monto=monto,
            descripcion=descripcion,
            usuario=usuario,
            referencia=referencia
        )

    @staticmethod
    def anular_movimiento(
        movimiento: MovimientoCaja,
        ejecutado_por,
        motivo: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Anula un movimiento creando un movimiento inverso.

        Args:
            movimiento: Movimiento a anular
            ejecutado_por: Usuario que anula
            motivo: Motivo de la anulación

        Returns:
            Tuple (exito, mensaje_error)
        """
        # Validar que el movimiento sea editable
        if movimiento.tipo_movimiento in TIPOS_NO_EDITABLES:
            return False, f'Los movimientos de tipo {movimiento.tipo_movimiento} no pueden anularse'

        # Validar que la sesión esté abierta
        if movimiento.sesion.estado != ESTADO_ABIERTA:
            return False, 'No se pueden anular movimientos de una sesión cerrada'

        try:
            # Determinar el tipo inverso
            if movimiento.tipo_movimiento in TIPOS_INGRESO:
                tipo_inverso = TIPO_RETIRO_MANUAL
            else:
                tipo_inverso = TIPO_INGRESO_MANUAL

            # Crear movimiento inverso
            MovimientoCaja.objects.create(
                sesion=movimiento.sesion,
                empresa=movimiento.empresa,
                tipo_movimiento=tipo_inverso,
                monto=movimiento.monto,
                descripcion=f'Anulación: {movimiento.descripcion}. Motivo: {motivo}',
                referencia=f'ANULA-{movimiento.id}',
                usuario=ejecutado_por,
                usuario_creacion=ejecutado_por
            )

            logger.warning(
                f"Movimiento {movimiento.id} anulado por {ejecutado_por.username}. "
                f"Motivo: {motivo}"
            )
            return True, None

        except Exception as e:
            logger.error(f"Error anulando movimiento {movimiento.id}: {e}")
            return False, str(e)

    @staticmethod
    def puede_eliminar(movimiento: MovimientoCaja) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un movimiento puede ser eliminado.

        Args:
            movimiento: Movimiento a verificar

        Returns:
            Tuple (puede_eliminar, mensaje_error)
        """
        if movimiento.tipo_movimiento in TIPOS_NO_ELIMINABLES:
            return False, f'Los movimientos de tipo {movimiento.tipo_movimiento} no pueden eliminarse'

        if movimiento.sesion.estado != ESTADO_ABIERTA:
            return False, 'No se pueden eliminar movimientos de una sesión cerrada'

        return True, None

"""
Servicios de negocio para el módulo de Clientes

Este módulo contiene la lógica de negocio separada de las vistas,
siguiendo los principios SRP (Single Responsibility Principle) y
SoC (Separation of Concerns).

Todos los métodos son IDEMPOTENTES: pueden ejecutarse múltiples veces
sin efectos secundarios diferentes.
"""
import logging
from typing import Tuple, Optional, Dict, Any, List
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count

from .models import Cliente, CategoriaCliente
from .constants import LIMITE_CREDITO_DEFAULT, DESCUENTO_MIN, DESCUENTO_MAX

logger = logging.getLogger(__name__)


class ClienteService:
    """
    Servicio para gestionar operaciones de negocio relacionadas con Cliente.

    Todos los métodos son estáticos e idempotentes.
    """

    @staticmethod
    def calcular_credito_disponible(cliente: Cliente) -> Decimal:
        """
        Calcula el crédito disponible del cliente.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            cliente: Instancia de Cliente

        Returns:
            Decimal: Crédito disponible (limite_credito - saldo_pendiente)
        """
        from ventas.models import Factura

        if cliente.limite_credito == 0:
            return Decimal('0.00')  # Sin límite = sin crédito disponible calculable

        # Calcular saldo pendiente
        saldo_pendiente = Factura.objects.filter(
            cliente=cliente
        ).aggregate(
            total=Sum('monto_pendiente')
        )['total'] or Decimal('0.00')

        credito_disponible = cliente.limite_credito - saldo_pendiente
        return max(credito_disponible, Decimal('0.00'))

    @staticmethod
    def verificar_limite_credito(
        cliente: Cliente,
        monto: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el cliente puede realizar una compra a crédito con el monto dado.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            cliente: Instancia de Cliente
            monto: Monto a verificar

        Returns:
            Tuple (puede_comprar, mensaje_error)
        """
        if cliente.limite_credito == 0:
            return True, None  # Sin límite configurado, permitir

        credito_disponible = ClienteService.calcular_credito_disponible(cliente)

        if monto > credito_disponible:
            return False, (
                f'El monto ({monto}) excede el crédito disponible '
                f'({credito_disponible}) del cliente.'
            )

        return True, None

    @staticmethod
    def obtener_historial_compras(
        cliente: Cliente,
        limit: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Obtiene el historial de compras de un cliente.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            cliente: Instancia de Cliente
            limit: Límite de facturas a retornar (None = todas)

        Returns:
            Tuple (historial_dict, error)
        """
        try:
            from ventas.models import Factura

            facturas_qs = Factura.objects.filter(
                cliente=cliente
            ).select_related('vendedor').order_by('-fecha')

            if limit:
                facturas_qs = facturas_qs[:limit]

            facturas = list(facturas_qs)

            data = [{
                'id': f.id,
                'numero': f.numero_factura,
                'ncf': f.ncf,
                'fecha': f.fecha,
                'total': float(f.total),
                'estado': f.estado,
                'monto_pendiente': float(f.monto_pendiente),
                'tipo_venta': f.tipo_venta
            } for f in facturas]

            return {
                'cliente': cliente.nombre,
                'cliente_id': cliente.id,
                'total_facturas': len(data),
                'total_ventas': sum(f['total'] for f in data),
                'total_pendiente': sum(f['monto_pendiente'] for f in data),
                'facturas': data
            }, None

        except Exception as e:
            logger.error(f"Error obteniendo historial de compras: {e}")
            return {}, str(e)

    @staticmethod
    def obtener_historial_pagos(
        cliente: Cliente,
        limit: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Obtiene el historial de pagos de un cliente.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            cliente: Instancia de Cliente
            limit: Límite de pagos a retornar (None = todos)

        Returns:
            Tuple (historial_dict, error)
        """
        try:
            from ventas.models import PagoCaja

            pagos_qs = PagoCaja.objects.filter(
                cliente=cliente
            ).prefetch_related('facturas').order_by('-fecha_pago')

            if limit:
                pagos_qs = pagos_qs[:limit]

            pagos = list(pagos_qs)

            data = [{
                'id': p.id,
                'fecha': p.fecha_pago,
                'monto': float(p.monto),
                'metodo': p.metodo_pago,
                'referencia': p.referencia,
                'facturas': [f.numero_factura for f in p.facturas.all()]
            } for p in pagos]

            return {
                'cliente': cliente.nombre,
                'cliente_id': cliente.id,
                'total_pagos': len(data),
                'total_monto': sum(p['monto'] for p in data),
                'pagos': data
            }, None

        except Exception as e:
            logger.error(f"Error obteniendo historial de pagos: {e}")
            return {}, str(e)

    @staticmethod
    def obtener_resumen(cliente: Cliente) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Obtiene un resumen completo del cliente con estadísticas.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            cliente: Instancia de Cliente

        Returns:
            Tuple (resumen_dict, error)
        """
        try:
            from ventas.models import Factura, PagoCaja

            # Estadísticas de facturas
            facturas = Factura.objects.filter(cliente=cliente)
            total_facturas = facturas.count()
            total_ventas = facturas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            total_pendiente = facturas.aggregate(total=Sum('monto_pendiente'))['total'] or Decimal('0.00')

            # Estadísticas de pagos
            pagos = PagoCaja.objects.filter(cliente=cliente)
            total_pagos = pagos.count()
            total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

            # Calcular crédito disponible
            credito_disponible = None
            if cliente.limite_credito > 0:
                credito_disponible = float(cliente.limite_credito - total_pendiente)

            return {
                'cliente_id': cliente.id,
                'cliente_nombre': cliente.nombre,
                'estadisticas': {
                    'total_facturas': total_facturas,
                    'total_ventas': float(total_ventas),
                    'total_pendiente': float(total_pendiente),
                    'total_pagos': total_pagos,
                    'total_pagado': float(total_pagado),
                    'saldo_actual': float(total_pendiente),
                    'limite_credito': float(cliente.limite_credito),
                    'credito_disponible': credito_disponible
                }
            }, None

        except Exception as e:
            logger.error(f"Error obteniendo resumen de cliente: {e}")
            return {}, str(e)

    @staticmethod
    def activar_cliente(
        cliente: Cliente,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Activa un cliente.

        IDEMPOTENTE: Si el cliente ya está activo, retorna éxito sin cambios.

        Args:
            cliente: Instancia de Cliente
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, error)
        """
        # IDEMPOTENCIA: Verificar si ya está activo
        if cliente.activo:
            logger.info(f"Cliente {cliente.id} ya está activo (idempotente)")
            return True, None

        try:
            with transaction.atomic():
                cliente.activo = True
                cliente.usuario_modificacion = ejecutado_por
                cliente.save(update_fields=['activo', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(f"Cliente {cliente.id} activado por {ejecutado_por}")
            return True, None

        except Exception as e:
            logger.error(f"Error activando cliente {cliente.id}: {e}")
            return False, str(e)

    @staticmethod
    def desactivar_cliente(
        cliente: Cliente,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Desactiva un cliente.

        IDEMPOTENTE: Si el cliente ya está inactivo, retorna éxito sin cambios.

        Args:
            cliente: Instancia de Cliente
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, error)
        """
        # IDEMPOTENCIA: Verificar si ya está inactivo
        if not cliente.activo:
            logger.info(f"Cliente {cliente.id} ya está inactivo (idempotente)")
            return True, None

        try:
            with transaction.atomic():
                cliente.activo = False
                cliente.usuario_modificacion = ejecutado_por
                cliente.save(update_fields=['activo', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(f"Cliente {cliente.id} desactivado por {ejecutado_por}")
            return True, None

        except Exception as e:
            logger.error(f"Error desactivando cliente {cliente.id}: {e}")
            return False, str(e)

    @staticmethod
    def actualizar_limite_credito(
        cliente: Cliente,
        nuevo_limite: Decimal,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Actualiza el límite de crédito de un cliente.

        IDEMPOTENTE: Si el límite ya es el mismo, retorna éxito sin cambios.

        Args:
            cliente: Instancia de Cliente
            nuevo_limite: Nuevo límite de crédito
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, error)
        """
        # Validar límite no negativo
        if nuevo_limite < 0:
            return False, 'El límite de crédito no puede ser negativo.'

        # IDEMPOTENCIA: Verificar si el límite ya es el mismo
        if cliente.limite_credito == nuevo_limite:
            logger.info(f"Cliente {cliente.id} ya tiene límite {nuevo_limite} (idempotente)")
            return True, None

        try:
            with transaction.atomic():
                limite_anterior = cliente.limite_credito
                cliente.limite_credito = nuevo_limite
                cliente.usuario_modificacion = ejecutado_por
                cliente.save(update_fields=['limite_credito', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(
                f"Límite de crédito de cliente {cliente.id} actualizado: "
                f"{limite_anterior} -> {nuevo_limite} por {ejecutado_por}"
            )
            return True, None

        except Exception as e:
            logger.error(f"Error actualizando límite de crédito: {e}")
            return False, str(e)


class CategoriaClienteService:
    """
    Servicio para gestionar operaciones de negocio relacionadas con CategoriaCliente.

    Todos los métodos son estáticos e idempotentes.
    """

    @staticmethod
    def aplicar_descuento(
        categoria: Optional[CategoriaCliente],
        monto: Decimal
    ) -> Decimal:
        """
        Aplica el descuento de la categoría a un monto.

        IDEMPOTENTE: Solo cálculo, no modifica datos.

        Args:
            categoria: Instancia de CategoriaCliente (puede ser None)
            monto: Monto al que aplicar descuento

        Returns:
            Decimal: Monto con descuento aplicado
        """
        if not categoria or not categoria.activa:
            return monto

        if categoria.descuento_porcentaje <= 0:
            return monto

        descuento = monto * (categoria.descuento_porcentaje / 100)
        return monto - descuento

    @staticmethod
    def calcular_descuento(
        categoria: Optional[CategoriaCliente],
        monto: Decimal
    ) -> Decimal:
        """
        Calcula el monto de descuento de la categoría.

        IDEMPOTENTE: Solo cálculo, no modifica datos.

        Args:
            categoria: Instancia de CategoriaCliente (puede ser None)
            monto: Monto base

        Returns:
            Decimal: Monto del descuento
        """
        if not categoria or not categoria.activa:
            return Decimal('0.00')

        if categoria.descuento_porcentaje <= 0:
            return Decimal('0.00')

        return monto * (categoria.descuento_porcentaje / 100)

    @staticmethod
    def obtener_estadisticas(
        categoria: CategoriaCliente
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Obtiene estadísticas de una categoría de clientes.

        IDEMPOTENTE: Solo lectura, no modifica datos.

        Args:
            categoria: Instancia de CategoriaCliente

        Returns:
            Tuple (estadisticas_dict, error)
        """
        try:
            clientes = Cliente.objects.filter(categoria=categoria)

            total_clientes = clientes.count()
            clientes_activos = clientes.filter(activo=True).count()
            clientes_inactivos = clientes.filter(activo=False).count()

            return {
                'categoria_id': categoria.id,
                'categoria_nombre': categoria.nombre,
                'descuento_porcentaje': float(categoria.descuento_porcentaje),
                'total_clientes': total_clientes,
                'clientes_activos': clientes_activos,
                'clientes_inactivos': clientes_inactivos
            }, None

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de categoría: {e}")
            return {}, str(e)

    @staticmethod
    def activar_categoria(
        categoria: CategoriaCliente,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Activa una categoría de clientes.

        IDEMPOTENTE: Si ya está activa, retorna éxito sin cambios.

        Args:
            categoria: Instancia de CategoriaCliente
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, error)
        """
        # IDEMPOTENCIA: Verificar si ya está activa
        if categoria.activa:
            logger.info(f"Categoría {categoria.id} ya está activa (idempotente)")
            return True, None

        try:
            with transaction.atomic():
                categoria.activa = True
                categoria.usuario_modificacion = ejecutado_por
                categoria.save(update_fields=['activa', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(f"Categoría {categoria.id} activada por {ejecutado_por}")
            return True, None

        except Exception as e:
            logger.error(f"Error activando categoría: {e}")
            return False, str(e)

    @staticmethod
    def desactivar_categoria(
        categoria: CategoriaCliente,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Desactiva una categoría de clientes.

        IDEMPOTENTE: Si ya está inactiva, retorna éxito sin cambios.

        Args:
            categoria: Instancia de CategoriaCliente
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, error)
        """
        # IDEMPOTENCIA: Verificar si ya está inactiva
        if not categoria.activa:
            logger.info(f"Categoría {categoria.id} ya está inactiva (idempotente)")
            return True, None

        try:
            with transaction.atomic():
                categoria.activa = False
                categoria.usuario_modificacion = ejecutado_por
                categoria.save(update_fields=['activa', 'usuario_modificacion', 'fecha_actualizacion'])

            logger.info(f"Categoría {categoria.id} desactivada por {ejecutado_por}")
            return True, None

        except Exception as e:
            logger.error(f"Error desactivando categoría: {e}")
            return False, str(e)

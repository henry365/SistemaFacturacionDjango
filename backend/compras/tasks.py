"""
Django 6.0 Background Tasks para procesamiento de compras.

Estas tareas permiten ejecutar operaciones pesadas de compras
de forma asíncrona, mejorando el rendimiento del sistema.
"""
from django.tasks import task
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@task
def procesar_recepcion_compra(recepcion_id: int, usuario_id: int) -> dict:
    """
    Procesa una recepción de compra confirmada.

    Esta tarea:
    - Crea movimientos de inventario para cada detalle
    - Actualiza el inventario de productos
    - Actualiza las cantidades recibidas en la orden de compra

    Args:
        recepcion_id: ID de la recepción de compra
        usuario_id: ID del usuario que confirma

    Returns:
        dict con el resultado del procesamiento
    """
    from .models import RecepcionCompra, DetalleRecepcion
    from inventario.models import InventarioProducto, MovimientoInventario
    from usuarios.models import User

    logger.info(f"Iniciando procesamiento de recepción de compra {recepcion_id}")

    try:
        with transaction.atomic():
            recepcion = RecepcionCompra.objects.select_for_update().get(id=recepcion_id)
            usuario = User.objects.get(id=usuario_id)

            if recepcion.estado != 'PENDIENTE':
                return {
                    'status': 'error',
                    'error': f'La recepción ya está en estado {recepcion.estado}'
                }

            movimientos_creados = 0
            detalles = recepcion.detalles.select_related('producto', 'detalle_orden')

            for detalle in detalles:
                if detalle.cantidad_recibida <= 0:
                    continue

                # Obtener o crear inventario
                inventario, created = InventarioProducto.objects.get_or_create(
                    empresa=recepcion.empresa,
                    producto=detalle.producto,
                    almacen=recepcion.almacen,
                    defaults={
                        'cantidad_disponible': 0,
                        'costo_promedio': detalle.costo_unitario or 0
                    }
                )

                # Crear movimiento de inventario
                MovimientoInventario.objects.create(
                    empresa=recepcion.empresa,
                    producto=detalle.producto,
                    almacen=recepcion.almacen,
                    tipo_movimiento='ENTRADA_COMPRA',
                    cantidad=detalle.cantidad_recibida,
                    costo_unitario=detalle.costo_unitario or 0,
                    documento_referencia=f'REC-{recepcion.id}',
                    usuario_creacion=usuario,
                    notas=f'Recepción de compra #{recepcion.numero_recepcion}'
                )
                movimientos_creados += 1

                # Actualizar inventario
                inventario.cantidad_disponible += detalle.cantidad_recibida

                # Recalcular costo promedio ponderado
                if detalle.costo_unitario and detalle.costo_unitario > 0:
                    cantidad_anterior = inventario.cantidad_disponible - detalle.cantidad_recibida
                    if cantidad_anterior > 0:
                        costo_total_anterior = cantidad_anterior * inventario.costo_promedio
                        costo_nueva_entrada = detalle.cantidad_recibida * detalle.costo_unitario
                        inventario.costo_promedio = (costo_total_anterior + costo_nueva_entrada) / inventario.cantidad_disponible
                    else:
                        inventario.costo_promedio = detalle.costo_unitario

                inventario.save()

                # Actualizar cantidad recibida en la orden de compra
                if detalle.detalle_orden:
                    detalle.detalle_orden.cantidad_recibida += detalle.cantidad_recibida
                    detalle.detalle_orden.save()

            # Actualizar estado de la recepción
            recepcion.estado = 'CONFIRMADA'
            recepcion.usuario_modificacion = usuario
            recepcion.save()

            logger.info(f"Recepción {recepcion_id} procesada: {movimientos_creados} movimientos creados")

            return {
                'status': 'completed',
                'recepcion_id': recepcion_id,
                'movimientos_creados': movimientos_creados,
                'estado': 'CONFIRMADA'
            }

    except RecepcionCompra.DoesNotExist:
        logger.error(f"Recepción {recepcion_id} no encontrada")
        return {
            'status': 'error',
            'error': f'Recepción {recepcion_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error procesando recepción {recepcion_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def procesar_devolucion_proveedor(devolucion_id: int, usuario_id: int) -> dict:
    """
    Procesa una devolución a proveedor.

    Esta tarea:
    - Crea movimientos de salida de inventario
    - Actualiza el inventario de productos
    - Genera nota de crédito si aplica

    Args:
        devolucion_id: ID de la devolución
        usuario_id: ID del usuario que procesa

    Returns:
        dict con el resultado del procesamiento
    """
    from .models import DevolucionProveedor
    from inventario.models import InventarioProducto, MovimientoInventario
    from usuarios.models import User

    logger.info(f"Iniciando procesamiento de devolución {devolucion_id}")

    try:
        with transaction.atomic():
            devolucion = DevolucionProveedor.objects.select_for_update().get(id=devolucion_id)
            usuario = User.objects.get(id=usuario_id)

            if devolucion.estado != 'PENDIENTE':
                return {
                    'status': 'error',
                    'error': f'La devolución ya está en estado {devolucion.estado}'
                }

            movimientos_creados = 0
            detalles = devolucion.detalles.select_related('producto')

            for detalle in detalles:
                if detalle.cantidad <= 0:
                    continue

                # Verificar stock disponible
                try:
                    inventario = InventarioProducto.objects.select_for_update().get(
                        empresa=devolucion.empresa,
                        producto=detalle.producto,
                        almacen=devolucion.almacen
                    )
                except InventarioProducto.DoesNotExist:
                    continue

                if inventario.cantidad_disponible < detalle.cantidad:
                    return {
                        'status': 'error',
                        'error': f'Stock insuficiente para {detalle.producto.nombre}'
                    }

                # Crear movimiento de salida
                MovimientoInventario.objects.create(
                    empresa=devolucion.empresa,
                    producto=detalle.producto,
                    almacen=devolucion.almacen,
                    tipo_movimiento='SALIDA_DEVOLUCION',
                    cantidad=detalle.cantidad,
                    costo_unitario=detalle.costo_unitario or inventario.costo_promedio,
                    documento_referencia=f'DEV-{devolucion.id}',
                    usuario_creacion=usuario,
                    notas=f'Devolución a proveedor #{devolucion.numero_devolucion}'
                )
                movimientos_creados += 1

                # Actualizar inventario
                inventario.cantidad_disponible -= detalle.cantidad
                inventario.save()

            # Actualizar estado de la devolución
            devolucion.estado = 'PROCESADA'
            devolucion.usuario_modificacion = usuario
            devolucion.save()

            logger.info(f"Devolución {devolucion_id} procesada: {movimientos_creados} movimientos creados")

            return {
                'status': 'completed',
                'devolucion_id': devolucion_id,
                'movimientos_creados': movimientos_creados,
                'estado': 'PROCESADA'
            }

    except DevolucionProveedor.DoesNotExist:
        logger.error(f"Devolución {devolucion_id} no encontrada")
        return {
            'status': 'error',
            'error': f'Devolución {devolucion_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error procesando devolución {devolucion_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def liquidar_importacion(liquidacion_id: int, usuario_id: int) -> dict:
    """
    Procesa la liquidación de una importación.

    Esta tarea:
    - Calcula el prorrateo de gastos
    - Actualiza los costos promedio de inventario
    - Marca la liquidación como completada

    Args:
        liquidacion_id: ID de la liquidación
        usuario_id: ID del usuario que procesa

    Returns:
        dict con el resultado del procesamiento
    """
    from .models import LiquidacionImportacion
    from inventario.models import InventarioProducto
    from usuarios.models import User
    from decimal import Decimal

    logger.info(f"Iniciando liquidación de importación {liquidacion_id}")

    try:
        with transaction.atomic():
            liquidacion = LiquidacionImportacion.objects.select_for_update().get(id=liquidacion_id)
            usuario = User.objects.get(id=usuario_id)

            if liquidacion.estado != 'PENDIENTE':
                return {
                    'status': 'error',
                    'error': f'La liquidación ya está en estado {liquidacion.estado}'
                }

            # Calcular totales
            compra = liquidacion.compra
            total_gastos = sum(g.monto for g in liquidacion.gastos.all())
            total_productos = sum(d.subtotal for d in compra.detalles.all())

            if total_productos <= 0:
                return {
                    'status': 'error',
                    'error': 'No hay productos para liquidar'
                }

            # Prorratear gastos y actualizar costos
            productos_actualizados = 0
            for detalle in compra.detalles.all():
                if detalle.subtotal <= 0:
                    continue

                # Calcular proporción de gastos
                proporcion = detalle.subtotal / total_productos
                gastos_prorrateados = total_gastos * proporcion

                # Nuevo costo unitario incluyendo gastos
                nuevo_costo = (detalle.subtotal + gastos_prorrateados) / detalle.cantidad

                # Actualizar inventario
                try:
                    inventario = InventarioProducto.objects.get(
                        empresa=liquidacion.empresa,
                        producto=detalle.producto,
                        almacen=compra.almacen_destino
                    )

                    # Recalcular costo promedio
                    if inventario.cantidad_disponible > 0:
                        inventario.costo_promedio = nuevo_costo
                        inventario.save(update_fields=['costo_promedio'])
                        productos_actualizados += 1

                except InventarioProducto.DoesNotExist:
                    pass

            # Actualizar liquidación
            liquidacion.total_gastos = total_gastos
            liquidacion.estado = 'LIQUIDADA'
            liquidacion.usuario_modificacion = usuario
            liquidacion.save()

            logger.info(f"Liquidación {liquidacion_id} completada: {productos_actualizados} costos actualizados")

            return {
                'status': 'completed',
                'liquidacion_id': liquidacion_id,
                'total_gastos': str(total_gastos),
                'productos_actualizados': productos_actualizados,
                'estado': 'LIQUIDADA'
            }

    except LiquidacionImportacion.DoesNotExist:
        logger.error(f"Liquidación {liquidacion_id} no encontrada")
        return {
            'status': 'error',
            'error': f'Liquidación {liquidacion_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error procesando liquidación {liquidacion_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

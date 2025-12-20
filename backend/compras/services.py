"""
Servicios de negocio para el módulo de Compras.

Este módulo implementa el principio SRP (Single Responsibility Principle)
extrayendo la lógica de negocio de los ViewSets a servicios reutilizables.

Servicios disponibles:
- ServicioCompras: Operaciones generales de compras
- ServicioRecepciones: Confirmar y procesar recepciones de compra
- ServicioDevoluciones: Confirmar devoluciones a proveedores
- ServicioLiquidaciones: Liquidar importaciones y prorratear gastos
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Imports diferidos para evitar imports circulares
def get_inventario_models():
    from inventario.models import MovimientoInventario, InventarioProducto, Almacen
    return MovimientoInventario, InventarioProducto, Almacen

def get_inventario_service():
    from inventario.services import ServicioInventario
    return ServicioInventario

def get_cuentas_pagar_models():
    from cuentas_pagar.models import CuentaPorPagar
    return CuentaPorPagar


class ServicioCompras:
    """Servicio principal para operaciones de compras"""
    
    @staticmethod
    @transaction.atomic
    def procesar_compra(compra, usuario, almacen=None):
        """
        Procesa una compra registrando movimientos de inventario para productos almacenables.
        
        Args:
            compra: Instancia de Compra
            usuario: Usuario que procesa la compra
            almacen: Almacén donde se recibirá el inventario (opcional, usa el primero de la empresa si no se proporciona)
        """
        if compra.estado != 'REGISTRADA':
            raise ValidationError(f"No se puede procesar una compra con estado {compra.estado}. Debe estar en estado REGISTRADA.")
        
        # Obtener almacén si no se proporciona
        _, _, Almacen = get_inventario_models()
        if not almacen:
            almacenes = Almacen.objects.filter(empresa=compra.empresa, activo=True)
            if not almacenes.exists():
                raise ValidationError("No hay almacenes activos disponibles para esta empresa.")
            almacen = almacenes.first()
        
        # Verificar que el almacén pertenezca a la misma empresa
        if almacen.empresa != compra.empresa:
            raise ValidationError("El almacén debe pertenecer a la misma empresa de la compra.")
        
        # Registrar movimientos de inventario solo para productos almacenables
        ServicioInventario = get_inventario_service()
        movimientos_registrados = []
        for detalle in compra.detalles.all():
            if detalle.tipo_linea == 'ALMACENABLE':
                try:
                    movimiento = ServicioInventario.registrar_movimiento(
                        producto=detalle.producto,
                        almacen=almacen,
                        tipo_movimiento='ENTRADA_COMPRA',
                        cantidad=detalle.cantidad,
                        costo_unitario=detalle.costo_unitario,
                        usuario=usuario,
                        empresa=compra.empresa,
                        referencia=f"COMP-{compra.numero_factura_proveedor}",
                        notas=f"Compra #{compra.numero_factura_proveedor} - Proveedor: {compra.proveedor.nombre}"
                    )
                    # Actualizar el movimiento con referencia al documento origen
                    movimiento.tipo_documento_origen = 'COMPRA'
                    movimiento.documento_origen_id = compra.id
                    movimiento.save()
                    movimientos_registrados.append(movimiento)
                except Exception as e:
                    raise ValidationError(f"Error al registrar movimiento para producto {detalle.producto.nombre}: {str(e)}")
        
        # Cambiar estado de la compra
        compra.estado = 'CXP'
        compra.usuario_modificacion = usuario
        compra.save()
        
        return movimientos_registrados
    
    @staticmethod
    @transaction.atomic
    def anular_compra(compra, usuario):
        """
        Anula una compra y revierte los movimientos de inventario si existen.
        
        Args:
            compra: Instancia de Compra
            usuario: Usuario que anula la compra
        """
        if compra.estado == 'ANULADA':
            raise ValidationError("La compra ya está anulada.")
        
        if compra.estado == 'PAGADA':
            raise ValidationError("No se puede anular una compra que ya está pagada.")
        
        # Buscar movimientos de inventario relacionados con esta compra
        from inventario.models import MovimientoInventario
        movimientos = MovimientoInventario.objects.filter(
            empresa=compra.empresa,
            tipo_documento_origen='COMPRA',
            documento_origen_id=compra.id,
            tipo_movimiento='ENTRADA_COMPRA'
        )
        
        # Revertir movimientos (crear movimientos de salida)
        ServicioInventario = get_inventario_service()
        for movimiento_original in movimientos:
            try:
                ServicioInventario.registrar_movimiento(
                    producto=movimiento_original.producto,
                    almacen=movimiento_original.almacen,
                    tipo_movimiento='SALIDA_AJUSTE',
                    cantidad=movimiento_original.cantidad,
                    costo_unitario=movimiento_original.costo_unitario,
                    usuario=usuario,
                    empresa=compra.empresa,
                    referencia=f"ANUL-{compra.numero_factura_proveedor}",
                    notas=f"Anulación de compra #{compra.numero_factura_proveedor}"
                )
            except Exception as e:
                raise ValidationError(f"Error al revertir movimiento para producto {movimiento_original.producto.nombre}: {str(e)}")
        
        # Cambiar estado de la compra
        compra.estado = 'ANULADA'
        compra.usuario_modificacion = usuario
        compra.save()
    
    @staticmethod
    @transaction.atomic
    def recibir_orden_compra(orden_compra, detalles_recibidos, usuario, almacen=None):
        """
        Recibe una orden de compra actualizando las cantidades recibidas.
        Puede crear movimientos de inventario si se especifica.
        
        Args:
            orden_compra: Instancia de OrdenCompra
            detalles_recibidos: Dict con {detalle_id: cantidad_recibida}
            usuario: Usuario que recibe la orden
            almacen: Almacén donde se recibirá (opcional)
        """
        if orden_compra.estado not in ['APROBADA', 'ENVIADA', 'RECIBIDA_PARCIAL']:
            raise ValidationError(f"No se puede recibir una orden con estado {orden_compra.estado}.")
        
        # Actualizar cantidades recibidas
        total_recibido = 0
        total_solicitado = 0
        
        for detalle in orden_compra.detalles.all():
            cantidad_recibida = detalles_recibidos.get(detalle.id, detalle.cantidad_recibida)
            if cantidad_recibida > detalle.cantidad:
                raise ValidationError(f"La cantidad recibida ({cantidad_recibida}) no puede ser mayor que la solicitada ({detalle.cantidad}) para el producto {detalle.producto.nombre}.")
            
            detalle.cantidad_recibida = cantidad_recibida
            detalle.save()
            
            total_recibido += cantidad_recibida
            total_solicitado += detalle.cantidad
        
        # Actualizar estado según cantidades recibidas
        if total_recibido == 0:
            raise ValidationError("Debe recibir al menos una cantidad de algún producto.")
        elif total_recibido >= total_solicitado:
            orden_compra.estado = 'RECIBIDA_TOTAL'
        else:
            orden_compra.estado = 'RECIBIDA_PARCIAL'
        
        orden_compra.usuario_modificacion = usuario
        orden_compra.save()

        return orden_compra


class ServicioRecepciones:
    """
    Servicio para procesar recepciones de compra.

    Responsabilidades:
    - Confirmar recepciones y actualizar inventario
    - Crear movimientos de inventario
    - Actualizar estado de órdenes de compra
    """

    @staticmethod
    @transaction.atomic
    def confirmar_recepcion(recepcion, usuario):
        """
        Confirma una recepción de compra y actualiza el inventario.

        Args:
            recepcion: Instancia de RecepcionCompra
            usuario: Usuario que confirma la recepción

        Returns:
            dict con resultado de la operación

        Raises:
            ValidationError: Si la recepción no puede ser confirmada
        """
        MovimientoInventario, InventarioProducto, _ = get_inventario_models()

        # Validar estado
        if recepcion.estado not in ['PENDIENTE', 'PARCIAL']:
            raise ValidationError(
                'Solo se pueden confirmar recepciones en estado PENDIENTE o PARCIAL'
            )

        movimientos_creados = 0

        for detalle in recepcion.detalles.all():
            if detalle.cantidad_recibida <= 0:
                continue

            # Crear movimiento de inventario
            MovimientoInventario.objects.create(
                empresa=recepcion.empresa,
                almacen=recepcion.almacen,
                producto=detalle.producto,
                tipo_movimiento='ENTRADA_COMPRA',
                cantidad=detalle.cantidad_recibida,
                referencia=f"Recepción {recepcion.numero_recepcion}",
                usuario=usuario,
                usuario_creacion=usuario
            )
            movimientos_creados += 1

            # Obtener costo unitario
            costo_unitario = getattr(detalle, 'costo_unitario', None)
            if not costo_unitario and hasattr(detalle, 'detalle_orden'):
                costo_unitario = detalle.detalle_orden.costo_unitario

            # Actualizar o crear inventario
            inventario, created = InventarioProducto.objects.get_or_create(
                empresa=recepcion.empresa,
                almacen=recepcion.almacen,
                producto=detalle.producto,
                defaults={
                    'cantidad_disponible': 0,
                    'costo_promedio': costo_unitario or Decimal('0')
                }
            )

            # Recalcular costo promedio ponderado
            if costo_unitario and costo_unitario > 0 and inventario.cantidad_disponible > 0:
                costo_total_anterior = inventario.cantidad_disponible * inventario.costo_promedio
                costo_nueva_entrada = detalle.cantidad_recibida * costo_unitario
                nueva_cantidad = inventario.cantidad_disponible + detalle.cantidad_recibida
                inventario.costo_promedio = (costo_total_anterior + costo_nueva_entrada) / nueva_cantidad

            inventario.cantidad_disponible += detalle.cantidad_recibida
            inventario.save()

            # Actualizar cantidad recibida en la orden de compra
            if hasattr(detalle, 'detalle_orden') and detalle.detalle_orden:
                detalle.detalle_orden.cantidad_recibida += detalle.cantidad_recibida
                detalle.detalle_orden.save()

        # Verificar si la orden está completamente recibida
        orden = recepcion.orden_compra
        total_ordenado = sum(d.cantidad for d in orden.detalles.all())
        total_recibido = sum(d.cantidad_recibida for d in orden.detalles.all())

        if total_recibido >= total_ordenado:
            orden.estado = 'RECIBIDA_TOTAL'
            recepcion.estado = 'COMPLETA'
        else:
            orden.estado = 'RECIBIDA_PARCIAL'
            recepcion.estado = 'PARCIAL'

        orden.usuario_modificacion = usuario
        orden.save()
        recepcion.usuario_modificacion = usuario
        recepcion.save()

        logger.info(
            f"Recepción {recepcion.numero_recepcion} confirmada: "
            f"{movimientos_creados} movimientos creados"
        )

        return {
            'recepcion': recepcion,
            'movimientos_creados': movimientos_creados,
            'estado_orden': orden.estado
        }


class ServicioDevoluciones:
    """
    Servicio para procesar devoluciones a proveedores.

    Responsabilidades:
    - Confirmar devoluciones y registrar salida de inventario
    - Verificar disponibilidad de stock
    - Ajustar cuentas por pagar si aplica
    """

    @staticmethod
    @transaction.atomic
    def confirmar_devolucion(devolucion, usuario):
        """
        Confirma una devolución a proveedor y registra salida de inventario.

        Args:
            devolucion: Instancia de DevolucionProveedor
            usuario: Usuario que confirma

        Returns:
            dict con resultado de la operación

        Raises:
            ValidationError: Si no hay stock suficiente o estado inválido
        """
        MovimientoInventario, InventarioProducto, _ = get_inventario_models()

        # Validar estado
        if devolucion.estado != 'BORRADOR':
            raise ValidationError(
                'Solo se pueden confirmar devoluciones en estado BORRADOR'
            )

        movimientos_creados = 0

        for detalle in devolucion.detalles.all():
            # Obtener almacén del detalle o de la devolución
            almacen = getattr(detalle, 'almacen', None) or devolucion.almacen

            # Verificar stock disponible
            inventario = InventarioProducto.objects.filter(
                empresa=devolucion.empresa,
                almacen=almacen,
                producto=detalle.producto
            ).first()

            if not inventario or inventario.cantidad_disponible < detalle.cantidad:
                raise ValidationError(
                    f'Stock insuficiente para {detalle.producto.nombre}'
                )

            # Crear movimiento de inventario (salida)
            # Nota: cantidad es positiva, el tipo_movimiento indica la dirección
            MovimientoInventario.objects.create(
                empresa=devolucion.empresa,
                almacen=almacen,
                producto=detalle.producto,
                tipo_movimiento='DEVOLUCION_PROVEEDOR',
                cantidad=detalle.cantidad,
                referencia=f"Devolución {devolucion.numero_devolucion}",
                usuario=usuario,
                usuario_creacion=usuario
            )
            movimientos_creados += 1

            # Actualizar inventario
            inventario.cantidad_disponible -= detalle.cantidad
            inventario.save()

        # Actualizar totales y estado
        if hasattr(devolucion, 'calcular_totales'):
            devolucion.calcular_totales()

        devolucion.estado = 'CONFIRMADA'
        devolucion.usuario_modificacion = usuario
        devolucion.save()

        # Si genera nota de crédito, ajustar CxP
        ajuste_cxp = None
        if devolucion.genera_nota_credito and devolucion.compra:
            ajuste_cxp = ServicioDevoluciones._ajustar_cuenta_por_pagar(devolucion)

        logger.info(
            f"Devolución {devolucion.numero_devolucion} confirmada: "
            f"{movimientos_creados} movimientos creados"
        )

        return {
            'devolucion': devolucion,
            'movimientos_creados': movimientos_creados,
            'ajuste_cxp': ajuste_cxp
        }

    @staticmethod
    def _ajustar_cuenta_por_pagar(devolucion):
        """Ajusta la cuenta por pagar asociada a la compra."""
        CuentaPorPagar = get_cuentas_pagar_models()

        cxp = CuentaPorPagar.objects.filter(compra=devolucion.compra).first()
        if cxp:
            monto_anterior = cxp.monto_pendiente
            cxp.monto_pendiente -= devolucion.total
            if cxp.monto_pendiente <= 0:
                cxp.monto_pendiente = 0
                cxp.estado = 'PAGADA'
            cxp.save()

            return {
                'cxp_id': cxp.id,
                'monto_anterior': monto_anterior,
                'monto_nuevo': cxp.monto_pendiente
            }
        return None


class ServicioLiquidaciones:
    """
    Servicio para liquidar importaciones.

    Responsabilidades:
    - Calcular prorrateo de gastos entre productos
    - Actualizar costos promedio en inventario
    - Aplicar tasa de cambio
    """

    @staticmethod
    @transaction.atomic
    def liquidar_importacion(liquidacion, usuario):
        """
        Liquida una importación y actualiza los costos en inventario.

        Args:
            liquidacion: Instancia de LiquidacionImportacion
            usuario: Usuario que liquida

        Returns:
            dict con resultado de la operación

        Raises:
            ValidationError: Si no se puede liquidar
        """
        _, InventarioProducto, _ = get_inventario_models()

        # Validar estado
        if liquidacion.estado != 'BORRADOR':
            raise ValidationError(
                'Solo se pueden liquidar importaciones en estado BORRADOR'
            )

        # Calcular totales
        if hasattr(liquidacion, 'calcular_totales'):
            liquidacion.calcular_totales()

        # Obtener detalles de la compra
        detalles_compra = liquidacion.compra.detalles.all()
        total_valor_fob = sum(
            d.cantidad * d.costo_unitario for d in detalles_compra
        )

        if total_valor_fob <= 0:
            raise ValidationError('El valor FOB total debe ser mayor a cero')

        productos_actualizados = 0

        for detalle in detalles_compra:
            if detalle.cantidad <= 0:
                continue

            # Calcular costo unitario nacionalizado
            costo_unitario_nacionalizado = ServicioLiquidaciones._calcular_costo_nacionalizado(
                detalle=detalle,
                total_valor_fob=total_valor_fob,
                total_gastos=liquidacion.total_gastos
            )

            # Actualizar costo promedio en inventario
            inventarios = InventarioProducto.objects.filter(
                empresa=liquidacion.empresa,
                producto=detalle.producto
            )

            for inv in inventarios:
                if inv.cantidad_disponible > 0:
                    costo_actual_total = inv.cantidad_disponible * inv.costo_promedio
                    costo_nuevo_total = detalle.cantidad * costo_unitario_nacionalizado
                    inv.costo_promedio = (
                        (costo_actual_total + costo_nuevo_total) /
                        (inv.cantidad_disponible + detalle.cantidad)
                    )
                    inv.save()
                    productos_actualizados += 1

        liquidacion.estado = 'LIQUIDADA'
        liquidacion.usuario_modificacion = usuario
        liquidacion.save()

        logger.info(
            f"Liquidación {liquidacion.numero_liquidacion} completada: "
            f"{productos_actualizados} productos actualizados"
        )

        return {
            'liquidacion': liquidacion,
            'productos_actualizados': productos_actualizados,
            'total_gastos': liquidacion.total_gastos
        }

    @staticmethod
    def _calcular_costo_nacionalizado(detalle, total_valor_fob, total_gastos):
        """
        Calcula el costo unitario nacionalizado de un producto.

        Fórmula:
        costo_nacionalizado = (valor_fob + gasto_prorrateado) / cantidad
        """
        valor_fob_linea = detalle.cantidad * detalle.costo_unitario
        proporcion = valor_fob_linea / total_valor_fob
        gasto_prorrateado = total_gastos * proporcion
        costo_total_linea = valor_fob_linea + gasto_prorrateado

        return costo_total_linea / detalle.cantidad


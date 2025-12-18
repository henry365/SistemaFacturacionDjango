"""
Django 6.0 Background Tasks para gestión de inventario.

Estas tareas permiten ejecutar operaciones pesadas de inventario
de forma asíncrona, mejorando el rendimiento del sistema.

KISS Principle: La lógica de negocio está delegada a ServicioAlertasInventario
para evitar código duplicado y funciones largas.
"""
from django.tasks import task
import logging

logger = logging.getLogger(__name__)


@task
def generar_alertas_inventario(empresa_id: int = None) -> dict:
    """
    Genera todas las alertas de inventario.

    Delega la lógica a ServicioAlertasInventario para mantener
    el principio KISS y evitar funciones largas.

    Args:
        empresa_id: ID de la empresa (opcional, si no se especifica genera para todas)

    Returns:
        dict con el resumen de alertas generadas
    """
    from .services import ServicioAlertasInventario

    logger.info(f"Iniciando generación de alertas de inventario")

    try:
        resultado = ServicioAlertasInventario.generar_todas_las_alertas()

        logger.info(
            f"Alertas de inventario generadas: {resultado['total']} "
            f"(bajo: {resultado['stock_bajo']}, "
            f"vencimiento: {resultado['vencimientos']}, "
            f"excesivo: {resultado['stock_excesivo']})"
        )

        return {
            'status': 'completed',
            'alertas_creadas': resultado,
            'total': resultado['total']
        }

    except Exception as e:
        logger.error(f"Error generando alertas de inventario: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def recalcular_costos_promedio(empresa_id: int, producto_id: int = None) -> dict:
    """
    Recalcula los costos promedio ponderado de inventario.

    Args:
        empresa_id: ID de la empresa
        producto_id: ID del producto (opcional, si no se especifica recalcula todos)

    Returns:
        dict con el resumen del recálculo
    """
    from empresas.models import Empresa
    from .models import InventarioProducto, MovimientoInventario
    from django.db.models import Sum, F
    from decimal import Decimal

    logger.info(f"Iniciando recálculo de costos promedio para empresa {empresa_id}")

    try:
        empresa = Empresa.objects.get(id=empresa_id)

        filtros = {'empresa': empresa}
        if producto_id:
            filtros['producto_id'] = producto_id

        inventarios = InventarioProducto.objects.filter(**filtros)
        actualizados = 0

        for inv in inventarios:
            # Calcular costo promedio ponderado basado en movimientos de entrada
            entradas = MovimientoInventario.objects.filter(
                empresa=empresa,
                producto=inv.producto,
                almacen=inv.almacen,
                tipo_movimiento__in=['ENTRADA_COMPRA', 'ENTRADA_INICIAL', 'AJUSTE_ENTRADA']
            ).aggregate(
                total_cantidad=Sum('cantidad'),
                total_valor=Sum(F('cantidad') * F('costo_unitario'))
            )

            if entradas['total_cantidad'] and entradas['total_cantidad'] > 0:
                nuevo_costo = entradas['total_valor'] / entradas['total_cantidad']
                if inv.costo_promedio != nuevo_costo:
                    inv.costo_promedio = nuevo_costo
                    inv.save(update_fields=['costo_promedio'])
                    actualizados += 1

        logger.info(f"Costos promedio recalculados: {actualizados} inventarios actualizados")

        return {
            'status': 'completed',
            'empresa_id': empresa_id,
            'inventarios_actualizados': actualizados
        }

    except Exception as e:
        logger.error(f"Error recalculando costos promedio: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

"""
Django 6.0 Background Tasks para reportes DGII.

Estas tareas permiten generar reportes fiscales de forma asíncrona,
evitando bloquear el servidor durante la generación de reportes grandes.

KISS Principle: La lógica de negocio está delegada a GeneradorReportesDGII
para evitar código duplicado y funciones largas.
"""
from django.tasks import task
import logging

logger = logging.getLogger(__name__)


@task
def generar_reporte_606(empresa_id: int, anio: int, mes: int) -> dict:
    """
    Genera el reporte 606 de compras de bienes y servicios.

    Delega la lógica a GeneradorReportesDGII para mantener
    el principio KISS y evitar funciones largas.
    """
    from empresas.models import Empresa
    from .services import GeneradorReportesDGII

    logger.info(f"Iniciando generación de reporte 606 para empresa {empresa_id}, período {anio}-{mes:02d}")

    try:
        empresa = Empresa.objects.get(id=empresa_id)
        resultado = GeneradorReportesDGII.generar_606(empresa, anio, mes)

        logger.info(f"Reporte 606 generado exitosamente: {resultado['cantidad_registros']} registros")
        return resultado

    except Exception as e:
        logger.error(f"Error generando reporte 606: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def generar_reporte_607(empresa_id: int, anio: int, mes: int) -> dict:
    """
    Genera el reporte 607 de ventas de bienes y servicios.

    Delega la lógica a GeneradorReportesDGII para mantener
    el principio KISS y evitar funciones largas.
    """
    from empresas.models import Empresa
    from .services import GeneradorReportesDGII

    logger.info(f"Iniciando generación de reporte 607 para empresa {empresa_id}, período {anio}-{mes:02d}")

    try:
        empresa = Empresa.objects.get(id=empresa_id)
        resultado = GeneradorReportesDGII.generar_607(empresa, anio, mes)

        logger.info(f"Reporte 607 generado exitosamente: {resultado['cantidad_registros']} registros")
        return resultado

    except Exception as e:
        logger.error(f"Error generando reporte 607: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def generar_reporte_608(empresa_id: int, anio: int, mes: int) -> dict:
    """
    Genera el reporte 608 de comprobantes anulados.

    Delega la lógica a GeneradorReportesDGII para mantener
    el principio KISS y evitar funciones largas.
    """
    from empresas.models import Empresa
    from .services import GeneradorReportesDGII

    logger.info(f"Iniciando generación de reporte 608 para empresa {empresa_id}, período {anio}-{mes:02d}")

    try:
        empresa = Empresa.objects.get(id=empresa_id)
        resultado = GeneradorReportesDGII.generar_608(empresa, anio, mes)

        logger.info(f"Reporte 608 generado exitosamente: {resultado['cantidad_registros']} registros")
        return resultado

    except Exception as e:
        logger.error(f"Error generando reporte 608: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

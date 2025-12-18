"""
Servicios de negocio para generación de reportes DGII.

Este módulo implementa el principio SRP (Single Responsibility Principle)
extrayendo la lógica de generación de reportes a servicios reutilizables.

Los reportes DGII son:
- 606: Compras de bienes y servicios
- 607: Ventas de bienes y servicios
- 608: Comprobantes fiscales anulados
"""
from decimal import Decimal
import csv
import io
import logging

logger = logging.getLogger(__name__)


def _get_tipo_identificacion(numero: str) -> str:
    """
    Determina el tipo de identificación según el formato DGII.

    Args:
        numero: Número de identificación (RNC/Cédula)

    Returns:
        '1' para RNC, '2' para Cédula, '3' para otros
    """
    if not numero:
        return '3'
    numero = numero.replace('-', '').replace(' ', '')
    if len(numero) == 9:
        return '1'  # RNC
    elif len(numero) == 11:
        return '2'  # Cédula
    return '3'  # Otro


class GeneradorReportesDGII:
    """
    Servicio para generar reportes fiscales DGII.

    Centraliza la lógica de transformación de modelos a formato DGII,
    cálculo de totales y generación de archivos TXT.
    """

    # Campos requeridos para cada reporte
    CAMPOS_606 = [
        'rnc_cedula', 'tipo_identificacion', 'tipo_bienes_servicios',
        'ncf', 'ncf_modificado', 'fecha_comprobante', 'fecha_pago',
        'monto_facturado', 'itbis_facturado', 'itbis_retenido',
        'itbis_sujeto_proporcionalidad', 'itbis_llevado_costo',
        'itbis_por_adelantar', 'itbis_percibido_compras',
        'tipo_retencion_isr', 'monto_retencion_renta',
        'isr_percibido_compras', 'impuesto_selectivo_consumo',
        'otros_impuestos_tasas', 'monto_propina_legal', 'forma_pago'
    ]

    CAMPOS_607 = [
        'rnc_cedula', 'tipo_identificacion', 'ncf', 'ncf_modificado',
        'tipo_ingreso', 'fecha_comprobante', 'fecha_retencion',
        'monto_facturado', 'itbis_facturado', 'itbis_retenido_terceros',
        'itbis_percibido', 'retencion_renta_terceros', 'isr_percibido',
        'impuesto_selectivo_consumo', 'otros_impuestos_tasas',
        'monto_propina_legal', 'efectivo', 'cheque_transferencia_deposito',
        'tarjeta_debito_credito', 'venta_credito',
        'bonos_certificados_regalo', 'permuta', 'otras_formas_venta'
    ]

    CAMPOS_608 = ['ncf', 'tipo_anulacion', 'fecha_comprobante']

    @staticmethod
    def generar_606(empresa, anio, mes):
        """
        Genera el reporte 606 de compras de bienes y servicios.

        Args:
            empresa: Instancia de Empresa
            anio: Año del reporte
            mes: Mes del reporte (1-12)

        Returns:
            dict con registros, totales y contenido TXT
        """
        from compras.models import Compra

        compras = Compra.objects.filter(
            empresa=empresa,
            fecha_compra__year=anio,
            fecha_compra__month=mes,
            estado__in=['REGISTRADA', 'CXP', 'PAGADA']
        ).select_related('proveedor').order_by('fecha_compra')

        registros = []
        for compra in compras:
            registro = GeneradorReportesDGII._transformar_compra_606(compra)
            registros.append(registro)

        contenido_txt = GeneradorReportesDGII._generar_txt(
            registros,
            GeneradorReportesDGII.CAMPOS_606
        )

        return {
            'status': 'completed',
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': len(registros),
            'registros': registros,
            'totales': GeneradorReportesDGII._calcular_totales_606(registros),
            'contenido_txt': contenido_txt,
            'nombre_archivo': f"606_{empresa.rnc}_{anio}{mes:02d}.txt"
        }

    @staticmethod
    def generar_607(empresa, anio, mes):
        """
        Genera el reporte 607 de ventas de bienes y servicios.

        Args:
            empresa: Instancia de Empresa
            anio: Año del reporte
            mes: Mes del reporte (1-12)

        Returns:
            dict con registros, totales y contenido TXT
        """
        from ventas.models import Factura

        facturas = Factura.objects.filter(
            empresa=empresa,
            fecha__year=anio,
            fecha__month=mes,
            estado__in=['PENDIENTE_PAGO', 'PAGADA_PARCIAL', 'PAGADA'],
            venta_sin_comprobante=False
        ).select_related('cliente').order_by('fecha')

        registros = []
        for factura in facturas:
            registro = GeneradorReportesDGII._transformar_factura_607(factura)
            registros.append(registro)

        contenido_txt = GeneradorReportesDGII._generar_txt(
            registros,
            GeneradorReportesDGII.CAMPOS_607
        )

        return {
            'status': 'completed',
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': len(registros),
            'registros': registros,
            'totales': GeneradorReportesDGII._calcular_totales_607(registros),
            'contenido_txt': contenido_txt,
            'nombre_archivo': f"607_{empresa.rnc}_{anio}{mes:02d}.txt"
        }

    @staticmethod
    def generar_608(empresa, anio, mes):
        """
        Genera el reporte 608 de comprobantes anulados.

        Args:
            empresa: Instancia de Empresa
            anio: Año del reporte
            mes: Mes del reporte (1-12)

        Returns:
            dict con registros y contenido TXT
        """
        from ventas.models import Factura

        facturas_anuladas = Factura.objects.filter(
            empresa=empresa,
            fecha__year=anio,
            fecha__month=mes,
            estado='CANCELADA',
            ncf__isnull=False
        ).exclude(ncf='').order_by('fecha')

        registros = []
        for factura in facturas_anuladas:
            registro = GeneradorReportesDGII._transformar_anulacion_608(factura)
            registros.append(registro)

        contenido_txt = GeneradorReportesDGII._generar_txt(
            registros,
            GeneradorReportesDGII.CAMPOS_608
        )

        return {
            'status': 'completed',
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': len(registros),
            'registros': registros,
            'contenido_txt': contenido_txt,
            'nombre_archivo': f"608_{empresa.rnc}_{anio}{mes:02d}.txt"
        }

    # ==================== MÉTODOS DE TRANSFORMACIÓN ====================

    @staticmethod
    def _transformar_compra_606(compra):
        """Transforma una Compra al formato de registro 606."""
        proveedor = compra.proveedor
        rnc = proveedor.numero_identificacion.replace('-', '').replace(' ', '') if proveedor.numero_identificacion else ''

        return {
            'rnc_cedula': rnc,
            'tipo_identificacion': _get_tipo_identificacion(rnc),
            'tipo_bienes_servicios': compra.tipo_gasto or '01',
            'ncf': compra.numero_ncf or '',
            'ncf_modificado': compra.ncf_modificado or '',
            'fecha_comprobante': compra.fecha_compra.strftime('%Y%m%d'),
            'fecha_pago': compra.fecha_compra.strftime('%Y%m%d'),
            'monto_facturado': str(compra.total),
            'itbis_facturado': str(compra.impuestos),
            'itbis_retenido': '0',
            'itbis_sujeto_proporcionalidad': '0',
            'itbis_llevado_costo': '0',
            'itbis_por_adelantar': '0',
            'itbis_percibido_compras': '0',
            'tipo_retencion_isr': '',
            'monto_retencion_renta': '0',
            'isr_percibido_compras': '0',
            'impuesto_selectivo_consumo': '0',
            'otros_impuestos_tasas': '0',
            'monto_propina_legal': '0',
            'forma_pago': '01',
        }

    @staticmethod
    def _transformar_factura_607(factura):
        """Transforma una Factura al formato de registro 607."""
        cliente = factura.cliente
        rnc = cliente.numero_identificacion.replace('-', '').replace(' ', '') if cliente.numero_identificacion else ''

        return {
            'rnc_cedula': rnc,
            'tipo_identificacion': _get_tipo_identificacion(rnc),
            'ncf': factura.ncf or '',
            'ncf_modificado': '',
            'tipo_ingreso': '01',  # Ingresos por operaciones
            'fecha_comprobante': factura.fecha.strftime('%Y%m%d'),
            'fecha_retencion': '',
            'monto_facturado': str(factura.total),
            'itbis_facturado': str(factura.itbis),
            'itbis_retenido_terceros': '0',
            'itbis_percibido': '0',
            'retencion_renta_terceros': '0',
            'isr_percibido': '0',
            'impuesto_selectivo_consumo': '0',
            'otros_impuestos_tasas': '0',
            'monto_propina_legal': '0',
            'efectivo': str(factura.total) if factura.tipo_venta == 'CONTADO' else '0',
            'cheque_transferencia_deposito': '0',
            'tarjeta_debito_credito': '0',
            'venta_credito': str(factura.total) if factura.tipo_venta == 'CREDITO' else '0',
            'bonos_certificados_regalo': '0',
            'permuta': '0',
            'otras_formas_venta': '0',
        }

    @staticmethod
    def _transformar_anulacion_608(factura):
        """Transforma una factura anulada al formato de registro 608."""
        return {
            'ncf': factura.ncf,
            'tipo_anulacion': '02',  # Error de impresión
            'fecha_comprobante': factura.fecha.strftime('%Y%m%d'),
        }

    # ==================== MÉTODOS DE GENERACIÓN Y TOTALES ====================

    @staticmethod
    def _generar_txt(registros, campos):
        """
        Genera el contenido del archivo TXT con formato DGII.

        Args:
            registros: Lista de diccionarios con los datos
            campos: Lista de nombres de campos en orden

        Returns:
            str con el contenido del archivo TXT
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter='|')
        for reg in registros:
            fila = [reg.get(campo, '') for campo in campos]
            writer.writerow(fila)
        return output.getvalue()

    @staticmethod
    def _calcular_totales_606(registros):
        """Calcula los totales para el reporte 606."""
        return {
            'monto_facturado': str(sum(
                Decimal(r['monto_facturado']) for r in registros
            )),
            'itbis_facturado': str(sum(
                Decimal(r['itbis_facturado']) for r in registros
            )),
        }

    @staticmethod
    def _calcular_totales_607(registros):
        """Calcula los totales para el reporte 607."""
        return {
            'monto_facturado': str(sum(
                Decimal(r['monto_facturado']) for r in registros
            )),
            'itbis_facturado': str(sum(
                Decimal(r['itbis_facturado']) for r in registros
            )),
        }

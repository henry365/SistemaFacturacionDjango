"""
Servicios para el módulo Vendedores

Este módulo centraliza la lógica de negocio para operaciones
complejas relacionadas con vendedores.
"""
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q

from .models import Vendedor
from .constants import (
    ESTADOS_FACTURA_PARA_COMISION,
    ESTADO_COTIZACION_APROBADA,
)

logger = logging.getLogger(__name__)


class ServicioVendedor:
    """Servicio para operaciones complejas con vendedores."""

    @staticmethod
    def obtener_estadisticas_ventas(vendedor: Vendedor) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ventas de un vendedor.

        Args:
            vendedor: Vendedor para el cual obtener estadísticas

        Returns:
            Diccionario con estadísticas de ventas
        """
        from ventas.models import Factura

        facturas = Factura.objects.filter(vendedor=vendedor)
        total_ventas = facturas.count()
        monto_total_ventas = facturas.aggregate(total=Sum('total'))['total'] or Decimal('0')
        monto_comisiones = (monto_total_ventas * vendedor.comision_porcentaje) / Decimal('100')

        logger.info(f"Estadísticas de ventas obtenidas para vendedor {vendedor.nombre}")

        return {
            'total_ventas': total_ventas,
            'monto_total_ventas': float(monto_total_ventas),
            'comision_porcentaje': float(vendedor.comision_porcentaje),
            'monto_comisiones': float(monto_comisiones),
        }

    @staticmethod
    def obtener_estadisticas_cotizaciones(vendedor: Vendedor) -> Dict[str, Any]:
        """
        Obtiene estadísticas de cotizaciones de un vendedor.

        Args:
            vendedor: Vendedor para el cual obtener estadísticas

        Returns:
            Diccionario con estadísticas de cotizaciones
        """
        from ventas.models import CotizacionCliente

        cotizaciones = CotizacionCliente.objects.filter(vendedor=vendedor)
        total_cotizaciones = cotizaciones.count()
        cotizaciones_aprobadas = cotizaciones.filter(estado=ESTADO_COTIZACION_APROBADA).count()

        logger.info(f"Estadísticas de cotizaciones obtenidas para vendedor {vendedor.nombre}")

        return {
            'total_cotizaciones': total_cotizaciones,
            'cotizaciones_aprobadas': cotizaciones_aprobadas,
        }

    @staticmethod
    def obtener_estadisticas_completas(vendedor: Vendedor) -> Dict[str, Any]:
        """
        Obtiene todas las estadísticas de un vendedor.

        Args:
            vendedor: Vendedor para el cual obtener estadísticas

        Returns:
            Diccionario con todas las estadísticas
        """
        estadisticas_ventas = ServicioVendedor.obtener_estadisticas_ventas(vendedor)
        estadisticas_cotizaciones = ServicioVendedor.obtener_estadisticas_cotizaciones(vendedor)
        total_clientes = vendedor.clientes.count()

        logger.info(f"Estadísticas completas obtenidas para vendedor {vendedor.nombre}")

        return {
            **estadisticas_ventas,
            **estadisticas_cotizaciones,
            'total_clientes': total_clientes,
        }

    @staticmethod
    def obtener_historial_ventas(vendedor: Vendedor) -> Dict[str, Any]:
        """
        Obtiene historial de ventas de un vendedor.

        Args:
            vendedor: Vendedor para el cual obtener historial

        Returns:
            Diccionario con información de ventas
        """
        from ventas.models import Factura

        facturas = Factura.objects.filter(vendedor=vendedor).order_by('-fecha')

        data = [{
            'id': f.id,
            'numero': f.numero_factura,
            'ncf': f.ncf,
            'cliente': f.cliente.nombre,
            'fecha': f.fecha,
            'total': float(f.total),
            'estado': f.estado,
            'tipo_venta': f.tipo_venta
        } for f in facturas]

        logger.info(f"Historial de ventas obtenido para vendedor {vendedor.nombre}: {len(data)} ventas")

        return {
            'vendedor': vendedor.nombre,
            'total_ventas': len(data),
            'monto_total': sum(float(v['total']) for v in data),
            'ventas': data
        }

    @staticmethod
    def obtener_historial_cotizaciones(vendedor: Vendedor) -> Dict[str, Any]:
        """
        Obtiene historial de cotizaciones de un vendedor.

        Args:
            vendedor: Vendedor para el cual obtener historial

        Returns:
            Diccionario con información de cotizaciones
        """
        from ventas.models import CotizacionCliente

        cotizaciones = CotizacionCliente.objects.filter(vendedor=vendedor).order_by('-fecha')

        data = [{
            'id': c.id,
            'cliente': c.cliente.nombre,
            'fecha': c.fecha,
            'vigencia': c.vigencia,
            'total': float(c.total),
            'estado': c.estado
        } for c in cotizaciones]

        logger.info(f"Historial de cotizaciones obtenido para vendedor {vendedor.nombre}: {len(data)} cotizaciones")

        return {
            'vendedor': vendedor.nombre,
            'total_cotizaciones': len(data),
            'monto_total': sum(float(c['total']) for c in data),
            'cotizaciones': data
        }

    @staticmethod
    def calcular_comisiones(
        vendedor: Vendedor,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calcula comisiones del vendedor en un período.

        Args:
            vendedor: Vendedor para el cual calcular comisiones
            fecha_inicio: Fecha de inicio del período (opcional)
            fecha_fin: Fecha de fin del período (opcional)

        Returns:
            Diccionario con resumen y detalle de comisiones
        """
        from ventas.models import Factura

        facturas = Factura.objects.filter(
            vendedor=vendedor,
            estado__in=ESTADOS_FACTURA_PARA_COMISION
        )

        if fecha_inicio:
            facturas = facturas.filter(fecha__date__gte=fecha_inicio)
        if fecha_fin:
            facturas = facturas.filter(fecha__date__lte=fecha_fin)

        monto_total_ventas = facturas.aggregate(total=Sum('total'))['total'] or Decimal('0')
        monto_comisiones = (monto_total_ventas * vendedor.comision_porcentaje) / Decimal('100')

        # Detalle de comisiones por factura
        detalle_comisiones = []
        for factura in facturas:
            comision_factura = (factura.total * vendedor.comision_porcentaje) / Decimal('100')
            detalle_comisiones.append({
                'factura_id': factura.id,
                'numero_factura': factura.numero_factura,
                'fecha': factura.fecha,
                'cliente': factura.cliente.nombre,
                'monto_venta': float(factura.total),
                'comision': float(comision_factura)
            })

        logger.info(
            f"Comisiones calculadas para vendedor {vendedor.nombre}: "
            f"{len(detalle_comisiones)} facturas, total comisiones: {float(monto_comisiones)}"
        )

        return {
            'resumen': {
                'total_ventas': facturas.count(),
                'monto_total_ventas': float(monto_total_ventas),
                'monto_total_comisiones': float(monto_comisiones)
            },
            'detalle': detalle_comisiones
        }

    @staticmethod
    def obtener_vendedores_activos_por_empresa(empresa_id: int) -> List[Vendedor]:
        """
        Obtiene todos los vendedores activos de una empresa.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Lista de vendedores activos
        """
        return list(Vendedor.objects.filter(
            empresa_id=empresa_id,
            activo=True
        ).order_by('nombre'))

    @staticmethod
    def buscar_vendedores(
        termino: str,
        empresa_id: int,
        solo_activos: bool = True
    ) -> List[Vendedor]:
        """
        Busca vendedores por término en nombre, cédula o contacto.

        Args:
            termino: Término de búsqueda
            empresa_id: ID de la empresa
            solo_activos: Si solo debe buscar en vendedores activos

        Returns:
            Lista de vendedores que coinciden
        """
        qs = Vendedor.objects.filter(
            empresa_id=empresa_id
        ).filter(
            Q(nombre__icontains=termino) |
            Q(cedula__icontains=termino) |
            Q(telefono__icontains=termino) |
            Q(correo__icontains=termino)
        )

        if solo_activos:
            qs = qs.filter(activo=True)

        return list(qs.order_by('nombre'))

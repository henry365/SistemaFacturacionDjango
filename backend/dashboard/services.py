"""
Servicios de negocio para el módulo Dashboard

Separa la lógica de negocio de las vistas para cumplir con los principios
SRP (Single Responsibility Principle) y SoC (Separation of Concerns).
"""
import logging
from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta

from .constants import (
    ESTADOS_FACTURA_VALIDOS, ESTADOS_FACTURA_PAGADAS,
    ESTADOS_CXC_ACTIVOS, ESTADOS_CXP_ACTIVOS,
    ESTADOS_COMPRA_VALIDOS, TIPOS_MOVIMIENTO_RELEVANTES,
    RANGOS_VENCIMIENTO, RANGOS_ANTIGUEDAD,
    DECIMAL_CERO
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Servicio para métricas del Dashboard"""

    @staticmethod
    def obtener_resumen(empresa):
        """
        Obtiene resumen completo del dashboard.

        Args:
            empresa: Instancia de Empresa

        Returns:
            dict: Resumen con todas las métricas
        """
        if not empresa:
            raise ValueError("Empresa es requerida")

        logger.info(f"Generando resumen dashboard para empresa {empresa.id}")

        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        inicio_mes = hoy.replace(day=1)

        ventas_hoy = DashboardService._calcular_ventas_dia(empresa, hoy)
        ventas_ayer = DashboardService._calcular_ventas_dia(empresa, ayer)
        ventas_mes = DashboardService._calcular_ventas_mes(empresa, inicio_mes)
        cxc_vencidas = DashboardService._calcular_cxc_vencidas(empresa, hoy)
        cxp_vencidas = DashboardService._calcular_cxp_vencidas(empresa, hoy)
        alertas = DashboardService._obtener_alertas_inventario(empresa)
        stock_bajo = DashboardService._contar_stock_bajo(empresa)
        caja_actual = DashboardService._obtener_caja_actual(empresa)
        cambio_porcentual = DashboardService._calcular_cambio_porcentual(
            ventas_hoy['total'], ventas_ayer['total']
        )

        return {
            'fecha': hoy.isoformat(),
            'ventas': {
                'hoy': {
                    'total': str(ventas_hoy['total']),
                    'cantidad': ventas_hoy['cantidad'],
                    'pagadas': ventas_hoy['pagadas'],
                    'pendientes': ventas_hoy['pendientes'],
                    'cambio_porcentual': str(cambio_porcentual)
                },
                'mes': {
                    'total': str(ventas_mes['total']),
                    'cantidad': ventas_mes['cantidad']
                }
            },
            'cuentas_por_cobrar': {
                'vencidas_total': str(cxc_vencidas['total']),
                'vencidas_cantidad': cxc_vencidas['cantidad']
            },
            'cuentas_por_pagar': {
                'vencidas_total': str(cxp_vencidas['total']),
                'vencidas_cantidad': cxp_vencidas['cantidad']
            },
            'inventario': {
                'alertas_total': alertas['total'],
                'alertas_por_tipo': alertas['por_tipo'],
                'productos_stock_bajo': stock_bajo
            },
            'caja_actual': caja_actual
        }

    @staticmethod
    def _calcular_ventas_dia(empresa, fecha):
        """Calcula ventas de un día específico"""
        from ventas.models import Factura

        return Factura.objects.filter(
            empresa=empresa,
            fecha__date=fecha,
            estado__in=ESTADOS_FACTURA_VALIDOS
        ).aggregate(
            total=Coalesce(Sum('total'), DECIMAL_CERO),
            cantidad=Count('id'),
            pagadas=Count('id', filter=Q(estado='PAGADA')),
            pendientes=Count('id', filter=Q(estado='PENDIENTE_PAGO'))
        )

    @staticmethod
    def _calcular_ventas_mes(empresa, inicio_mes):
        """Calcula ventas desde el inicio del mes"""
        from ventas.models import Factura

        return Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_mes,
            estado__in=ESTADOS_FACTURA_VALIDOS
        ).aggregate(
            total=Coalesce(Sum('total'), DECIMAL_CERO),
            cantidad=Count('id')
        )

    @staticmethod
    def _calcular_cxc_vencidas(empresa, hoy):
        """Calcula cuentas por cobrar vencidas"""
        from cuentas_cobrar.models import CuentaPorCobrar

        return CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXC_ACTIVOS,
            fecha_vencimiento__lt=hoy
        ).aggregate(
            total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
            cantidad=Count('id')
        )

    @staticmethod
    def _calcular_cxp_vencidas(empresa, hoy):
        """Calcula cuentas por pagar vencidas"""
        from cuentas_pagar.models import CuentaPorPagar

        return CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXP_ACTIVOS,
            fecha_vencimiento__lt=hoy
        ).aggregate(
            total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
            cantidad=Count('id')
        )

    @staticmethod
    def _obtener_alertas_inventario(empresa):
        """Obtiene alertas de inventario agrupadas por tipo"""
        from inventario.models import AlertaInventario

        alertas = AlertaInventario.objects.filter(
            empresa=empresa,
            resuelta=False
        ).values('tipo').annotate(
            cantidad=Count('id')
        ).order_by('tipo')

        alertas_dict = {a['tipo']: a['cantidad'] for a in alertas}
        total_alertas = sum(alertas_dict.values())

        return {
            'total': total_alertas,
            'por_tipo': alertas_dict
        }

    @staticmethod
    def _contar_stock_bajo(empresa):
        """Cuenta productos con stock bajo"""
        from inventario.models import InventarioProducto

        return InventarioProducto.objects.filter(
            empresa=empresa,
            cantidad_disponible__lte=F('stock_minimo'),
            producto__activo=True
        ).count()

    @staticmethod
    def _obtener_caja_actual(empresa):
        """Obtiene información de la caja actual"""
        from caja.models import SesionCaja

        sesion = SesionCaja.objects.filter(
            caja__activa=True,
            estado='ABIERTA'
        ).select_related('caja', 'usuario').first()

        if not sesion:
            return None

        return {
            'id': sesion.id,
            'caja_nombre': sesion.caja.nombre,
            'usuario': sesion.usuario.get_full_name() or sesion.usuario.username,
            'fecha_apertura': sesion.fecha_apertura,
            'monto_apertura': str(sesion.monto_apertura)
        }

    @staticmethod
    def _calcular_cambio_porcentual(total_hoy, total_ayer):
        """Calcula cambio porcentual entre hoy y ayer"""
        if not total_ayer or total_ayer == 0:
            return DECIMAL_CERO

        return ((total_hoy - total_ayer) / total_ayer * 100).quantize(Decimal('0.01'))

    @staticmethod
    def obtener_ventas_periodo(empresa, dias):
        """
        Obtiene ventas agrupadas por día.

        Args:
            empresa: Instancia de Empresa
            dias: Número de días hacia atrás

        Returns:
            dict: Datos de ventas por día
        """
        from ventas.models import Factura

        logger.debug(f"Obteniendo ventas de {dias} días para empresa {empresa.id}")

        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        ventas = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=ESTADOS_FACTURA_VALIDOS
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            total=Coalesce(Sum('total'), DECIMAL_CERO),
            cantidad=Count('id')
        ).order_by('dia')

        return {
            'periodo_dias': dias,
            'fecha_inicio': fecha_inicio.isoformat(),
            'datos': [
                {
                    'fecha': v['dia'].isoformat(),
                    'total': str(v['total']),
                    'cantidad': v['cantidad']
                }
                for v in ventas
            ]
        }

    @staticmethod
    def obtener_ventas_por_mes(empresa, meses):
        """
        Obtiene ventas agrupadas por mes.

        Args:
            empresa: Instancia de Empresa
            meses: Número de meses hacia atrás

        Returns:
            dict: Datos de ventas por mes
        """
        from ventas.models import Factura

        logger.debug(f"Obteniendo ventas de {meses} meses para empresa {empresa.id}")

        fecha_inicio = (timezone.now().date().replace(day=1) - timedelta(days=meses * 30)).replace(day=1)

        ventas = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=ESTADOS_FACTURA_VALIDOS
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Coalesce(Sum('total'), DECIMAL_CERO),
            cantidad=Count('id')
        ).order_by('mes')

        return {
            'periodo_meses': meses,
            'datos': [
                {
                    'mes': v['mes'].strftime('%Y-%m'),
                    'total': str(v['total']),
                    'cantidad': v['cantidad']
                }
                for v in ventas
            ]
        }

    @staticmethod
    def obtener_top_productos(empresa, limite, dias):
        """
        Obtiene los productos más vendidos.

        Args:
            empresa: Instancia de Empresa
            limite: Cantidad de productos
            dias: Período en días

        Returns:
            dict: Top productos vendidos
        """
        from ventas.models import DetalleFactura

        logger.debug(f"Obteniendo top {limite} productos de {dias} días")

        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        productos = DetalleFactura.objects.filter(
            factura__empresa=empresa,
            factura__fecha__date__gte=fecha_inicio,
            factura__estado__in=ESTADOS_FACTURA_PAGADAS
        ).values(
            'producto__id',
            'producto__codigo_sku',
            'producto__nombre'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            total_vendido=Sum('importe')
        ).order_by('-cantidad_vendida')[:limite]

        return {
            'periodo_dias': dias,
            'productos': [
                {
                    'id': p['producto__id'],
                    'codigo_sku': p['producto__codigo_sku'],
                    'nombre': p['producto__nombre'],
                    'cantidad_vendida': str(p['cantidad_vendida']),
                    'total_vendido': str(p['total_vendido'])
                }
                for p in productos
            ]
        }

    @staticmethod
    def obtener_productos_stock_bajo(empresa, limite):
        """
        Obtiene productos con stock por debajo del mínimo.

        Args:
            empresa: Instancia de Empresa
            limite: Cantidad de productos

        Returns:
            dict: Productos con stock bajo
        """
        from inventario.models import InventarioProducto

        logger.debug(f"Obteniendo productos con stock bajo (limite: {limite})")

        productos = InventarioProducto.objects.filter(
            empresa=empresa,
            cantidad_disponible__lte=F('stock_minimo'),
            producto__activo=True
        ).select_related(
            'producto', 'almacen'
        ).annotate(
            deficit=F('stock_minimo') - F('cantidad_disponible')
        ).order_by('-deficit')[:limite]

        return {
            'total': productos.count(),
            'productos': [
                {
                    'id': p.producto.id,
                    'codigo_sku': p.producto.codigo_sku,
                    'nombre': p.producto.nombre,
                    'almacen': p.almacen.nombre,
                    'cantidad_disponible': str(p.cantidad_disponible),
                    'stock_minimo': str(p.stock_minimo),
                    'deficit': str(p.deficit)
                }
                for p in productos
            ]
        }

    @staticmethod
    def obtener_top_clientes(empresa, limite, dias):
        """
        Obtiene los clientes con mayor volumen de compras.

        Args:
            empresa: Instancia de Empresa
            limite: Cantidad de clientes
            dias: Período en días

        Returns:
            dict: Top clientes
        """
        from ventas.models import Factura

        logger.debug(f"Obteniendo top {limite} clientes de {dias} días")

        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        clientes = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=ESTADOS_FACTURA_PAGADAS
        ).values(
            'cliente__id',
            'cliente__nombre'
        ).annotate(
            total_compras=Sum('total'),
            cantidad_facturas=Count('id')
        ).order_by('-total_compras')[:limite]

        return {
            'periodo_dias': dias,
            'clientes': [
                {
                    'id': c['cliente__id'],
                    'nombre': c['cliente__nombre'],
                    'total_compras': str(c['total_compras']),
                    'cantidad_facturas': c['cantidad_facturas']
                }
                for c in clientes
            ]
        }

    @staticmethod
    def obtener_detalle_cxc(empresa):
        """
        Obtiene resumen detallado de cuentas por cobrar.

        Args:
            empresa: Instancia de Empresa

        Returns:
            dict: Detalle de CxC
        """
        from cuentas_cobrar.models import CuentaPorCobrar

        hoy = timezone.now().date()

        # Por estado
        resumen = CuentaPorCobrar.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
            cantidad=Count('id')
        )

        # Por vencer
        por_vencer = {}
        for dias in RANGOS_VENCIMIENTO:
            fecha_limite = hoy + timedelta(days=dias)
            resultado = CuentaPorCobrar.objects.filter(
                empresa=empresa,
                estado__in=['PENDIENTE', 'PARCIAL'],
                fecha_vencimiento__lte=fecha_limite,
                fecha_vencimiento__gt=hoy
            ).aggregate(
                total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
                cantidad=Count('id')
            )
            por_vencer[f'dias_{dias}'] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        # Vencidas por antigüedad
        vencidas = {}
        for inicio, fin in RANGOS_ANTIGUEDAD:
            filtros = {
                'empresa': empresa,
                'estado__in': ESTADOS_CXC_ACTIVOS,
                'fecha_vencimiento__lt': hoy - timedelta(days=inicio - 1)
            }
            if fin:
                filtros['fecha_vencimiento__gte'] = hoy - timedelta(days=fin)

            resultado = CuentaPorCobrar.objects.filter(**filtros).aggregate(
                total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
                cantidad=Count('id')
            )
            key = f'{inicio}_a_{fin}_dias' if fin else f'mas_de_{inicio}_dias'
            vencidas[key] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        return {
            'resumen_por_estado': {
                r['estado']: {'total': str(r['total']), 'cantidad': r['cantidad']}
                for r in resumen
            },
            'por_vencer': por_vencer,
            'vencidas_por_antiguedad': vencidas
        }

    @staticmethod
    def obtener_detalle_cxp(empresa):
        """
        Obtiene resumen detallado de cuentas por pagar.

        Args:
            empresa: Instancia de Empresa

        Returns:
            dict: Detalle de CxP
        """
        from cuentas_pagar.models import CuentaPorPagar

        hoy = timezone.now().date()

        # Por estado
        resumen = CuentaPorPagar.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
            cantidad=Count('id')
        )

        # Por vencer
        por_vencer = {}
        for dias in RANGOS_VENCIMIENTO:
            fecha_limite = hoy + timedelta(days=dias)
            resultado = CuentaPorPagar.objects.filter(
                empresa=empresa,
                estado__in=['PENDIENTE', 'PARCIAL'],
                fecha_vencimiento__lte=fecha_limite,
                fecha_vencimiento__gt=hoy
            ).aggregate(
                total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO),
                cantidad=Count('id')
            )
            por_vencer[f'dias_{dias}'] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        return {
            'resumen_por_estado': {
                r['estado']: {'total': str(r['total']), 'cantidad': r['cantidad']}
                for r in resumen
            },
            'por_vencer': por_vencer
        }

    @staticmethod
    def obtener_actividad_reciente(empresa, limite):
        """
        Obtiene las últimas actividades del sistema.

        Args:
            empresa: Instancia de Empresa
            limite: Cantidad de actividades

        Returns:
            dict: Actividades recientes
        """
        from ventas.models import Factura
        from compras.models import Compra
        from inventario.models import MovimientoInventario

        logger.debug(f"Obteniendo actividad reciente (limite: {limite})")

        actividades = []
        limite_por_tipo = limite // 3

        # Facturas
        facturas = Factura.objects.filter(
            empresa=empresa
        ).select_related('cliente', 'usuario').order_by('-fecha')[:limite_por_tipo]

        for f in facturas:
            actividades.append({
                'tipo': 'FACTURA',
                'fecha': f.fecha,
                'descripcion': f'Factura #{f.numero_factura or f.id} - {f.cliente.nombre}',
                'monto': str(f.total),
                'estado': f.estado,
                'usuario': f.usuario.get_full_name() if f.usuario else None
            })

        # Compras
        compras = Compra.objects.filter(
            empresa=empresa
        ).select_related('proveedor', 'usuario_creacion').order_by('-fecha_registro')[:limite_por_tipo]

        for c in compras:
            actividades.append({
                'tipo': 'COMPRA',
                'fecha': c.fecha_registro,
                'descripcion': f'Compra #{c.numero_factura_proveedor or c.id} - {c.proveedor.nombre}',
                'monto': str(c.total),
                'estado': c.estado,
                'usuario': c.usuario_creacion.get_full_name() if c.usuario_creacion else None
            })

        # Movimientos de inventario
        movimientos = MovimientoInventario.objects.filter(
            empresa=empresa,
            tipo_movimiento__in=TIPOS_MOVIMIENTO_RELEVANTES
        ).select_related('producto', 'usuario_creacion').order_by('-fecha')[:limite_por_tipo]

        for m in movimientos:
            actividades.append({
                'tipo': f'INVENTARIO_{m.tipo_movimiento}',
                'fecha': m.fecha,
                'descripcion': f'{m.get_tipo_movimiento_display()} - {m.producto.nombre}',
                'monto': str(m.cantidad),
                'estado': None,
                'usuario': m.usuario_creacion.get_full_name() if m.usuario_creacion else None
            })

        # Ordenar y limitar
        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        actividades = actividades[:limite]

        # Convertir fechas
        for a in actividades:
            a['fecha'] = a['fecha'].isoformat()

        return {
            'total': len(actividades),
            'actividades': actividades
        }

    @staticmethod
    def obtener_indicadores_financieros(empresa):
        """
        Obtiene indicadores financieros clave.

        Args:
            empresa: Instancia de Empresa

        Returns:
            dict: Indicadores financieros
        """
        from ventas.models import Factura
        from compras.models import Compra
        from cuentas_cobrar.models import CuentaPorCobrar
        from cuentas_pagar.models import CuentaPorPagar
        from inventario.models import InventarioProducto

        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        # Ventas del mes
        ventas_mes = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_mes,
            estado__in=ESTADOS_FACTURA_PAGADAS
        ).aggregate(total=Coalesce(Sum('total'), DECIMAL_CERO))['total']

        # Ventas del año
        ventas_anio = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_anio,
            estado__in=ESTADOS_FACTURA_PAGADAS
        ).aggregate(total=Coalesce(Sum('total'), DECIMAL_CERO))['total']

        # Compras del mes
        compras_mes = Compra.objects.filter(
            empresa=empresa,
            fecha_compra__gte=inicio_mes,
            estado__in=ESTADOS_COMPRA_VALIDOS
        ).aggregate(total=Coalesce(Sum('total'), DECIMAL_CERO))['total']

        # Total CxC
        total_cxc = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXC_ACTIVOS
        ).aggregate(total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO))['total']

        # Total CxP
        total_cxp = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=ESTADOS_CXP_ACTIVOS
        ).aggregate(total=Coalesce(Sum('monto_pendiente'), DECIMAL_CERO))['total']

        # Valor del inventario
        valor_inventario = InventarioProducto.objects.filter(
            empresa=empresa,
            producto__activo=True
        ).aggregate(
            total=Coalesce(Sum('valor_inventario'), DECIMAL_CERO)
        )['total']

        # Margen bruto estimado
        margen_bruto = ventas_mes - compras_mes if ventas_mes and compras_mes else DECIMAL_CERO

        return {
            'periodo': {
                'mes': inicio_mes.strftime('%Y-%m'),
                'anio': str(inicio_anio.year)
            },
            'ventas': {
                'mes': str(ventas_mes),
                'anio': str(ventas_anio)
            },
            'compras': {
                'mes': str(compras_mes)
            },
            'cuentas': {
                'por_cobrar': str(total_cxc),
                'por_pagar': str(total_cxp),
                'diferencia': str(total_cxc - total_cxp)
            },
            'inventario': {
                'valor_total': str(valor_inventario)
            },
            'margen_bruto_mes': str(margen_bruto)
        }

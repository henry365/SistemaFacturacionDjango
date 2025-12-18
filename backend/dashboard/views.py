"""
Dashboard API - Endpoints optimizados para métricas y KPIs del sistema.

Este módulo provee endpoints eficientes que agregan datos de múltiples
modelos usando consultas optimizadas con Django ORM.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, F, Q, Case, When, Value, DecimalField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para métricas del Dashboard.

    Todos los endpoints filtran automáticamente por la empresa del usuario
    autenticado para garantizar aislamiento multi-tenant.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_empresa(self, request):
        """Obtiene la empresa del usuario autenticado"""
        return request.user.empresa

    # ==================== ENDPOINT PRINCIPAL ====================

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        Endpoint principal que retorna todas las métricas del dashboard
        en una sola llamada optimizada.

        Returns:
            - ventas_hoy: Total y cantidad de facturas del día
            - ventas_ayer: Para comparación porcentual
            - cxc_vencidas: Cuentas por cobrar vencidas
            - cxp_vencidas: Cuentas por pagar vencidas
            - alertas_inventario: Conteo por tipo de alerta
            - caja_actual: Estado de la sesión de caja activa
        """
        empresa = self.get_empresa(request)
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        inicio_mes = hoy.replace(day=1)

        # Importar modelos aquí para evitar importaciones circulares
        from ventas.models import Factura
        from cuentas_cobrar.models import CuentaPorCobrar
        from cuentas_pagar.models import CuentaPorPagar
        from inventario.models import AlertaInventario, InventarioProducto
        from caja.models import SesionCaja

        # === VENTAS DEL DÍA (optimizado con una sola query) ===
        ventas_hoy = Factura.objects.filter(
            empresa=empresa,
            fecha__date=hoy,
            estado__in=['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
        ).aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id'),
            pagadas=Count('id', filter=Q(estado='PAGADA')),
            pendientes=Count('id', filter=Q(estado='PENDIENTE_PAGO'))
        )

        # === VENTAS DE AYER (para comparación) ===
        ventas_ayer = Factura.objects.filter(
            empresa=empresa,
            fecha__date=ayer,
            estado__in=['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
        ).aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00'))
        )

        # === VENTAS DEL MES ===
        ventas_mes = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_mes,
            estado__in=['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
        ).aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id')
        )

        # === CUENTAS POR COBRAR VENCIDAS ===
        cxc_vencidas = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA'],
            fecha_vencimiento__lt=hoy
        ).aggregate(
            total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
            cantidad=Count('id')
        )

        # === CUENTAS POR PAGAR VENCIDAS ===
        cxp_vencidas = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA'],
            fecha_vencimiento__lt=hoy
        ).aggregate(
            total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
            cantidad=Count('id')
        )

        # === ALERTAS DE INVENTARIO (agrupadas por tipo) ===
        alertas = AlertaInventario.objects.filter(
            empresa=empresa,
            resuelta=False
        ).values('tipo').annotate(
            cantidad=Count('id')
        ).order_by('tipo')

        alertas_dict = {a['tipo']: a['cantidad'] for a in alertas}
        total_alertas = sum(alertas_dict.values())

        # === PRODUCTOS CON STOCK BAJO (directo) ===
        stock_bajo = InventarioProducto.objects.filter(
            empresa=empresa,
            cantidad_disponible__lte=F('stock_minimo'),
            producto__activo=True
        ).count()

        # === CAJA ACTUAL ===
        caja_actual = None
        sesion = SesionCaja.objects.filter(
            caja__activa=True,
            estado='ABIERTA'
        ).select_related('caja', 'usuario').first()

        if sesion:
            caja_actual = {
                'id': sesion.id,
                'caja_nombre': sesion.caja.nombre,
                'usuario': sesion.usuario.get_full_name() or sesion.usuario.username,
                'fecha_apertura': sesion.fecha_apertura,
                'monto_apertura': str(sesion.monto_apertura)
            }

        # === CALCULAR PORCENTAJE DE CAMBIO ===
        cambio_porcentual = Decimal('0.00')
        if ventas_ayer['total'] and ventas_ayer['total'] > 0:
            cambio_porcentual = (
                (ventas_hoy['total'] - ventas_ayer['total']) / ventas_ayer['total'] * 100
            ).quantize(Decimal('0.01'))

        return Response({
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
                'alertas_total': total_alertas,
                'alertas_por_tipo': alertas_dict,
                'productos_stock_bajo': stock_bajo
            },
            'caja_actual': caja_actual
        })

    # ==================== VENTAS ====================

    @action(detail=False, methods=['get'])
    def ventas_periodo(self, request):
        """
        Retorna ventas agrupadas por día para gráficos.

        Query params:
            - dias: Número de días hacia atrás (default: 30)
        """
        from ventas.models import Factura

        empresa = self.get_empresa(request)
        dias = int(request.query_params.get('dias', 30))
        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        ventas = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id')
        ).order_by('dia')

        return Response({
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
        })

    @action(detail=False, methods=['get'])
    def ventas_por_mes(self, request):
        """
        Retorna ventas agrupadas por mes para gráficos anuales.

        Query params:
            - meses: Número de meses hacia atrás (default: 12)
        """
        from ventas.models import Factura

        empresa = self.get_empresa(request)
        meses = int(request.query_params.get('meses', 12))
        fecha_inicio = (timezone.now().date().replace(day=1) - timedelta(days=meses * 30)).replace(day=1)

        ventas = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id')
        ).order_by('mes')

        return Response({
            'periodo_meses': meses,
            'datos': [
                {
                    'mes': v['mes'].strftime('%Y-%m'),
                    'total': str(v['total']),
                    'cantidad': v['cantidad']
                }
                for v in ventas
            ]
        })

    # ==================== PRODUCTOS ====================

    @action(detail=False, methods=['get'])
    def top_productos(self, request):
        """
        Retorna los productos más vendidos.

        Query params:
            - limite: Cantidad de productos (default: 10)
            - dias: Período en días (default: 30)
        """
        from ventas.models import DetalleFactura

        empresa = self.get_empresa(request)
        limite = int(request.query_params.get('limite', 10))
        dias = int(request.query_params.get('dias', 30))
        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        productos = DetalleFactura.objects.filter(
            factura__empresa=empresa,
            factura__fecha__date__gte=fecha_inicio,
            factura__estado__in=['PAGADA', 'PAGADA_PARCIAL']
        ).values(
            'producto__id',
            'producto__codigo_sku',
            'producto__nombre'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            total_vendido=Sum('importe')
        ).order_by('-cantidad_vendida')[:limite]

        return Response({
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
        })

    @action(detail=False, methods=['get'])
    def productos_stock_bajo(self, request):
        """
        Retorna productos con stock por debajo del mínimo.

        Query params:
            - limite: Cantidad de productos (default: 20)
        """
        from inventario.models import InventarioProducto

        empresa = self.get_empresa(request)
        limite = int(request.query_params.get('limite', 20))

        productos = InventarioProducto.objects.filter(
            empresa=empresa,
            cantidad_disponible__lte=F('stock_minimo'),
            producto__activo=True
        ).select_related(
            'producto', 'almacen'
        ).annotate(
            deficit=F('stock_minimo') - F('cantidad_disponible')
        ).order_by('-deficit')[:limite]

        return Response({
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
        })

    # ==================== CLIENTES ====================

    @action(detail=False, methods=['get'])
    def top_clientes(self, request):
        """
        Retorna los clientes con mayor volumen de compras.

        Query params:
            - limite: Cantidad de clientes (default: 10)
            - dias: Período en días (default: 90)
        """
        from ventas.models import Factura

        empresa = self.get_empresa(request)
        limite = int(request.query_params.get('limite', 10))
        dias = int(request.query_params.get('dias', 90))
        fecha_inicio = timezone.now().date() - timedelta(days=dias)

        clientes = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=fecha_inicio,
            estado__in=['PAGADA', 'PAGADA_PARCIAL']
        ).values(
            'cliente__id',
            'cliente__nombre'
        ).annotate(
            total_compras=Sum('total'),
            cantidad_facturas=Count('id')
        ).order_by('-total_compras')[:limite]

        return Response({
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
        })

    # ==================== CUENTAS ====================

    @action(detail=False, methods=['get'])
    def cuentas_por_cobrar(self, request):
        """
        Resumen detallado de cuentas por cobrar.
        """
        from cuentas_cobrar.models import CuentaPorCobrar

        empresa = self.get_empresa(request)
        hoy = timezone.now().date()

        # Agrupación por estado
        resumen = CuentaPorCobrar.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
            cantidad=Count('id')
        )

        # Por vencer (próximos 7, 15, 30 días)
        por_vencer = {}
        for dias in [7, 15, 30]:
            fecha_limite = hoy + timedelta(days=dias)
            resultado = CuentaPorCobrar.objects.filter(
                empresa=empresa,
                estado__in=['PENDIENTE', 'PARCIAL'],
                fecha_vencimiento__lte=fecha_limite,
                fecha_vencimiento__gt=hoy
            ).aggregate(
                total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
                cantidad=Count('id')
            )
            por_vencer[f'dias_{dias}'] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        # Vencidas por antigüedad
        vencidas = {}
        rangos = [(1, 30), (31, 60), (61, 90), (91, None)]
        for inicio, fin in rangos:
            filtros = {
                'empresa': empresa,
                'estado__in': ['PENDIENTE', 'PARCIAL', 'VENCIDA'],
                'fecha_vencimiento__lt': hoy - timedelta(days=inicio - 1)
            }
            if fin:
                filtros['fecha_vencimiento__gte'] = hoy - timedelta(days=fin)

            resultado = CuentaPorCobrar.objects.filter(**filtros).aggregate(
                total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
                cantidad=Count('id')
            )
            key = f'{inicio}_a_{fin}_dias' if fin else f'mas_de_{inicio}_dias'
            vencidas[key] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        return Response({
            'resumen_por_estado': {r['estado']: {'total': str(r['total']), 'cantidad': r['cantidad']} for r in resumen},
            'por_vencer': por_vencer,
            'vencidas_por_antiguedad': vencidas
        })

    @action(detail=False, methods=['get'])
    def cuentas_por_pagar(self, request):
        """
        Resumen detallado de cuentas por pagar.
        """
        from cuentas_pagar.models import CuentaPorPagar

        empresa = self.get_empresa(request)
        hoy = timezone.now().date()

        # Agrupación por estado
        resumen = CuentaPorPagar.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
            cantidad=Count('id')
        )

        # Por vencer (próximos 7, 15, 30 días)
        por_vencer = {}
        for dias in [7, 15, 30]:
            fecha_limite = hoy + timedelta(days=dias)
            resultado = CuentaPorPagar.objects.filter(
                empresa=empresa,
                estado__in=['PENDIENTE', 'PARCIAL'],
                fecha_vencimiento__lte=fecha_limite,
                fecha_vencimiento__gt=hoy
            ).aggregate(
                total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')),
                cantidad=Count('id')
            )
            por_vencer[f'dias_{dias}'] = {
                'total': str(resultado['total']),
                'cantidad': resultado['cantidad']
            }

        return Response({
            'resumen_por_estado': {r['estado']: {'total': str(r['total']), 'cantidad': r['cantidad']} for r in resumen},
            'por_vencer': por_vencer
        })

    # ==================== ACTIVIDAD RECIENTE ====================

    @action(detail=False, methods=['get'])
    def actividad_reciente(self, request):
        """
        Retorna las últimas actividades del sistema.

        Query params:
            - limite: Cantidad de actividades (default: 20)
        """
        from ventas.models import Factura
        from compras.models import Compra
        from inventario.models import MovimientoInventario

        empresa = self.get_empresa(request)
        limite = int(request.query_params.get('limite', 20))

        actividades = []

        # Últimas facturas
        facturas = Factura.objects.filter(
            empresa=empresa
        ).select_related('cliente', 'usuario').order_by('-fecha')[:limite // 3]

        for f in facturas:
            actividades.append({
                'tipo': 'FACTURA',
                'fecha': f.fecha,
                'descripcion': f'Factura #{f.numero_factura or f.id} - {f.cliente.nombre}',
                'monto': str(f.total),
                'estado': f.estado,
                'usuario': f.usuario.get_full_name() if f.usuario else None
            })

        # Últimas compras
        compras = Compra.objects.filter(
            empresa=empresa
        ).select_related('proveedor', 'usuario_creacion').order_by('-fecha_registro')[:limite // 3]

        for c in compras:
            actividades.append({
                'tipo': 'COMPRA',
                'fecha': c.fecha_registro,
                'descripcion': f'Compra #{c.numero_factura_proveedor or c.id} - {c.proveedor.nombre}',
                'monto': str(c.total),
                'estado': c.estado,
                'usuario': c.usuario_creacion.get_full_name() if c.usuario_creacion else None
            })

        # Últimos movimientos de inventario relevantes
        movimientos = MovimientoInventario.objects.filter(
            empresa=empresa,
            tipo_movimiento__in=['ENTRADA_COMPRA', 'SALIDA_VENTA', 'AJUSTE', 'TRANSFERENCIA']
        ).select_related('producto', 'usuario_creacion').order_by('-fecha')[:limite // 3]

        for m in movimientos:
            actividades.append({
                'tipo': f'INVENTARIO_{m.tipo_movimiento}',
                'fecha': m.fecha,
                'descripcion': f'{m.get_tipo_movimiento_display()} - {m.producto.nombre}',
                'monto': str(m.cantidad),
                'estado': None,
                'usuario': m.usuario_creacion.get_full_name() if m.usuario_creacion else None
            })

        # Ordenar por fecha y limitar
        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        actividades = actividades[:limite]

        # Convertir fechas a ISO format
        for a in actividades:
            a['fecha'] = a['fecha'].isoformat()

        return Response({
            'total': len(actividades),
            'actividades': actividades
        })

    # ==================== INDICADORES FINANCIEROS ====================

    @action(detail=False, methods=['get'])
    def indicadores_financieros(self, request):
        """
        Retorna indicadores financieros clave.
        """
        from ventas.models import Factura
        from compras.models import Compra
        from cuentas_cobrar.models import CuentaPorCobrar
        from cuentas_pagar.models import CuentaPorPagar
        from inventario.models import InventarioProducto

        empresa = self.get_empresa(request)
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        # Ventas del mes
        ventas_mes = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_mes,
            estado__in=['PAGADA', 'PAGADA_PARCIAL']
        ).aggregate(total=Coalesce(Sum('total'), Decimal('0.00')))['total']

        # Ventas del año
        ventas_anio = Factura.objects.filter(
            empresa=empresa,
            fecha__date__gte=inicio_anio,
            estado__in=['PAGADA', 'PAGADA_PARCIAL']
        ).aggregate(total=Coalesce(Sum('total'), Decimal('0.00')))['total']

        # Compras del mes
        compras_mes = Compra.objects.filter(
            empresa=empresa,
            fecha_compra__gte=inicio_mes,
            estado__in=['REGISTRADA', 'CXP', 'PAGADA']
        ).aggregate(total=Coalesce(Sum('total'), Decimal('0.00')))['total']

        # Total CxC
        total_cxc = CuentaPorCobrar.objects.filter(
            empresa=empresa,
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        ).aggregate(total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')))['total']

        # Total CxP
        total_cxp = CuentaPorPagar.objects.filter(
            empresa=empresa,
            estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']
        ).aggregate(total=Coalesce(Sum('monto_pendiente'), Decimal('0.00')))['total']

        # Valor del inventario (usando GeneratedField de Django 6.0)
        valor_inventario = InventarioProducto.objects.filter(
            empresa=empresa,
            producto__activo=True
        ).aggregate(
            total=Coalesce(Sum('valor_inventario'), Decimal('0.00'))
        )['total']

        # Margen bruto estimado del mes (ventas - costo de ventas)
        # Nota: Esto es una estimación, el cálculo real dependería de más datos
        margen_bruto = ventas_mes - compras_mes if ventas_mes and compras_mes else Decimal('0.00')

        return Response({
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
        })

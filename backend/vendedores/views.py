from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from .models import Vendedor
from .serializers import VendedorSerializer
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin

class VendedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'cedula', 'telefono', 'correo']
    ordering_fields = ['nombre', 'fecha_creacion', 'comision_porcentaje']
    ordering = ['nombre']

    def get_queryset(self):
        """Filtrar vendedores según empresa del usuario"""
        queryset = super().get_queryset()
        # Filtros específicos
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        return queryset

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas del vendedor"""
        vendedor = self.get_object()
        from ventas.models import Factura, CotizacionCliente
        
        # Estadísticas de ventas
        facturas = Factura.objects.filter(vendedor=vendedor)
        total_ventas = facturas.count()
        monto_total_ventas = facturas.aggregate(total=Sum('total'))['total'] or 0
        monto_comisiones = (monto_total_ventas * vendedor.comision_porcentaje) / 100
        
        # Estadísticas de cotizaciones
        cotizaciones = CotizacionCliente.objects.filter(vendedor=vendedor)
        total_cotizaciones = cotizaciones.count()
        cotizaciones_aprobadas = cotizaciones.filter(estado='APROBADA').count()
        
        # Estadísticas de clientes
        total_clientes = vendedor.clientes.count()
        
        return Response({
            'vendedor': VendedorSerializer(vendedor).data,
            'estadisticas': {
                'total_ventas': total_ventas,
                'monto_total_ventas': float(monto_total_ventas),
                'comision_porcentaje': float(vendedor.comision_porcentaje),
                'monto_comisiones': float(monto_comisiones),
                'total_cotizaciones': total_cotizaciones,
                'cotizaciones_aprobadas': cotizaciones_aprobadas,
                'total_clientes': total_clientes
            }
        })

    @action(detail=True, methods=['get'])
    def ventas(self, request, pk=None):
        """Listar ventas del vendedor"""
        vendedor = self.get_object()
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
        
        return Response({
            'vendedor': vendedor.nombre,
            'total_ventas': len(data),
            'monto_total': sum(float(v['total']) for v in data),
            'ventas': data
        })

    @action(detail=True, methods=['get'])
    def cotizaciones(self, request, pk=None):
        """Listar cotizaciones del vendedor"""
        vendedor = self.get_object()
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
        
        return Response({
            'vendedor': vendedor.nombre,
            'total_cotizaciones': len(data),
            'monto_total': sum(float(c['total']) for c in data),
            'cotizaciones': data
        })

    @action(detail=True, methods=['get'])
    def clientes(self, request, pk=None):
        """Listar clientes asignados al vendedor"""
        vendedor = self.get_object()
        clientes = vendedor.clientes.all()
        
        from clientes.serializers import ClienteSerializer
        serializer = ClienteSerializer(clientes, many=True)
        
        return Response({
            'vendedor': vendedor.nombre,
            'total_clientes': clientes.count(),
            'clientes': serializer.data
        })

    @action(detail=True, methods=['get'])
    def comisiones(self, request, pk=None):
        """Calcular comisiones del vendedor en un período"""
        vendedor = self.get_object()
        from ventas.models import Factura
        
        # Obtener parámetros de fecha (opcional)
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        facturas = Factura.objects.filter(vendedor=vendedor, estado__in=['PAGADA', 'PAGADA_PARCIAL'])
        
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                facturas = facturas.filter(fecha__date__gte=fecha_inicio)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_fin:
            try:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                facturas = facturas.filter(fecha__date__lte=fecha_fin)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calcular comisiones
        monto_total_ventas = facturas.aggregate(total=Sum('total'))['total'] or 0
        monto_comisiones = (monto_total_ventas * vendedor.comision_porcentaje) / 100
        
        # Detalle de comisiones por factura
        detalle_comisiones = []
        for factura in facturas:
            comision_factura = (factura.total * vendedor.comision_porcentaje) / 100
            detalle_comisiones.append({
                'factura_id': factura.id,
                'numero_factura': factura.numero_factura,
                'fecha': factura.fecha,
                'cliente': factura.cliente.nombre,
                'monto_venta': float(factura.total),
                'comision': float(comision_factura)
            })
        
        return Response({
            'vendedor': vendedor.nombre,
            'comision_porcentaje': float(vendedor.comision_porcentaje),
            'periodo': {
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else None,
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d') if fecha_fin else None
            },
            'resumen': {
                'total_ventas': facturas.count(),
                'monto_total_ventas': float(monto_total_ventas),
                'monto_total_comisiones': float(monto_comisiones)
            },
            'detalle': detalle_comisiones
        })

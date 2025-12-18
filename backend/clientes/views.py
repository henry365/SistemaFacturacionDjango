from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from .models import Cliente, CategoriaCliente
from .serializers import ClienteSerializer, CategoriaClienteSerializer
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
from ventas.models import Factura, PagoCaja

class CategoriaClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = CategoriaCliente.objects.all()
    serializer_class = CategoriaClienteSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'descuento_porcentaje', 'fecha_creacion']
    ordering = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtro por activa
        activa = self.request.query_params.get('activa')
        if activa is not None:
            queryset = queryset.filter(activa=activa.lower() == 'true')
        return queryset

class ClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'numero_identificacion', 'telefono', 'correo_electronico']
    ordering_fields = ['nombre', 'fecha_creacion', 'limite_credito']
    ordering = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtros específicos
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        vendedor = self.request.query_params.get('vendedor')
        if vendedor:
            queryset = queryset.filter(vendedor_asignado_id=vendedor)
        
        tipo_identificacion = self.request.query_params.get('tipo_identificacion')
        if tipo_identificacion:
            queryset = queryset.filter(tipo_identificacion=tipo_identificacion)
        
        return queryset

    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """Obtener historial de facturas del cliente"""
        cliente = self.get_object()
        facturas = Factura.objects.filter(cliente=cliente).order_by('-fecha')
        
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
        
        return Response({
            'cliente': cliente.nombre,
            'total_facturas': len(data),
            'total_ventas': sum(float(f['total']) for f in data),
            'total_pendiente': sum(float(f['monto_pendiente']) for f in data),
            'facturas': data
        })

    @action(detail=True, methods=['get'])
    def historial_pagos(self, request, pk=None):
        """Obtener historial de pagos del cliente"""
        cliente = self.get_object()
        pagos = PagoCaja.objects.filter(cliente=cliente).order_by('-fecha_pago')
        
        data = [{
            'id': p.id,
            'fecha': p.fecha_pago,
            'monto': float(p.monto),
            'metodo': p.metodo_pago,
            'referencia': p.referencia,
            'factura': p.factura.numero_factura if p.factura else None
        } for p in pagos]
        
        return Response({
            'cliente': cliente.nombre,
            'total_pagos': len(data),
            'total_monto': sum(float(p['monto']) for p in data),
            'pagos': data
        })

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Resumen completo del cliente con estadísticas"""
        cliente = self.get_object()
        
        # Estadísticas de facturas
        facturas = Factura.objects.filter(cliente=cliente)
        total_facturas = facturas.count()
        total_ventas = facturas.aggregate(total=Sum('total'))['total'] or 0
        total_pendiente = facturas.aggregate(total=Sum('monto_pendiente'))['total'] or 0
        
        # Estadísticas de pagos
        pagos = PagoCaja.objects.filter(cliente=cliente)
        total_pagos = pagos.count()
        total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or 0
        
        return Response({
            'cliente': ClienteSerializer(cliente).data,
            'estadisticas': {
                'total_facturas': total_facturas,
                'total_ventas': float(total_ventas),
                'total_pendiente': float(total_pendiente),
                'total_pagado': float(total_pagado),
                'saldo_actual': float(total_pendiente),
                'limite_credito': float(cliente.limite_credito),
                'credito_disponible': float(cliente.limite_credito - total_pendiente) if cliente.limite_credito else None
            }
        })

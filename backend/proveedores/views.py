from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Proveedor
from .serializers import ProveedorSerializer
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin

class ProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'numero_identificacion', 'telefono', 'correo_electronico']
    ordering_fields = ['nombre', 'fecha_creacion', 'tipo_contribuyente']
    ordering = ['nombre']

    def get_queryset(self):
        """Filtrar proveedores según empresa del usuario"""
        queryset = super().get_queryset()
        # Filtros específicos
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        tipo_identificacion = self.request.query_params.get('tipo_identificacion')
        if tipo_identificacion:
            queryset = queryset.filter(tipo_identificacion=tipo_identificacion)
        
        tipo_contribuyente = self.request.query_params.get('tipo_contribuyente')
        if tipo_contribuyente:
            queryset = queryset.filter(tipo_contribuyente=tipo_contribuyente)
        
        es_internacional = self.request.query_params.get('es_internacional')
        if es_internacional is not None:
            queryset = queryset.filter(es_internacional=es_internacional.lower() == 'true')
        
        return queryset

    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """Obtener historial de compras del proveedor"""
        proveedor = self.get_object()
        from compras.models import Compra
        
        compras = Compra.objects.filter(proveedor=proveedor).order_by('-fecha_compra')
        
        data = [{
            'id': c.id,
            'numero_factura': c.numero_factura_proveedor,
            'ncf': c.numero_ncf,
            'fecha_compra': c.fecha_compra,
            'total': float(c.total),
            'estado': c.estado,
            'monto_pagado': float(c.monto_pagado),
            'monto_pendiente': float(c.total - c.monto_pagado),
            'tipo_gasto': c.tipo_gasto
        } for c in compras]
        
        return Response({
            'proveedor': proveedor.nombre,
            'total_compras': len(data),
            'total_comprado': sum(float(c['total']) for c in data),
            'total_pagado': sum(float(c['monto_pagado']) for c in data),
            'total_pendiente': sum(float(c['monto_pendiente']) for c in data),
            'compras': data
        })

    @action(detail=True, methods=['get'])
    def historial_ordenes(self, request, pk=None):
        """Obtener historial de órdenes de compra del proveedor"""
        proveedor = self.get_object()
        from compras.models import OrdenCompra
        
        ordenes = OrdenCompra.objects.filter(proveedor=proveedor).order_by('-fecha_emision')
        
        data = [{
            'id': o.id,
            'fecha_emision': o.fecha_emision,
            'fecha_entrega_esperada': o.fecha_entrega_esperada,
            'estado': o.estado,
            'total': float(o.total),
            'subtotal': float(o.subtotal),
            'impuestos': float(o.impuestos),
            'descuentos': float(o.descuentos)
        } for o in ordenes]
        
        return Response({
            'proveedor': proveedor.nombre,
            'total_ordenes': len(data),
            'total_ordenado': sum(float(o['total']) for o in data),
            'ordenes': data
        })

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Resumen completo del proveedor con estadísticas"""
        proveedor = self.get_object()
        from compras.models import Compra, OrdenCompra
        
        # Estadísticas de compras
        compras = Compra.objects.filter(proveedor=proveedor)
        total_compras = compras.count()
        total_comprado = compras.aggregate(total=Sum('total'))['total'] or 0
        total_pagado = compras.aggregate(total=Sum('monto_pagado'))['total'] or 0
        total_pendiente = total_comprado - total_pagado
        
        # Estadísticas de órdenes
        ordenes = OrdenCompra.objects.filter(proveedor=proveedor)
        total_ordenes = ordenes.count()
        total_ordenado = ordenes.aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'proveedor': ProveedorSerializer(proveedor).data,
            'estadisticas': {
                'total_compras': total_compras,
                'total_comprado': float(total_comprado),
                'total_pagado': float(total_pagado),
                'total_pendiente': float(total_pendiente),
                'total_ordenes': total_ordenes,
                'total_ordenado': float(total_ordenado),
            }
        })

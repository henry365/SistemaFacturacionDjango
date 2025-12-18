from rest_framework import viewsets, permissions, filters
from .models import (
    CotizacionCliente, Factura, PagoCaja, 
    NotaCredito, NotaDebito, DevolucionVenta,
    ListaEsperaProducto
)
from .serializers import (
    CotizacionClienteSerializer, FacturaSerializer, PagoCajaSerializer,
    NotaCreditoSerializer, NotaDebitoSerializer, DevolucionVentaSerializer,
    ListaEsperaProductoSerializer
)
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin

class ListaEsperaProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = ListaEsperaProducto.objects.all()
    serializer_class = ListaEsperaProductoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'producto__nombre']
    ordering_fields = ['fecha_solicitud', 'prioridad']
    ordering = ['-fecha_solicitud']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

class CotizacionClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = CotizacionCliente.objects.all()
    serializer_class = CotizacionClienteSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre']
    ordering_fields = ['fecha', 'estado']
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

class FacturaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_factura', 'cliente__nombre']
    ordering_fields = ['fecha', 'total', 'estado']
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset

class PagoCajaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = PagoCaja.objects.all()
    serializer_class = PagoCajaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'referencia']
    ordering_fields = ['fecha_pago']
    ordering = ['-fecha_pago']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset

class NotaCreditoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = NotaCredito.objects.all()
    serializer_class = NotaCreditoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset

class NotaDebitoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = NotaDebito.objects.all()
    serializer_class = NotaDebitoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset

class DevolucionVentaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = DevolucionVenta.objects.all()
    serializer_class = DevolucionVentaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'factura__numero_factura']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset

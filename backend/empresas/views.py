from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import Empresa
from .serializers import EmpresaSerializer
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin

class EmpresaViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar empresas.
    
    Las empresas son la base del sistema multiempresa.
    Cada usuario puede estar asociado a una empresa y solo verá datos de su empresa.
    """
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'rnc', 'telefono', 'direccion']
    ordering_fields = ['nombre', 'rnc', 'fecha_creacion', 'activo']
    ordering = ['nombre']

    def get_queryset(self):
        """Filtrar empresas según permisos del usuario"""
        queryset = super().get_queryset()
        
        # Si el usuario tiene una empresa asignada, solo puede ver su empresa
        # Los superusuarios pueden ver todas las empresas
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser or user.is_staff:
                # Superusuarios y staff pueden ver todas las empresas
                pass
            elif hasattr(user, 'empresa') and user.empresa:
                # Usuarios normales solo ven su empresa
                queryset = queryset.filter(id=user.empresa.id)
        
        # Filtro por activo
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        return queryset

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas de la empresa"""
        empresa = self.get_object()
        
        # Importar modelos relacionados
        from clientes.models import Cliente
        from proveedores.models import Proveedor
        from productos.models import Producto
        from ventas.models import Factura
        from compras.models import Compra
        
        # Estadísticas básicas de la empresa
        estadisticas = {
            'empresa': EmpresaSerializer(empresa).data,
            'resumen': {
                'total_clientes': Cliente.objects.filter(empresa=empresa).count(),
            }
        }
        
        # Estadísticas de facturas (filtradas por cliente__empresa)
        facturas = Factura.objects.filter(cliente__empresa=empresa)
        estadisticas['resumen']['total_facturas'] = facturas.count()
        estadisticas['resumen']['total_ventas'] = float(facturas.aggregate(total=Sum('total'))['total'] or 0)
        estadisticas['resumen']['ventas_pendientes'] = float(facturas.aggregate(total=Sum('monto_pendiente'))['total'] or 0)
        
        # Estadísticas adicionales (solo si los modelos tienen campo empresa)
        # Proveedores
        try:
            if 'empresa' in [f.name for f in Proveedor._meta.get_fields()]:
                estadisticas['resumen']['total_proveedores'] = Proveedor.objects.filter(empresa=empresa).count()
            else:
                estadisticas['resumen']['total_proveedores'] = Proveedor.objects.count()
        except:
            estadisticas['resumen']['total_proveedores'] = 0
        
        # Productos
        try:
            if 'empresa' in [f.name for f in Producto._meta.get_fields()]:
                estadisticas['resumen']['total_productos'] = Producto.objects.filter(empresa=empresa).count()
            else:
                estadisticas['resumen']['total_productos'] = Producto.objects.count()
        except:
            estadisticas['resumen']['total_productos'] = 0
        
        # Compras
        try:
            estadisticas['resumen']['total_compras'] = Compra.objects.count()
        except:
            estadisticas['resumen']['total_compras'] = 0
        
        return Response(estadisticas)

    @action(detail=True, methods=['get'])
    def configuracion_fiscal(self, request, pk=None):
        """Obtener o actualizar configuración fiscal"""
        empresa = self.get_object()
        return Response({
            'empresa': empresa.nombre,
            'configuracion_fiscal': empresa.configuracion_fiscal
        })

    @action(detail=True, methods=['patch'])
    def actualizar_configuracion_fiscal(self, request, pk=None):
        """Actualizar configuración fiscal"""
        empresa = self.get_object()
        nueva_config = request.data.get('configuracion_fiscal')
        
        if nueva_config is None:
            return Response(
                {'error': 'Se requiere el campo configuracion_fiscal'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(nueva_config, dict):
            return Response(
                {'error': 'configuracion_fiscal debe ser un objeto JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar configuración fiscal
        empresa.configuracion_fiscal = nueva_config
        empresa.save()
        
        return Response({
            'mensaje': 'Configuración fiscal actualizada correctamente',
            'configuracion_fiscal': empresa.configuracion_fiscal
        })

    @action(detail=False, methods=['get'])
    def mi_empresa(self, request):
        """Obtener la empresa del usuario autenticado"""
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if hasattr(user, 'empresa') and user.empresa:
            serializer = self.get_serializer(user.empresa)
            return Response(serializer.data)
        
        return Response(
            {'error': 'El usuario no tiene una empresa asignada'},
            status=status.HTTP_404_NOT_FOUND
        )

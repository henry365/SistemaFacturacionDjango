from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import CustomTokenObtainPairView, validar_empresa, UserViewSet, GroupViewSet, PermissionViewSet

router = DefaultRouter()

# Views
from empresas.views import EmpresaViewSet
from clientes.views import ClienteViewSet, CategoriaClienteViewSet
from productos.views import ProductoViewSet, CategoriaViewSet, ImagenProductoViewSet, ReferenciasCruzadasViewSet
from vendedores.views import VendedorViewSet
from proveedores.views import ProveedorViewSet
from compras.views import (
    SolicitudCotizacionProveedorViewSet,
    OrdenCompraViewSet,
    CompraViewSet,
    GastoViewSet,
    RecepcionCompraViewSet,
    DevolucionProveedorViewSet,
    LiquidacionImportacionViewSet,
    TipoRetencionViewSet,
    RetencionCompraViewSet
)
from ventas.views import (
    CotizacionClienteViewSet, 
    FacturaViewSet, 
    PagoCajaViewSet, 
    NotaCreditoViewSet, 
    NotaDebitoViewSet, 
    DevolucionVentaViewSet,
    ListaEsperaProductoViewSet
)
from inventario.views import (
    AlmacenViewSet, 
    InventarioProductoViewSet, 
    MovimientoInventarioViewSet,
    ReservaStockViewSet,
    LoteViewSet,
    AlertaInventarioViewSet,
    TransferenciaInventarioViewSet,
    DetalleTransferenciaViewSet,
    AjusteInventarioViewSet,
    DetalleAjusteInventarioViewSet,
    ConteoFisicoViewSet,
    DetalleConteoFisicoViewSet
)
from despachos.views import DespachoViewSet, DetalleDespachoViewSet
from caja.views import CajaViewSet, SesionCajaViewSet, MovimientoCajaViewSet
from cuentas_pagar.views import CuentaPorPagarViewSet, PagoProveedorViewSet, DetallePagoProveedorViewSet
from cuentas_cobrar.views import CuentaPorCobrarViewSet, CobroClienteViewSet, DetalleCobroClienteViewSet
from dgii.views import TipoComprobanteViewSet, SecuenciaNCFViewSet, ReportesDGIIViewSet
from activos.views import TipoActivoViewSet, ActivoFijoViewSet, DepreciacionViewSet
from dashboard.views import DashboardViewSet
from core.views import ConfiguracionEmpresaViewSet

# Catálogos
router.register(r'usuarios', UserViewSet)
router.register(r'grupos', GroupViewSet)
router.register(r'permisos', PermissionViewSet)
router.register(r'empresas', EmpresaViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'categorias-clientes', CategoriaClienteViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'imagenes-producto', ImagenProductoViewSet, basename='imagenes-producto')
router.register(r'referencias-producto', ReferenciasCruzadasViewSet, basename='referencias-producto')
router.register(r'categorias', CategoriaViewSet)
router.register(r'vendedores', VendedorViewSet)
router.register(r'almacenes', AlmacenViewSet)

# Compras
router.register(r'compras/solicitudes', SolicitudCotizacionProveedorViewSet)
router.register(r'compras/ordenes', OrdenCompraViewSet)
router.register(r'compras/facturas', CompraViewSet)
router.register(r'compras/gastos', GastoViewSet)
router.register(r'compras/recepciones', RecepcionCompraViewSet)
router.register(r'compras/devoluciones', DevolucionProveedorViewSet)
router.register(r'compras/liquidaciones', LiquidacionImportacionViewSet)
router.register(r'compras/tipos-retencion', TipoRetencionViewSet)
router.register(r'compras/retenciones', RetencionCompraViewSet)

# Ventas
router.register(r'ventas/cotizaciones', CotizacionClienteViewSet)
router.register(r'ventas/facturas', FacturaViewSet)
router.register(r'ventas/pagos', PagoCajaViewSet)
router.register(r'ventas/notas-credito', NotaCreditoViewSet)
router.register(r'ventas/notas-debito', NotaDebitoViewSet)
router.register(r'ventas/devoluciones', DevolucionVentaViewSet)
router.register(r'ventas/lista-espera', ListaEsperaProductoViewSet)

# Inventario y Despachos
router.register(r'inventario/existencias', InventarioProductoViewSet)
router.register(r'inventario/movimientos', MovimientoInventarioViewSet)
router.register(r'inventario/reservas', ReservaStockViewSet)
router.register(r'inventario/lotes', LoteViewSet)
router.register(r'inventario/alertas', AlertaInventarioViewSet)
router.register(r'inventario/transferencias', TransferenciaInventarioViewSet)
router.register(r'inventario/transferencias-detalles', DetalleTransferenciaViewSet)
router.register(r'inventario/ajustes', AjusteInventarioViewSet)
router.register(r'inventario/ajustes-detalles', DetalleAjusteInventarioViewSet)
router.register(r'inventario/conteos-fisicos', ConteoFisicoViewSet)
router.register(r'inventario/conteos-fisicos-detalles', DetalleConteoFisicoViewSet)
router.register(r'despachos', DespachoViewSet)
router.register(r'despachos-detalles', DetalleDespachoViewSet)

# Caja
router.register(r'caja/cajas', CajaViewSet)
router.register(r'caja/sesiones', SesionCajaViewSet)
router.register(r'caja/movimientos', MovimientoCajaViewSet)

# Cuentas por Pagar
router.register(r'cxp/cuentas', CuentaPorPagarViewSet)
router.register(r'cxp/pagos', PagoProveedorViewSet)
router.register(r'cxp/pagos-detalle', DetallePagoProveedorViewSet)

# Cuentas por Cobrar
router.register(r'cxc/cuentas', CuentaPorCobrarViewSet)
router.register(r'cxc/cobros', CobroClienteViewSet)
router.register(r'cxc/cobros-detalle', DetalleCobroClienteViewSet)

# DGII (Comprobantes Fiscales)
router.register(r'dgii/tipos-comprobante', TipoComprobanteViewSet)
router.register(r'dgii/secuencias', SecuenciaNCFViewSet)
router.register(r'dgii/reportes', ReportesDGIIViewSet, basename='dgii-reportes')

# Activos Fijos
router.register(r'activos/tipos', TipoActivoViewSet)
router.register(r'activos/activos', ActivoFijoViewSet)
router.register(r'activos/depreciaciones', DepreciacionViewSet)

# Dashboard
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Configuración del Sistema
router.register(r'configuracion', ConfiguracionEmpresaViewSet, basename='configuracion')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/validar-empresa/', validar_empresa, name='validar_empresa'),
    path('api/v1/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

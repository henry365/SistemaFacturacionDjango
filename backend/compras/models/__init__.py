"""
Modelos del módulo de Compras.

Este paquete organiza los modelos en archivos separados
para mejor mantenibilidad (KISS principle).

Estructura:
- solicitudes.py: SolicitudCotizacionProveedor
- ordenes.py: OrdenCompra, DetalleOrdenCompra
- compras.py: Compra, DetalleCompra, Gasto
- recepciones.py: RecepcionCompra, DetalleRecepcion, DevolucionProveedor, DetalleDevolucionProveedor
- importaciones.py: LiquidacionImportacion, GastoImportacion, TipoRetencion, RetencionCompra
"""

# Solicitudes
from .solicitudes import SolicitudCotizacionProveedor

# Órdenes de compra
from .ordenes import OrdenCompra, DetalleOrdenCompra

# Compras y gastos
from .compras import Compra, DetalleCompra, Gasto

# Recepciones y devoluciones
from .recepciones import (
    RecepcionCompra,
    DetalleRecepcion,
    DevolucionProveedor,
    DetalleDevolucionProveedor,
)

# Importaciones y retenciones
from .importaciones import (
    LiquidacionImportacion,
    GastoImportacion,
    TipoRetencion,
    RetencionCompra,
)

__all__ = [
    # Solicitudes
    'SolicitudCotizacionProveedor',
    # Órdenes
    'OrdenCompra',
    'DetalleOrdenCompra',
    # Compras
    'Compra',
    'DetalleCompra',
    'Gasto',
    # Recepciones
    'RecepcionCompra',
    'DetalleRecepcion',
    'DevolucionProveedor',
    'DetalleDevolucionProveedor',
    # Importaciones
    'LiquidacionImportacion',
    'GastoImportacion',
    'TipoRetencion',
    'RetencionCompra',
]

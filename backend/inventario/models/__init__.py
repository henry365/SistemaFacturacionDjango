"""
Modelos del módulo de Inventario.

Este paquete organiza los modelos en archivos separados
para mejor mantenibilidad (KISS principle).

Estructura:
- almacen.py: Almacen, InventarioProducto (con QuerySet y Manager)
- movimientos.py: MovimientoInventario, ReservaStock, Lote, AlertaInventario
- transferencias.py: TransferenciaInventario, DetalleTransferencia
- ajustes.py: AjusteInventario, DetalleAjusteInventario, ConteoFisico, DetalleConteoFisico
"""

# Almacén e inventario
from .almacen import (
    Almacen,
    InventarioProducto,
    InventarioProductoManager,
    InventarioProductoQuerySet,
)

# Movimientos, reservas, lotes y alertas
from .movimientos import (
    MovimientoInventario,
    ReservaStock,
    Lote,
    AlertaInventario,
)

# Transferencias
from .transferencias import (
    TransferenciaInventario,
    DetalleTransferencia,
)

# Ajustes y conteos
from .ajustes import (
    AjusteInventario,
    DetalleAjusteInventario,
    ConteoFisico,
    DetalleConteoFisico,
)

__all__ = [
    # Almacén
    'Almacen',
    'InventarioProducto',
    'InventarioProductoManager',
    'InventarioProductoQuerySet',
    # Movimientos
    'MovimientoInventario',
    'ReservaStock',
    'Lote',
    'AlertaInventario',
    # Transferencias
    'TransferenciaInventario',
    'DetalleTransferencia',
    # Ajustes
    'AjusteInventario',
    'DetalleAjusteInventario',
    'ConteoFisico',
    'DetalleConteoFisico',
]

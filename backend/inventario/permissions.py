"""
Permisos personalizados para el módulo Inventario

Este módulo define permisos específicos para acciones críticas en el módulo
de inventario, heredando de BaseEmpresaPermission para mantener consistencia
con los estándares del proyecto.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarAlmacen(BaseEmpresaPermission):
    """
    Permiso para gestionar almacenes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_almacen'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_almacen',
            message='No tiene permiso para gestionar almacenes.'
        )


class CanGestionarInventario(BaseEmpresaPermission):
    """
    Permiso para gestionar inventario de productos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_inventarioproducto'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_inventarioproducto',
            message='No tiene permiso para gestionar inventario.'
        )


class CanGestionarMovimientos(BaseEmpresaPermission):
    """
    Permiso para gestionar movimientos de inventario.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_movimientoinventario'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_movimientoinventario',
            message='No tiene permiso para gestionar movimientos.'
        )


class CanGestionarReservas(BaseEmpresaPermission):
    """
    Permiso para gestionar reservas de stock.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_reservastock'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_reservastock',
            message='No tiene permiso para gestionar reservas.'
        )


class CanGestionarLotes(BaseEmpresaPermission):
    """
    Permiso para gestionar lotes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_lote'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_lote',
            message='No tiene permiso para gestionar lotes.'
        )


class CanGestionarAlertas(BaseEmpresaPermission):
    """
    Permiso para gestionar alertas de inventario.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_alertainventario'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_alertainventario',
            message='No tiene permiso para gestionar alertas.'
        )


class CanGestionarTransferencias(BaseEmpresaPermission):
    """
    Permiso para gestionar transferencias entre almacenes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_transferenciainventario'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_transferenciainventario',
            message='No tiene permiso para gestionar transferencias.'
        )


class CanGestionarAjustes(BaseEmpresaPermission):
    """
    Permiso para gestionar ajustes de inventario.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_ajusteinventario'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_ajusteinventario',
            message='No tiene permiso para gestionar ajustes.'
        )


class CanAprobarAjustes(BaseEmpresaPermission):
    """
    Permiso para aprobar ajustes de inventario.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.aprobar_ajusteinventario'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.aprobar_ajusteinventario',
            message='No tiene permiso para aprobar ajustes.'
        )


class CanGestionarConteos(BaseEmpresaPermission):
    """
    Permiso para gestionar conteos físicos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.gestionar_conteofisico'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.gestionar_conteofisico',
            message='No tiene permiso para gestionar conteos físicos.'
        )


class CanVerKardex(BaseEmpresaPermission):
    """
    Permiso para ver Kardex.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'inventario.ver_kardex'
    """

    def __init__(self):
        super().__init__(
            permission_codename='inventario.ver_kardex',
            message='No tiene permiso para ver Kardex.'
        )

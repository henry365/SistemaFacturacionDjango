"""
Permisos personalizados para el módulo Compras

Este módulo define permisos específicos para acciones críticas en el módulo
de compras, heredando de BaseEmpresaPermission para mantener consistencia
con los estándares del proyecto.
"""
from core.permissions import BaseEmpresaPermission


class CanAprobarOrdenCompra(BaseEmpresaPermission):
    """
    Permiso para aprobar órdenes de compra.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.aprobar_ordencompra'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.aprobar_ordencompra',
            message='No tiene permiso para aprobar órdenes de compra.'
        )


class CanConfirmarRecepcion(BaseEmpresaPermission):
    """
    Permiso para confirmar recepciones de compra.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.confirmar_recepcioncompra'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.confirmar_recepcioncompra',
            message='No tiene permiso para confirmar recepciones de compra.'
        )


class CanConfirmarDevolucion(BaseEmpresaPermission):
    """
    Permiso para confirmar devoluciones a proveedores.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.confirmar_devolucionproveedor'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.confirmar_devolucionproveedor',
            message='No tiene permiso para confirmar devoluciones a proveedores.'
        )


class CanLiquidarImportacion(BaseEmpresaPermission):
    """
    Permiso para liquidar importaciones.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.liquidar_liquidacionimportacion'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.liquidar_liquidacionimportacion',
            message='No tiene permiso para liquidar importaciones.'
        )


class CanAnularCompra(BaseEmpresaPermission):
    """
    Permiso para anular compras.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.anular_compra'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.anular_compra',
            message='No tiene permiso para anular compras.'
        )


class CanCancelarOrdenCompra(BaseEmpresaPermission):
    """
    Permiso para cancelar órdenes de compra.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.cancelar_ordencompra'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.cancelar_ordencompra',
            message='No tiene permiso para cancelar órdenes de compra.'
        )


class CanAplicarRetencion(BaseEmpresaPermission):
    """
    Permiso para aplicar retenciones a compras.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'compras.add_retencioncompra'
    """

    def __init__(self):
        super().__init__(
            permission_codename='compras.add_retencioncompra',
            message='No tiene permiso para aplicar retenciones a compras.'
        )

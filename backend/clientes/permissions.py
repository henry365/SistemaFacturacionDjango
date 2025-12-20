"""
Permisos personalizados para el módulo de Clientes

Este módulo define permisos específicos para el módulo de clientes,
heredando de las clases base genéricas para mantener consistencia
y eliminar código duplicado (DRY).
"""
from core.permissions.base import BaseEmpresaPermission


class CanViewClienteHistorial(BaseEmpresaPermission):
    """
    Permiso para ver historial de compras/pagos de cliente.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'clientes.view_cliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='clientes.view_cliente',
            message='No tiene permiso para ver el historial del cliente.'
        )


class CanManageLimiteCredito(BaseEmpresaPermission):
    """
    Permiso para modificar límite de crédito de cliente.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'clientes.change_cliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='clientes.change_cliente',
            message='No tiene permiso para modificar el límite de crédito.'
        )


class CanActivateDeactivateCliente(BaseEmpresaPermission):
    """
    Permiso para activar/desactivar clientes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'clientes.change_cliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='clientes.change_cliente',
            message='No tiene permiso para activar/desactivar clientes.'
        )


class CanManageCategoria(BaseEmpresaPermission):
    """
    Permiso para gestionar categorías de clientes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'clientes.change_categoriacliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='clientes.change_categoriacliente',
            message='No tiene permiso para gestionar categorías de clientes.'
        )


class CanViewClienteResumen(BaseEmpresaPermission):
    """
    Permiso para ver resumen/estadísticas de cliente.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'clientes.view_cliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='clientes.view_cliente',
            message='No tiene permiso para ver el resumen del cliente.'
        )

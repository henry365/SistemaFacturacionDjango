"""
Permisos personalizados para el módulo Vendedores

Este módulo define permisos específicos para gestión de vendedores
utilizando BaseEmpresaPermission para validar multi-tenancy.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarVendedor(BaseEmpresaPermission):
    """
    Permiso para gestionar vendedores.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'vendedores.gestionar_vendedor'
    - Y pertenece a la misma empresa que el vendedor
    """

    def __init__(self):
        super().__init__(
            permission_codename='vendedores.gestionar_vendedor',
            message='No tiene permiso para gestionar vendedores.'
        )

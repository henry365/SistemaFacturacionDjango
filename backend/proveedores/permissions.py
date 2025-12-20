"""
Permisos personalizados para el módulo Proveedores

Este módulo define permisos específicos para acciones en el módulo
de proveedores, heredando de BaseEmpresaPermission para mantener consistencia
con los estándares del proyecto.

Incluye validación de empresa (multi-tenancy) para todos los objetos.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarProveedor(BaseEmpresaPermission):
    """
    Permiso para gestionar proveedores.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'proveedores.gestionar_proveedor'
    - Y pertenece a la misma empresa que el proveedor
    """

    def __init__(self):
        super().__init__(
            permission_codename='proveedores.gestionar_proveedor',
            message='No tiene permiso para gestionar proveedores.'
        )

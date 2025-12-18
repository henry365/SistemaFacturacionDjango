"""
Infraestructura Global de Permisos

Este paquete proporciona clases base genéricas y mixins reutilizables
para el manejo de permisos en todo el sistema.

Uso básico:
    from core.permissions import BaseEmpresaPermission

    class CanActionModel(BaseEmpresaPermission):
        def __init__(self):
            super().__init__(
                permission_codename='app.action_model',
                message='No tiene permiso.'
            )

Clases base disponibles:
    - BaseEmpresaPermission: Permiso con validación de empresa
    - BaseModelPermission: Permiso para modelos específicos
    - BaseActionPermission: Permiso para acciones personalizadas
    - BaseReadOnlyPermission: Permiso de solo lectura

Mixins disponibles:
    - EmpresaValidationMixin: Validación de empresa
    - AdminStaffMixin: Verificación de admin/staff
    - PermissionCheckMixin: Verificación de permisos
    - OwnerValidationMixin: Validación de propiedad
    - ResponsableValidationMixin: Validación de responsable
"""

# Clases base
from .base import (
    BaseEmpresaPermission,
    BaseModelPermission,
    BaseActionPermission,
    BaseReadOnlyPermission,
)

# Mixins
from .mixins import (
    EmpresaValidationMixin,
    AdminStaffMixin,
    PermissionCheckMixin,
    OwnerValidationMixin,
    ResponsableValidationMixin,
)

__all__ = [
    # Clases base
    'BaseEmpresaPermission',
    'BaseModelPermission',
    'BaseActionPermission',
    'BaseReadOnlyPermission',
    # Mixins
    'EmpresaValidationMixin',
    'AdminStaffMixin',
    'PermissionCheckMixin',
    'OwnerValidationMixin',
    'ResponsableValidationMixin',
]

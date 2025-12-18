"""
Infraestructura Global de Permisos

Este paquete proporciona clases base genéricas, mixins reutilizables
y utilidades para el manejo de permisos en todo el sistema.

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

Utilidades disponibles:
    - check_permission: Verificar permiso con admin/staff bypass
    - check_empresa_permission: Verificar permiso + misma empresa
    - user_has_any_permission: Verificar si tiene alguno de los permisos
    - user_has_all_permissions: Verificar si tiene todos los permisos
    - belongs_to_same_empresa: Verificar si objeto pertenece a empresa del usuario
    - require_permission: Decorador para asignar permiso a acción
    - require_same_empresa: Decorador para verificar misma empresa
    - create_user_with_permission: Helper de testing
    - create_mock_request: Helper de testing
    - assert_has_permission: Helper de testing
    - create_test_empresa: Helper de testing
    - get_cached_permission: Verificación con caché
    - log_permission_check: Logging de verificaciones
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

# Utilidades
from .utils import (
    # Helpers de verificación
    check_permission,
    check_empresa_permission,
    user_has_any_permission,
    user_has_all_permissions,
    belongs_to_same_empresa,
    # Decoradores
    require_permission,
    require_same_empresa,
    # Helpers de testing
    create_user_with_permission,
    create_mock_request,
    assert_has_permission,
    create_test_empresa,
    # Utilidades avanzadas
    get_cached_permission,
    invalidate_permission_cache,
    log_permission_check,
    get_user_permissions_summary,
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
    # Utilidades - Helpers de verificación
    'check_permission',
    'check_empresa_permission',
    'user_has_any_permission',
    'user_has_all_permissions',
    'belongs_to_same_empresa',
    # Utilidades - Decoradores
    'require_permission',
    'require_same_empresa',
    # Utilidades - Testing
    'create_user_with_permission',
    'create_mock_request',
    'assert_has_permission',
    'create_test_empresa',
    # Utilidades - Avanzadas
    'get_cached_permission',
    'invalidate_permission_cache',
    'log_permission_check',
    'get_user_permissions_summary',
]

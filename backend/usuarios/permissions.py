"""
Permisos personalizados para el módulo de Usuarios

Usa las clases base genéricas de core.permissions para
eliminar código duplicado y mantener consistencia.

Siguiendo la Guía Inicial:
- Todos los permisos heredan de BaseEmpresaPermission
- NO se crean permisos desde cero (DRY)
"""
from rest_framework import permissions

from core.permissions.base import BaseEmpresaPermission, BaseReadOnlyPermission
from core.permissions.mixins import (
    AdminStaffMixin,
    EmpresaValidationMixin,
    OwnerValidationMixin,
)


class ActionBasedPermission(permissions.DjangoModelPermissions):
    """
    Clase de permiso extendida que mapea acciones de DRF a permisos de Django.

    Mapeo por defecto:
    - GET (list/retrieve) -> view_model
    - POST (create) -> add_model
    - PUT/PATCH (update) -> change_model
    - DELETE (destroy) -> delete_model

    Para acciones custom (@action), se puede definir el permiso requerido usando
    el decorador @require_permission o en el atributo 'permission_required' de la acción.
    """

    def __init__(self):
        super().__init__()
        self.perms_map = {
            'GET': ['%(app_label)s.view_%(model_name)s'],
            'OPTIONS': [],
            'HEAD': [],
            'POST': ['%(app_label)s.add_%(model_name)s'],
            'PUT': ['%(app_label)s.change_%(model_name)s'],
            'PATCH': ['%(app_label)s.change_%(model_name)s'],
            'DELETE': ['%(app_label)s.delete_%(model_name)s'],
        }

    def has_permission(self, request, view):
        # Permitir acceso a usuarios autenticados para endpoints sin modelo (si los hay)
        if not hasattr(view, 'queryset') or view.queryset is None:
            return True

        # Verificar permisos específicos para acciones personalizadas
        if hasattr(view, 'action') and view.action:
            # Verificar si la acción tiene un permiso específico definido
            action_method = getattr(view, view.action, None)
            if action_method:
                permission_required = getattr(action_method, 'permission_required', None)
                if permission_required:
                    if isinstance(permission_required, str):
                        permission_required = [permission_required]
                    return request.user.has_perms(permission_required)

        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.
        Por defecto, permite si el usuario tiene el permiso a nivel de modelo.
        """
        # Llamar al método padre para verificar permisos básicos
        if not super().has_object_permission(request, view, obj):
            return False

        # Verificar permisos específicos para acciones personalizadas en objetos
        if hasattr(view, 'action') and view.action:
            action_method = getattr(view, view.action, None)
            if action_method:
                permission_required = getattr(action_method, 'permission_required', None)
                if permission_required:
                    if isinstance(permission_required, str):
                        permission_required = [permission_required]
                    return request.user.has_perms(permission_required)

        return True


class IsAdminUserOrReadOnly(AdminStaffMixin, permissions.BasePermission):
    """
    Permiso que permite lectura a todos y escritura solo a admin/staff.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return self._is_admin_or_staff(request.user)


class HasPermissionOrReadOnly(permissions.BasePermission):
    """
    Permiso que requiere un permiso específico para escritura, pero permite lectura.
    """

    def __init__(self, permission_required):
        self.permission_required = permission_required

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.has_perm(self.permission_required)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.has_perm(self.permission_required)


class IsOwnerOrReadOnly(OwnerValidationMixin, AdminStaffMixin, permissions.BasePermission):
    """
    Permiso que permite a los usuarios ver/editar solo sus propios objetos.
    Requiere que el objeto tenga un campo 'usuario' o 'user' o que sea el mismo usuario.
    """

    def has_object_permission(self, request, view, obj):
        # Permitir lectura para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin/staff siempre tienen acceso
        if self._is_admin_or_staff(request.user):
            return True

        # Si el objeto es un User, verificar que sea el mismo usuario
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            if obj.id == request.user.id:
                return True

        # Verificar si es propietario usando el mixin
        return self._is_owner(obj, request.user)


class IsAdminOrSameEmpresa(BaseEmpresaPermission):
    """
    Permiso que permite a administradores todo, o a usuarios normales solo objetos de su empresa.

    Hereda de BaseEmpresaPermission según la Guía Inicial.
    No requiere permission_codename específico - solo valida empresa.
    """

    def __init__(self):
        super().__init__(
            permission_codename=None,  # No requiere permiso específico
            message='No tiene permiso para acceder a este recurso.'
        )

    def has_permission(self, request, view):
        """Todos los autenticados tienen permiso a nivel de vista."""
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        """
        Verifica permiso a nivel de objeto.

        - Superusuarios/staff tienen acceso completo
        - Usuarios normales solo pueden acceder a objetos de su empresa
        - Si el objeto es el mismo usuario, permitir acceso
        """
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if self._is_admin_or_staff(request.user):
            return True

        # Si el objeto es el mismo usuario, permitir acceso
        if hasattr(obj, 'id') and obj.id == request.user.id:
            return True

        # Verificar que pertenezca a la misma empresa
        return self._belongs_to_same_empresa(obj, request.user)


class CanChangeUser(BaseEmpresaPermission):
    """
    Permiso para modificar usuarios.

    Hereda de BaseEmpresaPermission según la Guía Inicial.
    Usado para acciones como activar, desactivar, asignar permisos/grupos.
    """

    def __init__(self):
        super().__init__(
            permission_codename='usuarios.change_user',
            message='No tiene permiso para modificar usuarios.'
        )


class CanDeleteUser(BaseEmpresaPermission):
    """
    Permiso para eliminar usuarios.

    Hereda de BaseEmpresaPermission según la Guía Inicial.
    """

    def __init__(self):
        super().__init__(
            permission_codename='usuarios.delete_user',
            message='No tiene permiso para eliminar usuarios.'
        )


class CanAddUser(BaseEmpresaPermission):
    """
    Permiso para crear usuarios.

    Hereda de BaseEmpresaPermission según la Guía Inicial.
    """

    def __init__(self):
        super().__init__(
            permission_codename='usuarios.add_user',
            message='No tiene permiso para crear usuarios.'
        )


def require_permission(permission):
    """
    Decorador para asignar un permiso específico a una acción personalizada.

    Uso:
        @action(detail=True, methods=['post'])
        @require_permission('usuarios.change_user')
        def activar(self, request, pk=None):
            ...
    """
    def decorator(func):
        func.permission_required = permission
        return func
    return decorator

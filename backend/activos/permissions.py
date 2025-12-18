"""
Permisos personalizados para el módulo de Activos Fijos

Define permisos granulares para operaciones críticas como
depreciación y cambio de estado de activos.
"""
from rest_framework import permissions


class CanDepreciarActivo(permissions.BasePermission):
    """
    Permiso para registrar depreciaciones de activos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.depreciar_activofijo'
    """
    message = 'No tiene permiso para registrar depreciaciones de activos.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        return request.user.has_perm('activos.depreciar_activofijo')

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        if not request.user.has_perm('activos.depreciar_activofijo'):
            return False

        # Verificar que el activo pertenezca a la empresa del usuario
        if hasattr(obj, 'empresa') and hasattr(request.user, 'empresa'):
            return obj.empresa == request.user.empresa

        return False


class CanCambiarEstadoActivo(permissions.BasePermission):
    """
    Permiso para cambiar el estado de activos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.cambiar_estado_activofijo'
    """
    message = 'No tiene permiso para cambiar el estado de activos.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        return request.user.has_perm('activos.cambiar_estado_activofijo')

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        if not request.user.has_perm('activos.cambiar_estado_activofijo'):
            return False

        # Verificar que el activo pertenezca a la empresa del usuario
        if hasattr(obj, 'empresa') and hasattr(request.user, 'empresa'):
            return obj.empresa == request.user.empresa

        return False


class CanVerProyeccion(permissions.BasePermission):
    """
    Permiso para ver proyecciones de depreciación.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.ver_proyeccion_activofijo'
    """
    message = 'No tiene permiso para ver proyecciones de depreciación.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        return request.user.has_perm('activos.ver_proyeccion_activofijo')

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar permiso específico
        if not request.user.has_perm('activos.ver_proyeccion_activofijo'):
            return False

        # Verificar que el activo pertenezca a la empresa del usuario
        if hasattr(obj, 'empresa') and hasattr(request.user, 'empresa'):
            return obj.empresa == request.user.empresa

        return False


class IsActivoResponsable(permissions.BasePermission):
    """
    Permiso que verifica si el usuario es el responsable del activo.

    Útil para permitir que responsables de activos realicen
    ciertas operaciones sobre los activos a su cargo.
    """
    message = 'Solo el responsable del activo puede realizar esta operación.'

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Verificar si el usuario es el responsable
        if hasattr(obj, 'responsable') and obj.responsable:
            return obj.responsable == request.user

        return False

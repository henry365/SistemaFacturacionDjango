"""
Permisos personalizados para el módulo de Activos Fijos

Define permisos granulares para operaciones críticas como
depreciación y cambio de estado de activos.

Usa las clases base genéricas de core.permissions para
eliminar código duplicado y mantener consistencia.
"""
from core.permissions import BaseEmpresaPermission
from core.permissions.mixins import ResponsableValidationMixin, AdminStaffMixin
from rest_framework import permissions


class CanGestionarTipoActivo(BaseEmpresaPermission):
    """
    Permiso para gestionar tipos de activos (CRUD).

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.gestionar_tipo_activo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='activos.gestionar_tipo_activo',
            message='No tiene permiso para gestionar tipos de activos.'
        )


class CanGestionarActivoFijo(BaseEmpresaPermission):
    """
    Permiso para gestionar activos fijos (CRUD).

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.gestionar_activo_fijo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='activos.gestionar_activo_fijo',
            message='No tiene permiso para gestionar activos fijos.'
        )


class CanDepreciarActivo(BaseEmpresaPermission):
    """
    Permiso para registrar depreciaciones de activos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.depreciar_activofijo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='activos.depreciar_activofijo',
            message='No tiene permiso para registrar depreciaciones de activos.'
        )


class CanCambiarEstadoActivo(BaseEmpresaPermission):
    """
    Permiso para cambiar el estado de activos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.cambiar_estado_activofijo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='activos.cambiar_estado_activofijo',
            message='No tiene permiso para cambiar el estado de activos.'
        )


class CanVerProyeccion(BaseEmpresaPermission):
    """
    Permiso para ver proyecciones de depreciación.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'activos.ver_proyeccion_activofijo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='activos.ver_proyeccion_activofijo',
            message='No tiene permiso para ver proyecciones de depreciación.'
        )


class IsActivoResponsable(ResponsableValidationMixin, AdminStaffMixin, permissions.BasePermission):
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
        if self._is_admin_or_staff(request.user):
            return True

        # Verificar si el usuario es el responsable
        return self._is_responsable(obj, request.user)

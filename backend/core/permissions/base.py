"""
Clases base genéricas para permisos - Infraestructura Global

Este módulo proporciona clases base reutilizables para permisos
que pueden ser extendidas por cualquier módulo del sistema.

Uso:
    from core.permissions.base import BaseEmpresaPermission

    class CanActionModel(BaseEmpresaPermission):
        def __init__(self):
            super().__init__(
                permission_codename='app.action_model',
                message='No tiene permiso para realizar esta acción.'
            )
"""
import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class BaseEmpresaPermission(permissions.BasePermission):
    """
    Clase base genérica para permisos con validación de empresa.

    Proporciona la lógica común para:
    - Verificación de autenticación
    - Verificación de superusuario/staff (bypass automático)
    - Verificación de permiso específico de Django
    - Validación de empresa a nivel de objeto

    Parámetros:
        permission_codename (str): Código del permiso Django requerido
            (ej: 'activos.depreciar_activofijo')
        message (str): Mensaje de error personalizado

    Ejemplo de uso:
        class CanDepreciarActivo(BaseEmpresaPermission):
            def __init__(self):
                super().__init__(
                    permission_codename='activos.depreciar_activofijo',
                    message='No tiene permiso para registrar depreciaciones.'
                )
    """

    def __init__(self, permission_codename=None, message=None):
        """
        Inicializa el permiso con configuración específica.

        Args:
            permission_codename: Código del permiso Django (ej: 'app.action_model')
            message: Mensaje de error personalizado
        """
        self.permission_codename = permission_codename
        self.message = message or 'No tiene permiso para realizar esta operación.'

    def _is_admin_or_staff(self, user):
        """
        Verifica si el usuario es superusuario o staff.

        Args:
            user: Instancia del usuario

        Returns:
            bool: True si es superusuario o staff
        """
        return user.is_superuser or user.is_staff

    def _has_permission_codename(self, user):
        """
        Verifica si el usuario tiene el permiso específico.

        Args:
            user: Instancia del usuario

        Returns:
            bool: True si tiene el permiso
        """
        if not self.permission_codename:
            return False
        return user.has_perm(self.permission_codename)

    def _belongs_to_same_empresa(self, obj, user):
        """
        Valida que el objeto pertenezca a la misma empresa del usuario.

        Funciona con cualquier modelo que tenga un campo 'empresa'.

        Args:
            obj: Instancia del objeto (modelo)
            user: Instancia del usuario

        Returns:
            bool: True si pertenecen a la misma empresa
        """
        if not (hasattr(obj, 'empresa') and hasattr(user, 'empresa')):
            return False
        return obj.empresa == user.empresa

    def has_permission(self, request, view):
        """
        Verifica permiso a nivel de vista.

        Orden de verificación:
        1. Usuario autenticado
        2. Superusuario/staff (bypass)
        3. Permiso específico

        Args:
            request: Request HTTP
            view: Vista DRF

        Returns:
            bool: True si tiene permiso
        """
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if self._is_admin_or_staff(request.user):
            return True

        # Verificar permiso específico
        return self._has_permission_codename(request.user)

    def has_object_permission(self, request, view, obj):
        """
        Verifica permiso a nivel de objeto.

        Incluye validación de empresa para evitar acceso cruzado.

        Orden de verificación:
        1. Usuario autenticado
        2. Superusuario/staff (bypass)
        3. Permiso específico
        4. Misma empresa

        Args:
            request: Request HTTP
            view: Vista DRF
            obj: Instancia del objeto

        Returns:
            bool: True si tiene permiso sobre el objeto
        """
        if not request.user.is_authenticated:
            return False

        # Superusuarios y staff siempre tienen acceso
        if self._is_admin_or_staff(request.user):
            return True

        # Verificar permiso específico
        if not self._has_permission_codename(request.user):
            return False

        # Verificar que pertenezca a la misma empresa
        return self._belongs_to_same_empresa(obj, request.user)


class BaseModelPermission(BaseEmpresaPermission):
    """
    Clase base para permisos de modelos específicos.

    Extiende BaseEmpresaPermission con soporte para generar
    automáticamente el código de permiso basado en app y modelo.

    Ejemplo de uso:
        class CanEditActivo(BaseModelPermission):
            def __init__(self):
                super().__init__(
                    app_label='activos',
                    model_name='activofijo',
                    action='change'
                )
    """

    def __init__(self, app_label=None, model_name=None, action='view', message=None):
        """
        Inicializa el permiso basado en modelo.

        Args:
            app_label: Nombre de la app Django (ej: 'activos')
            model_name: Nombre del modelo en minúsculas (ej: 'activofijo')
            action: Acción del permiso ('view', 'add', 'change', 'delete')
            message: Mensaje de error personalizado
        """
        permission_codename = None
        if app_label and model_name:
            permission_codename = f'{app_label}.{action}_{model_name}'

        super().__init__(
            permission_codename=permission_codename,
            message=message or f'No tiene permiso para {action} {model_name}.'
        )


class BaseActionPermission(BaseEmpresaPermission):
    """
    Clase base para permisos de acciones personalizadas.

    Diseñada para acciones custom en ViewSets (@action decorator).

    Ejemplo de uso:
        class CanDepreciar(BaseActionPermission):
            def __init__(self):
                super().__init__(
                    app_label='activos',
                    action_name='depreciar_activofijo'
                )
    """

    def __init__(self, app_label=None, action_name=None, message=None):
        """
        Inicializa el permiso de acción.

        Args:
            app_label: Nombre de la app Django
            action_name: Nombre de la acción/permiso
            message: Mensaje de error personalizado
        """
        permission_codename = None
        if app_label and action_name:
            permission_codename = f'{app_label}.{action_name}'

        super().__init__(
            permission_codename=permission_codename,
            message=message
        )


class BaseReadOnlyPermission(permissions.BasePermission):
    """
    Clase base para permisos de solo lectura.

    Permite acceso de lectura a usuarios autenticados,
    pero requiere permisos específicos para escritura.

    Ejemplo de uso:
        class ReadOnlyOrAdmin(BaseReadOnlyPermission):
            def __init__(self):
                super().__init__(
                    write_permission='activos.change_activofijo'
                )
    """

    def __init__(self, write_permission=None, message=None):
        """
        Inicializa el permiso de solo lectura.

        Args:
            write_permission: Permiso requerido para operaciones de escritura
            message: Mensaje de error personalizado
        """
        self.write_permission = write_permission
        self.message = message or 'Solo tiene permiso de lectura.'

    def has_permission(self, request, view):
        """
        Permite lectura a todos los autenticados,
        escritura solo con permiso específico.
        """
        if not request.user.is_authenticated:
            return False

        # Lectura siempre permitida para autenticados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escritura requiere admin/staff o permiso específico
        if request.user.is_superuser or request.user.is_staff:
            return True

        if self.write_permission:
            return request.user.has_perm(self.write_permission)

        return False

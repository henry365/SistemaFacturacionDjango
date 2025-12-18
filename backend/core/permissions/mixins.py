"""
Mixins genéricos reutilizables para permisos

Este módulo proporciona mixins que pueden ser combinados
con clases de permisos para agregar funcionalidades específicas.

Uso:
    from core.permissions.mixins import EmpresaValidationMixin, AdminStaffMixin

    class CustomPermission(EmpresaValidationMixin, AdminStaffMixin, BasePermission):
        pass
"""
import logging

logger = logging.getLogger(__name__)


class EmpresaValidationMixin:
    """
    Mixin para validación de empresa.

    Proporciona métodos para verificar que un objeto
    pertenezca a la misma empresa que el usuario.

    Métodos:
        _belongs_to_same_empresa(obj, user) -> bool
        _validate_empresa(obj, user) -> tuple[bool, str]
    """

    def _belongs_to_same_empresa(self, obj, user):
        """
        Verifica si el objeto pertenece a la misma empresa del usuario.

        Args:
            obj: Instancia del modelo con campo 'empresa'
            user: Instancia del usuario con campo 'empresa'

        Returns:
            bool: True si pertenecen a la misma empresa
        """
        if not hasattr(obj, 'empresa'):
            logger.warning(
                f"Objeto {type(obj).__name__} no tiene campo 'empresa'"
            )
            return False

        if not hasattr(user, 'empresa'):
            logger.warning(
                f"Usuario {user} no tiene campo 'empresa'"
            )
            return False

        return obj.empresa == user.empresa

    def _validate_empresa(self, obj, user):
        """
        Valida empresa con mensaje de error detallado.

        Args:
            obj: Instancia del modelo
            user: Instancia del usuario

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not hasattr(obj, 'empresa'):
            return False, f"Objeto {type(obj).__name__} no tiene campo 'empresa'"

        if not hasattr(user, 'empresa'):
            return False, "Usuario no tiene empresa asignada"

        if obj.empresa != user.empresa:
            return False, "El objeto no pertenece a su empresa"

        return True, None


class AdminStaffMixin:
    """
    Mixin para verificación de admin/staff.

    Proporciona métodos para verificar si un usuario
    es superusuario o miembro del staff.

    Métodos:
        _is_admin_or_staff(user) -> bool
        _check_admin_staff(user, log=False) -> bool
    """

    def _is_admin_or_staff(self, user):
        """
        Verifica si el usuario es superusuario o staff.

        Args:
            user: Instancia del usuario

        Returns:
            bool: True si es superusuario o staff
        """
        return user.is_superuser or user.is_staff

    def _check_admin_staff(self, user, log=False):
        """
        Verifica admin/staff con logging opcional.

        Args:
            user: Instancia del usuario
            log: Si True, registra el resultado en logs

        Returns:
            bool: True si es superusuario o staff
        """
        is_admin_staff = self._is_admin_or_staff(user)

        if log:
            if is_admin_staff:
                logger.debug(f"Usuario {user} es admin/staff - acceso permitido")
            else:
                logger.debug(f"Usuario {user} no es admin/staff")

        return is_admin_staff


class PermissionCheckMixin:
    """
    Mixin para verificación de permisos específicos.

    Proporciona métodos para verificar permisos de Django.

    Métodos:
        _has_perm(user, permission) -> bool
        _has_any_perm(user, permissions) -> bool
        _has_all_perms(user, permissions) -> bool
    """

    def _has_perm(self, user, permission):
        """
        Verifica si el usuario tiene un permiso específico.

        Args:
            user: Instancia del usuario
            permission: Código del permiso (ej: 'app.action_model')

        Returns:
            bool: True si tiene el permiso
        """
        return user.has_perm(permission)

    def _has_any_perm(self, user, permissions):
        """
        Verifica si el usuario tiene alguno de los permisos.

        Args:
            user: Instancia del usuario
            permissions: Lista de códigos de permisos

        Returns:
            bool: True si tiene al menos uno de los permisos
        """
        return any(user.has_perm(perm) for perm in permissions)

    def _has_all_perms(self, user, permissions):
        """
        Verifica si el usuario tiene todos los permisos.

        Args:
            user: Instancia del usuario
            permissions: Lista de códigos de permisos

        Returns:
            bool: True si tiene todos los permisos
        """
        return user.has_perms(permissions)


class OwnerValidationMixin:
    """
    Mixin para validación de propiedad.

    Verifica si el usuario es el propietario/creador de un objeto.

    Métodos:
        _is_owner(obj, user) -> bool
        _get_owner_field(obj) -> User or None
    """

    # Campos comunes que indican propiedad
    OWNER_FIELDS = ['usuario', 'user', 'usuario_creacion', 'owner', 'created_by']

    def _get_owner_field(self, obj):
        """
        Obtiene el usuario propietario del objeto.

        Busca en campos comunes de propiedad.

        Args:
            obj: Instancia del modelo

        Returns:
            Usuario propietario o None
        """
        for field_name in self.OWNER_FIELDS:
            owner = getattr(obj, field_name, None)
            if owner is not None:
                return owner
        return None

    def _is_owner(self, obj, user):
        """
        Verifica si el usuario es el propietario del objeto.

        Args:
            obj: Instancia del modelo
            user: Instancia del usuario

        Returns:
            bool: True si el usuario es el propietario
        """
        owner = self._get_owner_field(obj)
        if owner is None:
            return False
        return owner == user


class ResponsableValidationMixin:
    """
    Mixin para validación de responsable.

    Verifica si el usuario es el responsable asignado a un objeto.
    Útil para activos fijos y otros recursos con responsable asignado.

    Métodos:
        _is_responsable(obj, user) -> bool
    """

    def _is_responsable(self, obj, user):
        """
        Verifica si el usuario es el responsable del objeto.

        Args:
            obj: Instancia del modelo con campo 'responsable'
            user: Instancia del usuario

        Returns:
            bool: True si el usuario es el responsable
        """
        if not hasattr(obj, 'responsable'):
            return False

        responsable = getattr(obj, 'responsable', None)
        if responsable is None:
            return False

        return responsable == user

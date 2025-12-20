"""
Servicios de negocio para el módulo de Usuarios

Este módulo contiene la lógica de negocio separada de las vistas,
facilitando la testabilidad y mantenibilidad.
"""
import logging
from typing import Optional, Tuple, List
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

logger = logging.getLogger(__name__)

User = get_user_model()


class UserService:
    """
    Servicio para gestionar usuarios.
    """

    @staticmethod
    def activar_usuario(
        usuario,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Activa un usuario.

        Args:
            usuario: Usuario a activar
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if usuario.is_active:
            return False, 'El usuario ya está activo'

        usuario.is_active = True
        usuario.save(update_fields=['is_active'])

        logger.info(
            f"Usuario {usuario.username} activado por {ejecutado_por.username}"
        )

        return True, None

    @staticmethod
    def desactivar_usuario(
        usuario,
        ejecutado_por
    ) -> Tuple[bool, Optional[str]]:
        """
        Desactiva un usuario.

        Args:
            usuario: Usuario a desactivar
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if not usuario.is_active:
            return False, 'El usuario ya está inactivo'

        # No permitir desactivar superusuarios
        if usuario.is_superuser:
            return False, 'No se puede desactivar un superusuario'

        # No permitir auto-desactivación
        if usuario.id == ejecutado_por.id:
            return False, 'No puede desactivarse a sí mismo'

        usuario.is_active = False
        usuario.save(update_fields=['is_active'])

        logger.warning(
            f"Usuario {usuario.username} desactivado por {ejecutado_por.username}"
        )

        return True, None

    @staticmethod
    def asignar_permisos(
        usuario,
        permisos_ids: List[int],
        ejecutado_por
    ) -> Tuple[int, Optional[str]]:
        """
        Asigna permisos a un usuario.

        IDEMPOTENTE: Verifica si los permisos ya están asignados antes de operar.
        Solo asigna los permisos que el usuario no tiene.

        Args:
            usuario: Usuario al que asignar permisos
            permisos_ids: Lista de IDs de permisos
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (cantidad_asignados, mensaje_error)
        """
        if not permisos_ids:
            return 0, 'No se proporcionaron permisos'

        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            if not permisos.exists():
                return 0, 'No se encontraron permisos válidos'

            # IDEMPOTENCIA: Filtrar solo los permisos que no tiene
            permisos_actuales = set(usuario.user_permissions.values_list('id', flat=True))
            permisos_nuevos = permisos.exclude(id__in=permisos_actuales)

            if not permisos_nuevos.exists():
                # Ya tiene todos los permisos solicitados (idempotente)
                logger.info(
                    f"Usuario {usuario.username} ya tiene todos los permisos solicitados"
                )
                return 0, None

            with transaction.atomic():
                usuario.user_permissions.add(*permisos_nuevos)

            codenames = list(permisos_nuevos.values_list('codename', flat=True))
            logger.info(
                f"Permisos asignados a {usuario.username} por {ejecutado_por.username}: "
                f"{codenames}"
            )

            return permisos_nuevos.count(), None

        except Exception as e:
            logger.error(f"Error asignando permisos a {usuario.username}: {e}")
            return 0, str(e)

    @staticmethod
    def quitar_permisos(
        usuario,
        permisos_ids: List[int],
        ejecutado_por
    ) -> Tuple[int, Optional[str]]:
        """
        Quita permisos de un usuario.

        IDEMPOTENTE: Verifica si los permisos están asignados antes de quitar.
        Solo quita los permisos que el usuario tiene.

        Args:
            usuario: Usuario al que quitar permisos
            permisos_ids: Lista de IDs de permisos
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (cantidad_quitados, mensaje_error)
        """
        if not permisos_ids:
            return 0, 'No se proporcionaron permisos'

        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            if not permisos.exists():
                return 0, 'No se encontraron permisos válidos'

            # IDEMPOTENCIA: Filtrar solo los permisos que tiene
            permisos_actuales = set(usuario.user_permissions.values_list('id', flat=True))
            permisos_a_quitar = permisos.filter(id__in=permisos_actuales)

            if not permisos_a_quitar.exists():
                # No tiene ninguno de los permisos solicitados (idempotente)
                logger.info(
                    f"Usuario {usuario.username} no tiene los permisos solicitados"
                )
                return 0, None

            with transaction.atomic():
                usuario.user_permissions.remove(*permisos_a_quitar)

            codenames = list(permisos_a_quitar.values_list('codename', flat=True))
            logger.info(
                f"Permisos quitados de {usuario.username} por {ejecutado_por.username}: "
                f"{codenames}"
            )

            return permisos_a_quitar.count(), None

        except Exception as e:
            logger.error(f"Error quitando permisos de {usuario.username}: {e}")
            return 0, str(e)

    @staticmethod
    def asignar_grupo(
        usuario,
        grupo_id: Optional[int] = None,
        grupo_nombre: Optional[str] = None,
        ejecutado_por=None
    ) -> Tuple[bool, Optional[str]]:
        """
        Asigna un grupo a un usuario.

        IDEMPOTENTE: Verifica si el usuario ya pertenece al grupo antes de asignar.

        Args:
            usuario: Usuario al que asignar grupo
            grupo_id: ID del grupo (opcional)
            grupo_nombre: Nombre del grupo (opcional)
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if not grupo_id and not grupo_nombre:
            return False, 'Se requiere grupo_id o grupo_nombre'

        try:
            if grupo_id:
                grupo = Group.objects.get(id=grupo_id)
            else:
                grupo = Group.objects.get(name=grupo_nombre)

            # IDEMPOTENCIA: Verificar si ya pertenece al grupo
            if usuario.groups.filter(id=grupo.id).exists():
                logger.info(
                    f"Usuario {usuario.username} ya pertenece al grupo '{grupo.name}'"
                )
                return True, None  # Éxito, ya está asignado

            usuario.groups.add(grupo)

            if ejecutado_por:
                logger.info(
                    f"Grupo '{grupo.name}' asignado a {usuario.username} "
                    f"por {ejecutado_por.username}"
                )

            return True, None

        except Group.DoesNotExist:
            return False, 'Grupo no encontrado'
        except Exception as e:
            logger.error(f"Error asignando grupo a {usuario.username}: {e}")
            return False, str(e)

    @staticmethod
    def quitar_grupo(
        usuario,
        grupo_id: Optional[int] = None,
        grupo_nombre: Optional[str] = None,
        ejecutado_por=None
    ) -> Tuple[bool, Optional[str]]:
        """
        Quita un grupo de un usuario.

        IDEMPOTENTE: Verifica si el usuario pertenece al grupo antes de quitar.

        Args:
            usuario: Usuario al que quitar grupo
            grupo_id: ID del grupo (opcional)
            grupo_nombre: Nombre del grupo (opcional)
            ejecutado_por: Usuario que ejecuta la acción

        Returns:
            Tuple (exito, mensaje_error)
        """
        if not grupo_id and not grupo_nombre:
            return False, 'Se requiere grupo_id o grupo_nombre'

        try:
            if grupo_id:
                grupo = Group.objects.get(id=grupo_id)
            else:
                grupo = Group.objects.get(name=grupo_nombre)

            # IDEMPOTENCIA: Verificar si pertenece al grupo
            if not usuario.groups.filter(id=grupo.id).exists():
                logger.info(
                    f"Usuario {usuario.username} no pertenece al grupo '{grupo.name}'"
                )
                return True, None  # Éxito, ya no pertenece

            usuario.groups.remove(grupo)

            if ejecutado_por:
                logger.info(
                    f"Grupo '{grupo.name}' quitado de {usuario.username} "
                    f"por {ejecutado_por.username}"
                )

            return True, None

        except Group.DoesNotExist:
            return False, 'Grupo no encontrado'
        except Exception as e:
            logger.error(f"Error quitando grupo de {usuario.username}: {e}")
            return False, str(e)

    @staticmethod
    def cambiar_password(
        usuario,
        password_actual: str,
        password_nuevo: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Cambia la contraseña de un usuario.

        Args:
            usuario: Usuario al que cambiar contraseña
            password_actual: Contraseña actual
            password_nuevo: Nueva contraseña

        Returns:
            Tuple (exito, mensaje_error)
        """
        if not usuario.check_password(password_actual):
            return False, 'La contraseña actual es incorrecta'

        usuario.set_password(password_nuevo)
        usuario.save(update_fields=['password'])

        logger.info(f"Contraseña cambiada para usuario {usuario.username}")

        return True, None

    @staticmethod
    def obtener_resumen_por_empresa(empresa) -> dict:
        """
        Obtiene un resumen de usuarios por empresa.

        Args:
            empresa: Instancia de Empresa

        Returns:
            Diccionario con totales y estadísticas
        """
        from django.db.models import Count

        usuarios = User.objects.filter(empresa=empresa)

        resumen = {
            'total_usuarios': usuarios.count(),
            'usuarios_activos': usuarios.filter(is_active=True).count(),
            'usuarios_inactivos': usuarios.filter(is_active=False).count(),
            'por_rol': list(
                usuarios.values('rol').annotate(cantidad=Count('id')).order_by('rol')
            ),
        }

        return resumen

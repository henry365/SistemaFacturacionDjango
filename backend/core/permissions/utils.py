"""
Utilidades genéricas para permisos - Infraestructura Global

Este módulo proporciona funciones auxiliares, decoradores y helpers
para facilitar el trabajo con permisos en todo el sistema.

Compatibilidad: Django 6.0 - Usa el sistema de permisos nativo de Django

Contenido:
- Helpers para verificación de permisos
- Decoradores reutilizables
- Funciones de utilidad para testing
- Utilidades avanzadas (caché, logging)
"""
import logging
from functools import wraps
from typing import List, Optional, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import RequestFactory
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

logger = logging.getLogger(__name__)

User = get_user_model()


# =============================================================================
# Helpers para Verificación de Permisos
# =============================================================================

def check_permission(user, permission_codename: str) -> bool:
    """
    Verifica si un usuario tiene un permiso específico.

    Considera superusuarios y staff como usuarios con acceso completo.

    Args:
        user: Instancia del usuario de Django
        permission_codename: Código del permiso Django (ej: 'activos.depreciar_activofijo')

    Returns:
        bool: True si el usuario tiene el permiso, es superusuario o staff

    Example:
        >>> if check_permission(request.user, 'activos.depreciar_activofijo'):
        ...     # Usuario puede depreciar activos
        ...     pass
    """
    if not user or not user.is_authenticated:
        return False

    # Superusuarios y staff siempre tienen acceso
    if user.is_superuser or user.is_staff:
        return True

    return user.has_perm(permission_codename)


def check_empresa_permission(user, obj, permission_codename: str) -> bool:
    """
    Verifica permiso específico y que el objeto pertenezca a la misma empresa del usuario.

    Args:
        user: Instancia del usuario de Django
        obj: Instancia del modelo con campo 'empresa'
        permission_codename: Código del permiso Django

    Returns:
        bool: True si tiene permiso Y pertenece a la misma empresa

    Example:
        >>> activo = ActivoFijo.objects.get(pk=1)
        >>> if check_empresa_permission(request.user, activo, 'activos.change_activofijo'):
        ...     # Usuario puede editar este activo de su empresa
        ...     pass
    """
    if not check_permission(user, permission_codename):
        return False

    # Superusuarios y staff tienen acceso a todas las empresas
    if user.is_superuser or user.is_staff:
        return True

    return belongs_to_same_empresa(obj, user)


def user_has_any_permission(user, permissions: List[str]) -> bool:
    """
    Verifica si el usuario tiene al menos uno de los permisos especificados.

    Args:
        user: Instancia del usuario de Django
        permissions: Lista de códigos de permisos

    Returns:
        bool: True si tiene al menos uno de los permisos

    Example:
        >>> perms = ['activos.depreciar_activofijo', 'activos.cambiar_estado_activofijo']
        >>> if user_has_any_permission(request.user, perms):
        ...     # Usuario tiene al menos uno de los permisos
        ...     pass
    """
    if not user or not user.is_authenticated:
        return False

    # Superusuarios y staff siempre tienen acceso
    if user.is_superuser or user.is_staff:
        return True

    return any(user.has_perm(perm) for perm in permissions)


def user_has_all_permissions(user, permissions: List[str]) -> bool:
    """
    Verifica si el usuario tiene todos los permisos especificados.

    Args:
        user: Instancia del usuario de Django
        permissions: Lista de códigos de permisos

    Returns:
        bool: True si tiene todos los permisos

    Example:
        >>> perms = ['activos.depreciar_activofijo', 'activos.cambiar_estado_activofijo']
        >>> if user_has_all_permissions(request.user, perms):
        ...     # Usuario tiene todos los permisos requeridos
        ...     pass
    """
    if not user or not user.is_authenticated:
        return False

    # Superusuarios y staff siempre tienen acceso
    if user.is_superuser or user.is_staff:
        return True

    return user.has_perms(permissions)


def belongs_to_same_empresa(obj, user) -> bool:
    """
    Verifica si un objeto pertenece a la misma empresa que el usuario.

    Args:
        obj: Instancia del modelo con campo 'empresa'
        user: Instancia del usuario con campo 'empresa'

    Returns:
        bool: True si pertenecen a la misma empresa

    Example:
        >>> if belongs_to_same_empresa(activo, request.user):
        ...     # El activo pertenece a la empresa del usuario
        ...     pass
    """
    if not hasattr(obj, 'empresa'):
        logger.debug(f"Objeto {type(obj).__name__} no tiene campo 'empresa'")
        return False

    if not hasattr(user, 'empresa'):
        logger.debug(f"Usuario {user} no tiene campo 'empresa'")
        return False

    if obj.empresa is None or user.empresa is None:
        return False

    return obj.empresa == user.empresa


# =============================================================================
# Decoradores Reutilizables
# =============================================================================

def require_permission(permission_codename: str):
    """
    Decorador para asignar un permiso específico a una acción personalizada de ViewSet.

    Asigna el atributo `permission_required` a la función, que es utilizado
    por `ActionBasedPermission` y otras clases de permisos.

    Args:
        permission_codename: Código del permiso Django requerido

    Example:
        >>> from rest_framework.decorators import action
        >>> from core.permissions.utils import require_permission
        >>>
        >>> class ActivoFijoViewSet(viewsets.ModelViewSet):
        ...     @action(detail=True, methods=['post'])
        ...     @require_permission('activos.depreciar_activofijo')
        ...     def depreciar(self, request, pk=None):
        ...         # Esta acción requiere el permiso 'activos.depreciar_activofijo'
        ...         pass
    """
    def decorator(func):
        func.permission_required = permission_codename
        return func
    return decorator


def require_same_empresa(func):
    """
    Decorador que verifica que el objeto pertenezca a la empresa del usuario.

    Debe usarse en métodos de ViewSet que reciben `self` y `request`.
    Retorna 403 PermissionDenied si el objeto no pertenece a la misma empresa.

    Example:
        >>> from rest_framework.decorators import action
        >>> from core.permissions.utils import require_same_empresa
        >>>
        >>> class ActivoFijoViewSet(viewsets.ModelViewSet):
        ...     @action(detail=True, methods=['post'])
        ...     @require_same_empresa
        ...     def operacion_especial(self, request, pk=None):
        ...         # Verifica automáticamente que el activo pertenezca a la empresa
        ...         activo = self.get_object()
        ...         # ... lógica de la acción
        ...         pass
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        # Obtener el objeto usando get_object() del ViewSet
        obj = self.get_object()
        user = request.user

        # Superusuarios y staff tienen acceso a todo
        if user.is_superuser or user.is_staff:
            return func(self, request, *args, **kwargs)

        # Verificar que pertenezca a la misma empresa
        if not belongs_to_same_empresa(obj, user):
            logger.warning(
                f"Usuario {user} intentó acceder a objeto {obj} de otra empresa"
            )
            raise PermissionDenied(
                "No tiene permiso para acceder a recursos de otra empresa."
            )

        return func(self, request, *args, **kwargs)

    return wrapper


# =============================================================================
# Funciones de Utilidad para Testing
# =============================================================================

def create_user_with_permission(
    permission_codename: str,
    empresa=None,
    **kwargs
):
    """
    Crea un usuario de prueba con un permiso específico asignado.

    Args:
        permission_codename: Código del permiso a asignar (ej: 'activos.depreciar_activofijo')
        empresa: Empresa a asignar al usuario (opcional)
        **kwargs: Argumentos adicionales para User.objects.create_user()

    Returns:
        User: Usuario creado con el permiso asignado

    Example:
        >>> user = create_user_with_permission(
        ...     'activos.depreciar_activofijo',
        ...     empresa=self.empresa,
        ...     username='testuser'
        ... )
        >>> self.assertTrue(user.has_perm('activos.depreciar_activofijo'))
    """
    # Valores por defecto para el usuario
    defaults = {
        'username': f'testuser_{permission_codename.replace(".", "_")}',
        'email': 'test@example.com',
        'password': 'testpassword123',
    }
    defaults.update(kwargs)

    # Crear usuario
    user = User.objects.create_user(**defaults)

    # Asignar empresa si se proporciona
    if empresa is not None and hasattr(user, 'empresa'):
        user.empresa = empresa
        user.save(update_fields=['empresa'])

    # Asignar permiso
    try:
        # El formato es 'app_label.codename'
        app_label, codename = permission_codename.split('.')
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename
        )
        user.user_permissions.add(permission)
    except (ValueError, Permission.DoesNotExist) as e:
        logger.warning(f"No se pudo asignar permiso '{permission_codename}': {e}")

    return user


def create_mock_request(user, method: str = 'GET', data: dict = None) -> Request:
    """
    Crea un objeto request mock para tests de permisos.

    Args:
        user: Usuario a asignar al request
        method: Método HTTP ('GET', 'POST', 'PUT', 'DELETE')
        data: Datos del request body (opcional)

    Returns:
        Request: Objeto request de DRF con el usuario asignado

    Example:
        >>> request = create_mock_request(user, method='POST', data={'estado': 'ACTIVO'})
        >>> permission = CanDepreciarActivo()
        >>> self.assertTrue(permission.has_permission(request, None))
    """
    factory = RequestFactory()

    method_lower = method.lower()
    method_func = getattr(factory, method_lower, factory.get)

    if data:
        django_request = method_func('/', data=data, content_type='application/json')
    else:
        django_request = method_func('/')

    django_request.user = user

    # Convertir a Request de DRF
    drf_request = Request(django_request)

    # Asignar usuario explícitamente al request de DRF
    # (necesario porque DRF Request tiene su propia lógica de autenticación)
    drf_request._user = user
    drf_request._request.user = user

    return drf_request


def assert_has_permission(
    permission_instance,
    user,
    obj=None,
    should_have: bool = True,
    msg: str = None
):
    """
    Helper de assert para verificar permisos en tests.

    Args:
        permission_instance: Instancia de clase de permiso a probar
        user: Usuario a verificar
        obj: Objeto para has_object_permission (opcional)
        should_have: Si se espera que tenga permiso (True) o no (False)
        msg: Mensaje personalizado para el assert

    Raises:
        AssertionError: Si el resultado no coincide con should_have

    Example:
        >>> assert_has_permission(
        ...     CanDepreciarActivo(),
        ...     user,
        ...     obj=activo,
        ...     should_have=True
        ... )
    """
    request = create_mock_request(user)
    view = None  # La mayoría de permisos no requieren view

    # Verificar has_permission
    has_perm = permission_instance.has_permission(request, view)

    # Si hay objeto, también verificar has_object_permission
    if obj is not None and has_perm:
        has_perm = permission_instance.has_object_permission(request, view, obj)

    # Construir mensaje de error
    if msg is None:
        if should_have:
            msg = f"Usuario {user} debería tener permiso pero no lo tiene"
        else:
            msg = f"Usuario {user} no debería tener permiso pero lo tiene"

    # Assert
    if should_have:
        assert has_perm, msg
    else:
        assert not has_perm, msg


def create_test_empresa(name: str = 'Test Empresa'):
    """
    Crea una empresa de prueba para tests.

    Args:
        name: Nombre de la empresa

    Returns:
        Empresa: Empresa creada

    Example:
        >>> empresa = create_test_empresa('Mi Empresa Test')
        >>> user.empresa = empresa
        >>> user.save()
    """
    # Importar aquí para evitar imports circulares
    from empresas.models import Empresa

    empresa = Empresa.objects.create(
        nombre=name,
        rnc=f'RNC-{name[:10].replace(" ", "")}',
        activo=True
    )

    return empresa


# =============================================================================
# Utilidades Avanzadas
# =============================================================================

def get_cached_permission(
    user,
    permission_codename: str,
    cache_timeout: int = 300
) -> bool:
    """
    Obtiene resultado de verificación de permiso desde caché si está disponible.

    Útil para reducir consultas a la base de datos en verificaciones frecuentes.

    Args:
        user: Instancia del usuario
        permission_codename: Código del permiso
        cache_timeout: Tiempo de expiración del caché en segundos (default: 300)

    Returns:
        bool: Resultado de la verificación de permiso

    Note:
        Requiere configuración de caché en Django settings.

    Example:
        >>> if get_cached_permission(request.user, 'activos.depreciar_activofijo'):
        ...     # Permiso verificado (posiblemente desde caché)
        ...     pass
    """
    if not user or not user.is_authenticated:
        return False

    # Superusuarios y staff no necesitan caché
    if user.is_superuser or user.is_staff:
        return True

    # Generar clave de caché
    cache_key = f"perm:{user.pk}:{permission_codename}"

    # Intentar obtener del caché
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit para permiso {permission_codename} de usuario {user.pk}")
        return cached_result

    # Verificar permiso y guardar en caché
    has_perm = user.has_perm(permission_codename)
    cache.set(cache_key, has_perm, cache_timeout)
    logger.debug(f"Cache miss para permiso {permission_codename} de usuario {user.pk}")

    return has_perm


def invalidate_permission_cache(user, permission_codename: str = None):
    """
    Invalida el caché de permisos para un usuario.

    Args:
        user: Instancia del usuario
        permission_codename: Código del permiso específico a invalidar.
                            Si es None, invalida todos los permisos del usuario.

    Example:
        >>> # Invalidar un permiso específico
        >>> invalidate_permission_cache(user, 'activos.depreciar_activofijo')
        >>>
        >>> # Invalidar todos los permisos del usuario (después de cambiar permisos)
        >>> invalidate_permission_cache(user)
    """
    if permission_codename:
        cache_key = f"perm:{user.pk}:{permission_codename}"
        cache.delete(cache_key)
        logger.debug(f"Cache invalidado para permiso {permission_codename} de usuario {user.pk}")
    else:
        # Patrón para invalidar todos los permisos del usuario
        # Nota: esto requiere un backend de caché que soporte delete_pattern
        # Para backends simples, se debería mantener una lista de permisos cacheados
        cache_pattern = f"perm:{user.pk}:*"
        try:
            cache.delete_pattern(cache_pattern)
        except AttributeError:
            # El backend no soporta delete_pattern
            logger.warning(
                f"Cache backend no soporta delete_pattern. "
                f"No se puede invalidar todos los permisos para usuario {user.pk}"
            )


def log_permission_check(
    user,
    permission: str,
    granted: bool,
    obj=None,
    request=None
):
    """
    Registra verificaciones de permisos para auditoría.

    Args:
        user: Usuario que verificó el permiso
        permission: Código del permiso verificado
        granted: Si el permiso fue otorgado (True) o denegado (False)
        obj: Objeto relacionado (opcional)
        request: Request HTTP para obtener IP, etc. (opcional)

    Example:
        >>> def has_permission(self, request, view):
        ...     granted = check_permission(request.user, 'activos.depreciar_activofijo')
        ...     log_permission_check(
        ...         request.user,
        ...         'activos.depreciar_activofijo',
        ...         granted,
        ...         request=request
        ...     )
        ...     return granted
    """
    # Obtener información adicional del request
    ip_address = None
    user_agent = None
    if request:
        # Intentar obtener IP real (considerando proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]

    # Construir mensaje de log
    status = "GRANTED" if granted else "DENIED"
    obj_info = f" on {type(obj).__name__}({obj.pk})" if obj else ""

    log_message = (
        f"Permission {status}: user={user.pk} ({user.username}), "
        f"permission={permission}{obj_info}"
    )

    if ip_address:
        log_message += f", ip={ip_address}"

    # Registrar según el resultado
    if granted:
        logger.info(log_message)
    else:
        logger.warning(log_message)


def get_user_permissions_summary(user) -> dict:
    """
    Obtiene un resumen de los permisos de un usuario.

    Útil para debugging y auditoría.

    Args:
        user: Instancia del usuario

    Returns:
        dict: Resumen con permisos directos, de grupo y efectivos

    Example:
        >>> summary = get_user_permissions_summary(request.user)
        >>> print(summary['direct_permissions'])
    """
    if not user or not user.is_authenticated:
        return {
            'is_authenticated': False,
            'direct_permissions': [],
            'group_permissions': [],
            'all_permissions': [],
            'is_superuser': False,
            'is_staff': False,
        }

    # Permisos directos del usuario
    direct_perms = list(
        user.user_permissions.values_list('content_type__app_label', 'codename')
    )
    direct_permissions = [f"{app}.{code}" for app, code in direct_perms]

    # Permisos de grupos
    group_perms = list(
        Permission.objects.filter(group__user=user).values_list(
            'content_type__app_label', 'codename'
        )
    )
    group_permissions = [f"{app}.{code}" for app, code in group_perms]

    # Todos los permisos efectivos
    all_perms = list(user.get_all_permissions())

    return {
        'is_authenticated': True,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'direct_permissions': sorted(direct_permissions),
        'group_permissions': sorted(group_permissions),
        'all_permissions': sorted(all_perms),
        'groups': list(user.groups.values_list('name', flat=True)),
    }

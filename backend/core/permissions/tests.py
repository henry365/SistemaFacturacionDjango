"""
Tests para la infraestructura global de permisos

Verifica que las clases base y mixins funcionen correctamente.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, MagicMock

from .base import (
    BaseEmpresaPermission,
    BaseModelPermission,
    BaseActionPermission,
    BaseReadOnlyPermission,
)
from .mixins import (
    EmpresaValidationMixin,
    AdminStaffMixin,
    PermissionCheckMixin,
    OwnerValidationMixin,
    ResponsableValidationMixin,
)

User = get_user_model()


class BaseEmpresaPermissionTest(TestCase):
    """Tests para BaseEmpresaPermission"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = BaseEmpresaPermission(
            permission_codename='test.test_permission',
            message='Test message'
        )

    def test_unauthenticated_user_denied(self):
        """Test: Usuario no autenticado es denegado"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False)
        view = Mock()

        self.assertFalse(self.permission.has_permission(request, view))

    def test_superuser_allowed(self):
        """Test: Superusuario siempre permitido"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False
        )
        view = Mock()

        self.assertTrue(self.permission.has_permission(request, view))

    def test_staff_allowed(self):
        """Test: Staff siempre permitido"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=True
        )
        view = Mock()

        self.assertTrue(self.permission.has_permission(request, view))

    def test_user_with_permission_allowed(self):
        """Test: Usuario con permiso específico permitido"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        request.user.has_perm = Mock(return_value=True)
        view = Mock()

        self.assertTrue(self.permission.has_permission(request, view))
        request.user.has_perm.assert_called_with('test.test_permission')

    def test_user_without_permission_denied(self):
        """Test: Usuario sin permiso denegado"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        request.user.has_perm = Mock(return_value=False)
        view = Mock()

        self.assertFalse(self.permission.has_permission(request, view))

    def test_object_permission_same_empresa(self):
        """Test: Permiso de objeto con misma empresa"""
        request = self.factory.get('/')
        empresa = Mock()
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False,
            empresa=empresa
        )
        request.user.has_perm = Mock(return_value=True)
        view = Mock()
        obj = Mock(empresa=empresa)

        self.assertTrue(self.permission.has_object_permission(request, view, obj))

    def test_object_permission_different_empresa_denied(self):
        """Test: Permiso de objeto con diferente empresa denegado"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False,
            empresa=Mock()
        )
        request.user.has_perm = Mock(return_value=True)
        view = Mock()
        obj = Mock(empresa=Mock())  # Diferente empresa

        self.assertFalse(self.permission.has_object_permission(request, view, obj))


class BaseModelPermissionTest(TestCase):
    """Tests para BaseModelPermission"""

    def test_permission_codename_generated(self):
        """Test: Código de permiso generado correctamente"""
        permission = BaseModelPermission(
            app_label='activos',
            model_name='activofijo',
            action='change'
        )
        self.assertEqual(permission.permission_codename, 'activos.change_activofijo')

    def test_default_action_is_view(self):
        """Test: Acción por defecto es view"""
        permission = BaseModelPermission(
            app_label='activos',
            model_name='activofijo'
        )
        self.assertEqual(permission.permission_codename, 'activos.view_activofijo')


class BaseActionPermissionTest(TestCase):
    """Tests para BaseActionPermission"""

    def test_permission_codename_generated(self):
        """Test: Código de permiso generado correctamente"""
        permission = BaseActionPermission(
            app_label='activos',
            action_name='depreciar_activofijo'
        )
        self.assertEqual(permission.permission_codename, 'activos.depreciar_activofijo')


class BaseReadOnlyPermissionTest(TestCase):
    """Tests para BaseReadOnlyPermission"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = BaseReadOnlyPermission(
            write_permission='test.change_test'
        )

    def test_get_request_allowed(self):
        """Test: GET permitido para usuarios autenticados"""
        request = self.factory.get('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        view = Mock()

        self.assertTrue(self.permission.has_permission(request, view))

    def test_post_without_permission_denied(self):
        """Test: POST sin permiso denegado"""
        request = self.factory.post('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        request.user.has_perm = Mock(return_value=False)
        view = Mock()

        self.assertFalse(self.permission.has_permission(request, view))

    def test_post_with_permission_allowed(self):
        """Test: POST con permiso permitido"""
        request = self.factory.post('/')
        request.user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        request.user.has_perm = Mock(return_value=True)
        view = Mock()

        self.assertTrue(self.permission.has_permission(request, view))


class EmpresaValidationMixinTest(TestCase):
    """Tests para EmpresaValidationMixin"""

    def setUp(self):
        self.mixin = EmpresaValidationMixin()

    def test_same_empresa_returns_true(self):
        """Test: Misma empresa retorna True"""
        empresa = Mock()
        obj = Mock(empresa=empresa)
        user = Mock(empresa=empresa)

        self.assertTrue(self.mixin._belongs_to_same_empresa(obj, user))

    def test_different_empresa_returns_false(self):
        """Test: Diferente empresa retorna False"""
        obj = Mock(empresa=Mock())
        user = Mock(empresa=Mock())

        self.assertFalse(self.mixin._belongs_to_same_empresa(obj, user))

    def test_object_without_empresa_returns_false(self):
        """Test: Objeto sin empresa retorna False"""
        obj = Mock(spec=[])  # No tiene atributo empresa
        user = Mock(empresa=Mock())

        self.assertFalse(self.mixin._belongs_to_same_empresa(obj, user))


class AdminStaffMixinTest(TestCase):
    """Tests para AdminStaffMixin"""

    def setUp(self):
        self.mixin = AdminStaffMixin()

    def test_superuser_returns_true(self):
        """Test: Superusuario retorna True"""
        user = Mock(is_superuser=True, is_staff=False)
        self.assertTrue(self.mixin._is_admin_or_staff(user))

    def test_staff_returns_true(self):
        """Test: Staff retorna True"""
        user = Mock(is_superuser=False, is_staff=True)
        self.assertTrue(self.mixin._is_admin_or_staff(user))

    def test_regular_user_returns_false(self):
        """Test: Usuario regular retorna False"""
        user = Mock(is_superuser=False, is_staff=False)
        self.assertFalse(self.mixin._is_admin_or_staff(user))


class PermissionCheckMixinTest(TestCase):
    """Tests para PermissionCheckMixin"""

    def setUp(self):
        self.mixin = PermissionCheckMixin()

    def test_has_perm(self):
        """Test: _has_perm funciona correctamente"""
        user = Mock()
        user.has_perm = Mock(return_value=True)

        self.assertTrue(self.mixin._has_perm(user, 'test.permission'))
        user.has_perm.assert_called_with('test.permission')

    def test_has_any_perm_true(self):
        """Test: _has_any_perm retorna True si tiene algún permiso"""
        user = Mock()
        user.has_perm = Mock(side_effect=[False, True, False])

        perms = ['test.perm1', 'test.perm2', 'test.perm3']
        self.assertTrue(self.mixin._has_any_perm(user, perms))

    def test_has_any_perm_false(self):
        """Test: _has_any_perm retorna False si no tiene ningún permiso"""
        user = Mock()
        user.has_perm = Mock(return_value=False)

        perms = ['test.perm1', 'test.perm2']
        self.assertFalse(self.mixin._has_any_perm(user, perms))

    def test_has_all_perms(self):
        """Test: _has_all_perms funciona correctamente"""
        user = Mock()
        user.has_perms = Mock(return_value=True)

        perms = ['test.perm1', 'test.perm2']
        self.assertTrue(self.mixin._has_all_perms(user, perms))
        user.has_perms.assert_called_with(perms)


class OwnerValidationMixinTest(TestCase):
    """Tests para OwnerValidationMixin"""

    def setUp(self):
        self.mixin = OwnerValidationMixin()

    def test_is_owner_with_usuario_field(self):
        """Test: _is_owner con campo usuario"""
        user = Mock()
        obj = Mock(usuario=user)

        self.assertTrue(self.mixin._is_owner(obj, user))

    def test_is_owner_with_user_field(self):
        """Test: _is_owner con campo user"""
        user = Mock()
        obj = Mock(spec=['user'])
        obj.user = user

        self.assertTrue(self.mixin._is_owner(obj, user))

    def test_is_not_owner(self):
        """Test: _is_owner retorna False si no es propietario"""
        user = Mock()
        other_user = Mock()
        obj = Mock(usuario=other_user)

        self.assertFalse(self.mixin._is_owner(obj, user))


class ResponsableValidationMixinTest(TestCase):
    """Tests para ResponsableValidationMixin"""

    def setUp(self):
        self.mixin = ResponsableValidationMixin()

    def test_is_responsable_true(self):
        """Test: _is_responsable retorna True si es responsable"""
        user = Mock()
        obj = Mock(responsable=user)

        self.assertTrue(self.mixin._is_responsable(obj, user))

    def test_is_responsable_false(self):
        """Test: _is_responsable retorna False si no es responsable"""
        user = Mock()
        other_user = Mock()
        obj = Mock(responsable=other_user)

        self.assertFalse(self.mixin._is_responsable(obj, user))

    def test_is_responsable_no_field(self):
        """Test: _is_responsable retorna False si no hay campo responsable"""
        user = Mock()
        obj = Mock(spec=[])  # Sin campo responsable

        self.assertFalse(self.mixin._is_responsable(obj, user))


# =============================================================================
# Tests para Utilidades (utils.py)
# =============================================================================

from .utils import (
    check_permission,
    check_empresa_permission,
    user_has_any_permission,
    user_has_all_permissions,
    belongs_to_same_empresa,
    require_permission,
    require_same_empresa,
    create_mock_request,
    get_cached_permission,
    log_permission_check,
    get_user_permissions_summary,
)


class CheckPermissionTest(TestCase):
    """Tests para check_permission()"""

    def test_unauthenticated_user_returns_false(self):
        """Test: Usuario no autenticado retorna False"""
        user = Mock(is_authenticated=False)
        self.assertFalse(check_permission(user, 'test.perm'))

    def test_none_user_returns_false(self):
        """Test: Usuario None retorna False"""
        self.assertFalse(check_permission(None, 'test.perm'))

    def test_superuser_returns_true(self):
        """Test: Superusuario siempre retorna True"""
        user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False
        )
        self.assertTrue(check_permission(user, 'test.perm'))

    def test_staff_returns_true(self):
        """Test: Staff siempre retorna True"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=True
        )
        self.assertTrue(check_permission(user, 'test.perm'))

    def test_user_with_permission_returns_true(self):
        """Test: Usuario con permiso retorna True"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perm = Mock(return_value=True)

        self.assertTrue(check_permission(user, 'test.perm'))
        user.has_perm.assert_called_with('test.perm')

    def test_user_without_permission_returns_false(self):
        """Test: Usuario sin permiso retorna False"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perm = Mock(return_value=False)

        self.assertFalse(check_permission(user, 'test.perm'))


class CheckEmpresaPermissionTest(TestCase):
    """Tests para check_empresa_permission()"""

    def test_superuser_bypass_empresa_check(self):
        """Test: Superusuario bypasea verificación de empresa"""
        user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False,
            empresa=Mock()
        )
        obj = Mock(empresa=Mock())  # Diferente empresa

        self.assertTrue(check_empresa_permission(user, obj, 'test.perm'))

    def test_same_empresa_with_permission(self):
        """Test: Misma empresa con permiso retorna True"""
        empresa = Mock()
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False,
            empresa=empresa
        )
        user.has_perm = Mock(return_value=True)
        obj = Mock(empresa=empresa)

        self.assertTrue(check_empresa_permission(user, obj, 'test.perm'))

    def test_different_empresa_returns_false(self):
        """Test: Diferente empresa retorna False"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False,
            empresa=Mock()
        )
        user.has_perm = Mock(return_value=True)
        obj = Mock(empresa=Mock())

        self.assertFalse(check_empresa_permission(user, obj, 'test.perm'))


class UserHasAnyPermissionTest(TestCase):
    """Tests para user_has_any_permission()"""

    def test_superuser_returns_true(self):
        """Test: Superusuario siempre retorna True"""
        user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False
        )
        perms = ['test.perm1', 'test.perm2']

        self.assertTrue(user_has_any_permission(user, perms))

    def test_has_one_of_many(self):
        """Test: Tiene uno de varios permisos"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perm = Mock(side_effect=[False, True])

        perms = ['test.perm1', 'test.perm2']
        self.assertTrue(user_has_any_permission(user, perms))

    def test_has_none_of_many(self):
        """Test: No tiene ninguno de los permisos"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perm = Mock(return_value=False)

        perms = ['test.perm1', 'test.perm2']
        self.assertFalse(user_has_any_permission(user, perms))


class UserHasAllPermissionsTest(TestCase):
    """Tests para user_has_all_permissions()"""

    def test_superuser_returns_true(self):
        """Test: Superusuario siempre retorna True"""
        user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False
        )
        perms = ['test.perm1', 'test.perm2']

        self.assertTrue(user_has_all_permissions(user, perms))

    def test_has_all_permissions(self):
        """Test: Tiene todos los permisos"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perms = Mock(return_value=True)

        perms = ['test.perm1', 'test.perm2']
        self.assertTrue(user_has_all_permissions(user, perms))
        user.has_perms.assert_called_with(perms)

    def test_missing_some_permissions(self):
        """Test: Faltan algunos permisos"""
        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False
        )
        user.has_perms = Mock(return_value=False)

        perms = ['test.perm1', 'test.perm2']
        self.assertFalse(user_has_all_permissions(user, perms))


class BelongsToSameEmpresaTest(TestCase):
    """Tests para belongs_to_same_empresa()"""

    def test_same_empresa(self):
        """Test: Misma empresa retorna True"""
        empresa = Mock()
        obj = Mock(empresa=empresa)
        user = Mock(empresa=empresa)

        self.assertTrue(belongs_to_same_empresa(obj, user))

    def test_different_empresa(self):
        """Test: Diferente empresa retorna False"""
        obj = Mock(empresa=Mock())
        user = Mock(empresa=Mock())

        self.assertFalse(belongs_to_same_empresa(obj, user))

    def test_obj_without_empresa_field(self):
        """Test: Objeto sin campo empresa retorna False"""
        obj = Mock(spec=[])
        user = Mock(empresa=Mock())

        self.assertFalse(belongs_to_same_empresa(obj, user))

    def test_user_without_empresa_field(self):
        """Test: Usuario sin campo empresa retorna False"""
        obj = Mock(empresa=Mock())
        user = Mock(spec=['is_authenticated'])

        self.assertFalse(belongs_to_same_empresa(obj, user))

    def test_null_empresa(self):
        """Test: Empresa nula retorna False"""
        obj = Mock(empresa=None)
        user = Mock(empresa=Mock())

        self.assertFalse(belongs_to_same_empresa(obj, user))


class RequirePermissionDecoratorTest(TestCase):
    """Tests para require_permission decorator"""

    def test_decorator_sets_permission_required(self):
        """Test: Decorador asigna permission_required"""
        @require_permission('test.perm')
        def my_action(self, request):
            pass

        self.assertEqual(my_action.permission_required, 'test.perm')

    def test_decorator_preserves_function(self):
        """Test: Decorador preserva la función"""
        @require_permission('test.perm')
        def my_action(self, request):
            return 'result'

        self.assertEqual(my_action(None, None), 'result')


class RequireSameEmpresaDecoratorTest(TestCase):
    """Tests para require_same_empresa decorator"""

    def test_superuser_bypasses_check(self):
        """Test: Superusuario bypasea verificación"""
        @require_same_empresa
        def my_action(self, request):
            return 'result'

        mock_self = Mock()
        mock_self.get_object = Mock(return_value=Mock(empresa=Mock()))
        mock_request = Mock()
        mock_request.user = Mock(
            is_superuser=True,
            is_staff=False
        )

        result = my_action(mock_self, mock_request)
        self.assertEqual(result, 'result')

    def test_same_empresa_allowed(self):
        """Test: Misma empresa permite ejecución"""
        @require_same_empresa
        def my_action(self, request):
            return 'result'

        empresa = Mock()
        mock_self = Mock()
        mock_self.get_object = Mock(return_value=Mock(empresa=empresa))
        mock_request = Mock()
        mock_request.user = Mock(
            is_superuser=False,
            is_staff=False,
            empresa=empresa
        )

        result = my_action(mock_self, mock_request)
        self.assertEqual(result, 'result')

    def test_different_empresa_raises_permission_denied(self):
        """Test: Diferente empresa lanza PermissionDenied"""
        from rest_framework.exceptions import PermissionDenied

        @require_same_empresa
        def my_action(self, request):
            return 'result'

        mock_self = Mock()
        mock_self.get_object = Mock(return_value=Mock(empresa=Mock()))
        mock_request = Mock()
        mock_request.user = Mock(
            is_superuser=False,
            is_staff=False,
            empresa=Mock()  # Diferente empresa
        )

        with self.assertRaises(PermissionDenied):
            my_action(mock_self, mock_request)


class CreateMockRequestTest(TestCase):
    """Tests para create_mock_request()"""

    def test_creates_get_request(self):
        """Test: Crea request GET"""
        user = Mock(is_authenticated=True)
        request = create_mock_request(user, method='GET')

        self.assertEqual(request.user, user)
        self.assertEqual(request.method, 'GET')

    def test_creates_post_request(self):
        """Test: Crea request POST"""
        user = Mock(is_authenticated=True)
        request = create_mock_request(user, method='POST')

        self.assertEqual(request.user, user)
        self.assertEqual(request.method, 'POST')


class GetCachedPermissionTest(TestCase):
    """Tests para get_cached_permission()"""

    def test_unauthenticated_returns_false(self):
        """Test: Usuario no autenticado retorna False"""
        user = Mock(is_authenticated=False)
        self.assertFalse(get_cached_permission(user, 'test.perm'))

    def test_superuser_returns_true_without_cache(self):
        """Test: Superusuario retorna True sin usar caché"""
        user = Mock(
            is_authenticated=True,
            is_superuser=True,
            is_staff=False,
            pk=1
        )
        self.assertTrue(get_cached_permission(user, 'test.perm'))

    def test_caches_permission_result(self):
        """Test: Cachea resultado de permiso"""
        from django.core.cache import cache

        user = Mock(
            is_authenticated=True,
            is_superuser=False,
            is_staff=False,
            pk=1
        )
        user.has_perm = Mock(return_value=True)

        # Primera llamada - debería consultar y cachear
        result1 = get_cached_permission(user, 'test.perm')
        self.assertTrue(result1)

        # Verificar que se guardó en caché
        cache_key = f"perm:{user.pk}:test.perm"
        cached_value = cache.get(cache_key)
        self.assertTrue(cached_value)

        # Limpiar
        cache.delete(cache_key)


class GetUserPermissionsSummaryTest(TestCase):
    """Tests para get_user_permissions_summary()"""

    def test_unauthenticated_user(self):
        """Test: Usuario no autenticado"""
        user = Mock(is_authenticated=False)
        summary = get_user_permissions_summary(user)

        self.assertFalse(summary['is_authenticated'])
        self.assertEqual(summary['direct_permissions'], [])

    def test_none_user(self):
        """Test: Usuario None"""
        summary = get_user_permissions_summary(None)

        self.assertFalse(summary['is_authenticated'])

    def test_superuser_summary_with_real_user(self):
        """Test: Resumen de superusuario con usuario real"""
        # Crear un usuario real para evitar problemas con Mock y queries
        user = User.objects.create_superuser(
            username='testsuperuser',
            email='super@test.com',
            password='testpass123'
        )

        summary = get_user_permissions_summary(user)

        self.assertTrue(summary['is_authenticated'])
        self.assertTrue(summary['is_superuser'])
        self.assertIn('direct_permissions', summary)
        self.assertIn('group_permissions', summary)
        self.assertIn('all_permissions', summary)
        self.assertIn('groups', summary)

        # Cleanup
        user.delete()

    def test_regular_user_summary(self):
        """Test: Resumen de usuario regular"""
        user = User.objects.create_user(
            username='testregular',
            email='regular@test.com',
            password='testpass123'
        )

        summary = get_user_permissions_summary(user)

        self.assertTrue(summary['is_authenticated'])
        self.assertFalse(summary['is_superuser'])
        self.assertFalse(summary['is_staff'])
        self.assertIsInstance(summary['direct_permissions'], list)
        self.assertIsInstance(summary['group_permissions'], list)

        # Cleanup
        user.delete()

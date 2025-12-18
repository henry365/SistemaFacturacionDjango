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

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User
from empresas.models import Empresa


class UserModelTest(TestCase):
    """Tests para el modelo User"""

    def setUp(self):
        """Configuración inicial para los tests"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_usuario_basico(self):
        """Test: Crear un usuario básico"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            empresa=self.empresa
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@test.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.empresa, self.empresa)

    def test_crear_superusuario(self):
        """Test: Crear superusuario"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_rol_por_defecto(self):
        """Test: Rol por defecto es facturador"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            empresa=self.empresa
        )
        self.assertEqual(user.rol, 'facturador')

    def test_roles_validos(self):
        """Test: Crear usuarios con diferentes roles"""
        roles = ['admin', 'facturador', 'cajero', 'almacen', 'compras', 'contabilidad']
        for i, rol in enumerate(roles):
            user = User.objects.create_user(
                username=f'user_{rol}',
                password='testpass123',
                rol=rol,
                empresa=self.empresa
            )
            self.assertEqual(user.rol, rol)

    def test_admin_rol_es_staff(self):
        """Test: Usuario con rol admin se convierte en staff"""
        user = User.objects.create_user(
            username='admin_user',
            password='testpass123',
            rol='admin',
            empresa=self.empresa
        )
        self.assertTrue(user.is_staff)

    def test_usuario_str(self):
        """Test: Representación string de usuario"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='facturador',
            empresa=self.empresa
        )
        self.assertEqual(str(user), 'testuser - Facturador')

    def test_asignacion_grupo_automatica(self):
        """Test: Usuario se asigna automáticamente al grupo de su rol"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='cajero',
            empresa=self.empresa
        )
        # El signal debe haber creado/asignado el grupo
        self.assertTrue(user.groups.filter(name='cajero').exists())

    def test_clean_username_vacio(self):
        """Test: Username no puede estar vacío"""
        user = User(username='   ', password='test123', empresa=self.empresa)
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn('username', context.exception.message_dict)

    def test_email_normalizado(self):
        """Test: Email se normaliza a minúsculas"""
        user = User(
            username='testuser',
            email='  TEST@TEST.COM  ',
            empresa=self.empresa
        )
        user.clean()
        self.assertEqual(user.email, 'test@test.com')

    def test_telefono_normalizado(self):
        """Test: Teléfono se normaliza (strip)"""
        user = User(
            username='testuser',
            telefono='  809-555-1234  ',
            empresa=self.empresa
        )
        user.clean()
        self.assertEqual(user.telefono, '809-555-1234')


class UserSerializerTest(TestCase):
    """Tests para los serializers de Usuario"""

    def setUp(self):
        """Configuración inicial"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_user_create_serializer_valido(self):
        """Test: UserCreateSerializer con datos válidos"""
        from .serializers import UserCreateSerializer
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'rol': 'facturador',
            'empresa': self.empresa.id
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_create_serializer_passwords_no_coinciden(self):
        """Test: Error si passwords no coinciden"""
        from .serializers import UserCreateSerializer
        data = {
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'empresa': self.empresa.id
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_user_create_serializer_password_debil(self):
        """Test: Error si password es débil"""
        from .serializers import UserCreateSerializer
        data = {
            'username': 'newuser',
            'password': '123',
            'password_confirm': '123',
            'empresa': self.empresa.id
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_user_serializer_email_valido(self):
        """Test: Validación de email"""
        from .serializers import UserSerializer
        user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        data = {'email': 'invalid-email'}
        serializer = UserSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_user_serializer_telefono_valido(self):
        """Test: Validación de teléfono"""
        from .serializers import UserSerializer
        user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        data = {'telefono': 'abc123'}
        serializer = UserSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('telefono', serializer.errors)

    def test_change_password_serializer_password_actual_incorrecto(self):
        """Test: Error si password actual es incorrecto"""
        from .serializers import ChangePasswordSerializer
        from rest_framework.test import APIRequestFactory

        user = User.objects.create_user(
            username='testuser',
            password='correctpassword123',
            empresa=self.empresa
        )
        factory = APIRequestFactory()
        request = factory.post('/cambiar_password/')
        request.user = user

        data = {
            'password_actual': 'wrongpassword',
            'password_nuevo': 'NewSecure123!',
            'password_confirm': 'NewSecure123!'
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_actual', serializer.errors)


class UserAPITest(APITestCase):
    """Tests para la API de Usuario"""

    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.empresa2 = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )

        # Superusuario
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            email='super@test.com',
            password='super123',
            empresa=self.empresa
        )

        # Admin de empresa
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            rol='admin',
            empresa=self.empresa
        )

        # Usuario normal
        self.user = User.objects.create_user(
            username='usuario',
            email='usuario@test.com',
            password='user123',
            rol='facturador',
            empresa=self.empresa
        )

        # Usuario de otra empresa
        self.user_otra = User.objects.create_user(
            username='otro',
            email='otro@test.com',
            password='otro123',
            empresa=self.empresa2
        )

        self.client = APIClient()

    def test_login_exitoso(self):
        """Test: Login con credenciales válidas"""
        data = {
            'empresa_username': 'Empresa Principal',
            'username': 'usuario',
            'password': 'user123'
        }
        response = self.client.post('/api/v1/auth/token/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_empresa_incorrecta(self):
        """Test: Login falla si empresa no existe"""
        data = {
            'empresa_username': 'Empresa Inexistente',
            'username': 'usuario',
            'password': 'user123'
        }
        response = self.client.post('/api/v1/auth/token/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_credenciales_incorrectas(self):
        """Test: Login falla con credenciales incorrectas"""
        data = {
            'empresa_username': 'Empresa Principal',
            'username': 'usuario',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/v1/auth/token/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_usuario_otra_empresa(self):
        """Test: Login falla si usuario no pertenece a la empresa"""
        data = {
            'empresa_username': 'Empresa Principal',
            'username': 'otro',  # Usuario de otra empresa
            'password': 'otro123'
        }
        response = self.client.post('/api/v1/auth/token/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validar_empresa_existente(self):
        """Test: Validar empresa existente"""
        data = {'empresa_username': 'Empresa Principal'}
        response = self.client.post('/api/v1/auth/validar-empresa/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valida'])

    def test_validar_empresa_inexistente(self):
        """Test: Validar empresa inexistente"""
        data = {'empresa_username': 'No Existe'}
        response = self.client.post('/api/v1/auth/validar-empresa/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_perfil_usuario_autenticado(self):
        """Test: Obtener perfil del usuario autenticado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/usuarios/perfil/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'usuario')

    def test_actualizar_perfil(self):
        """Test: Actualizar perfil propio"""
        self.client.force_authenticate(user=self.user)
        data = {'first_name': 'Nombre Actualizado'}
        response = self.client.patch('/api/v1/usuarios/actualizar_perfil/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Nombre Actualizado')

    def test_cambiar_password(self):
        """Test: Cambiar contraseña"""
        self.client.force_authenticate(user=self.user)
        data = {
            'password_actual': 'user123',
            'password_nuevo': 'NewSecure123!',
            'password_confirm': 'NewSecure123!'
        }
        response = self.client.post('/api/v1/usuarios/cambiar_password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que el password fue cambiado
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure123!'))

    def test_admin_puede_listar_usuarios_empresa(self):
        """Test: Admin con permisos puede listar usuarios de su empresa"""
        # Asignar permiso view_user al admin
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(User)
        view_permission = Permission.objects.get(
            codename='view_user',
            content_type=content_type
        )
        self.admin.user_permissions.add(view_permission)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin ve usuarios de su empresa (superadmin, admin, usuario)
        usernames = [u['username'] for u in response.data['results']]
        self.assertIn('admin', usernames)
        self.assertIn('usuario', usernames)
        # No debe ver usuario de otra empresa
        self.assertNotIn('otro', usernames)

    def test_superuser_puede_listar_todos_usuarios(self):
        """Test: Superuser puede listar usuarios de su empresa"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_usuario_normal_solo_ve_su_perfil(self):
        """Test: Usuario normal solo ve su propio perfil en lista"""
        # Asignar permiso view_user al usuario
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(User)
        view_permission = Permission.objects.get(
            codename='view_user',
            content_type=content_type
        )
        self.user.user_permissions.add(view_permission)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'usuario')

    def test_usuario_sin_permisos_recibe_403(self):
        """Test: Usuario sin permisos recibe 403"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/usuarios/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_puede_crear_usuario(self):
        """Test: Superuser puede crear usuario"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'rol': 'cajero'
        }
        response = self.client.post('/api/v1/usuarios/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # El usuario hereda la empresa del creador
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.empresa, self.empresa)

    def test_activar_desactivar_usuario(self):
        """Test: Admin puede activar/desactivar usuarios"""
        self.client.force_authenticate(user=self.superuser)

        # Desactivar
        response = self.client.post(f'/api/v1/usuarios/{self.user.id}/desactivar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # Activar
        response = self.client.post(f'/api/v1/usuarios/{self.user.id}/activar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_filtrar_usuarios_por_rol(self):
        """Test: Filtrar usuarios por rol"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/usuarios/?rol=facturador')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user_data in response.data['results']:
            self.assertEqual(user_data['rol'], 'facturador')

    def test_buscar_usuarios(self):
        """Test: Buscar usuarios"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/usuarios/?search=usuario')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)


class GroupAPITest(APITestCase):
    """Tests para la API de Grupos"""

    def setUp(self):
        """Configuración inicial"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            empresa=self.empresa
        )

        self.user = User.objects.create_user(
            username='user',
            password='user123',
            empresa=self.empresa
        )

        self.client = APIClient()

    def test_solo_admin_puede_listar_grupos(self):
        """Test: Solo admin puede listar grupos"""
        # Usuario normal
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/grupos/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/grupos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_grupo(self):
        """Test: Admin puede crear grupo"""
        self.client.force_authenticate(user=self.superuser)
        data = {'name': 'nuevo_grupo'}
        response = self.client.post('/api/v1/grupos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Group.objects.filter(name='nuevo_grupo').exists())

    def test_asignar_permisos_a_grupo(self):
        """Test: Asignar permisos a grupo"""
        self.client.force_authenticate(user=self.superuser)
        grupo = Group.objects.create(name='test_group')
        permisos = Permission.objects.all()[:3]

        data = {'permisos': [p.id for p in permisos]}
        response = self.client.post(f'/api/v1/grupos/{grupo.id}/asignar_permisos/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(grupo.permissions.count(), 3)

    def test_listar_usuarios_de_grupo(self):
        """Test: Listar usuarios de un grupo"""
        self.client.force_authenticate(user=self.superuser)
        grupo = Group.objects.create(name='test_group')
        self.user.groups.add(grupo)

        response = self.client.get(f'/api/v1/grupos/{grupo.id}/usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_usuarios'], 1)


class PermissionAPITest(APITestCase):
    """Tests para la API de Permisos"""

    def setUp(self):
        """Configuración inicial"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            empresa=self.empresa
        )

        self.user = User.objects.create_user(
            username='user',
            password='user123',
            empresa=self.empresa
        )

        self.client = APIClient()

    def test_solo_admin_puede_listar_permisos(self):
        """Test: Solo admin puede listar permisos"""
        # Usuario normal
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/permisos/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/permisos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_permisos_por_app(self):
        """Test: Filtrar permisos por app_label"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/permisos/?app_label=usuarios')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for permiso in response.data['results']:
            self.assertEqual(permiso['app_label'], 'usuarios')

    def test_permisos_son_solo_lectura(self):
        """Test: No se pueden crear permisos via API"""
        self.client.force_authenticate(user=self.superuser)
        data = {'name': 'test_permission', 'codename': 'test_perm'}
        response = self.client.post('/api/v1/permisos/', data)
        # ReadOnlyModelViewSet no permite POST
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

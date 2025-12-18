from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from .models import Vendedor
from empresas.models import Empresa
from usuarios.models import User


class VendedorModelTest(TestCase):
    """Tests para el modelo Vendedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_vendedor_basico(self):
        """Test: Crear vendedor básico"""
        vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Test',
            telefono='809-555-1234'
        )
        self.assertEqual(vendedor.nombre, 'Vendedor Test')
        self.assertTrue(vendedor.activo)
        self.assertEqual(vendedor.comision_porcentaje, Decimal('0.00'))

    def test_crear_vendedor_completo(self):
        """Test: Crear vendedor con todos los campos"""
        vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Completo',
            cedula='001-0000000-0',
            telefono='809-555-1234',
            correo='vendedor@test.com',
            comision_porcentaje=Decimal('10.00')
        )
        self.assertEqual(vendedor.cedula, '001-0000000-0')
        self.assertEqual(vendedor.comision_porcentaje, Decimal('10.00'))

    def test_vendedor_str(self):
        """Test: Representación string de vendedor"""
        vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Juan Pérez'
        )
        self.assertIn('Juan Pérez', str(vendedor))
        self.assertIn('Empresa Test', str(vendedor))

    def test_vendedor_str_sin_empresa(self):
        """Test: Representación string de vendedor sin empresa"""
        vendedor = Vendedor.objects.create(
            nombre='Vendedor Sin Empresa'
        )
        self.assertIn('Sin empresa', str(vendedor))

    def test_validacion_comision_negativa(self):
        """Test: Comisión negativa falla validación"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='Test',
            comision_porcentaje=Decimal('-5.00')
        )
        with self.assertRaises(ValidationError) as context:
            vendedor.clean()
        self.assertIn('comision_porcentaje', context.exception.message_dict)

    def test_validacion_comision_mayor_100(self):
        """Test: Comisión mayor a 100 falla validación"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='Test',
            comision_porcentaje=Decimal('150.00')
        )
        with self.assertRaises(ValidationError) as context:
            vendedor.clean()
        self.assertIn('comision_porcentaje', context.exception.message_dict)

    def test_validacion_comision_valida(self):
        """Test: Comisión válida pasa validación"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='Test',
            comision_porcentaje=Decimal('25.50')
        )
        vendedor.clean()  # Should not raise

    def test_cedula_unica_por_empresa(self):
        """Test: Cédula es única por empresa"""
        Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor 1',
            cedula='001-0000000-0'
        )
        with self.assertRaises(Exception):
            Vendedor.objects.create(
                empresa=self.empresa,
                nombre='Vendedor 2',
                cedula='001-0000000-0'
            )

    def test_cedula_puede_repetirse_entre_empresas(self):
        """Test: Cédula puede repetirse en diferentes empresas"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor 1',
            cedula='001-0000000-0'
        )
        vendedor2 = Vendedor.objects.create(
            empresa=otra_empresa,
            nombre='Vendedor 2',
            cedula='001-0000000-0'
        )
        self.assertEqual(vendedor2.cedula, '001-0000000-0')

    def test_email_normalizado(self):
        """Test: Email se normaliza a minúsculas"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='Test',
            correo='  TEST@TEST.COM  '
        )
        vendedor.clean()
        self.assertEqual(vendedor.correo, 'test@test.com')

    def test_nombre_normalizado(self):
        """Test: Nombre se normaliza (strip)"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='  Vendedor Test  '
        )
        vendedor.clean()
        self.assertEqual(vendedor.nombre, 'Vendedor Test')

    def test_nombre_vacio_falla(self):
        """Test: Nombre vacío falla validación"""
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='   '
        )
        with self.assertRaises(ValidationError) as context:
            vendedor.clean()
        self.assertIn('nombre', context.exception.message_dict)

    def test_uuid_generado_automaticamente(self):
        """Test: UUID se genera automáticamente"""
        vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Test'
        )
        self.assertIsNotNone(vendedor.uuid)

    def test_vendedor_con_usuario_asociado(self):
        """Test: Vendedor con usuario del sistema asociado"""
        user = User.objects.create_user(
            username='vendedor_user',
            password='test123',
            empresa=self.empresa
        )
        vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Usuario',
            usuario=user
        )
        self.assertEqual(vendedor.usuario, user)
        self.assertEqual(user.vendedor_perfil, vendedor)

    def test_validacion_usuario_misma_empresa(self):
        """Test: Usuario debe pertenecer a la misma empresa"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        user_otra = User.objects.create_user(
            username='user_otra',
            password='test123',
            empresa=otra_empresa
        )
        vendedor = Vendedor(
            empresa=self.empresa,
            nombre='Test',
            usuario=user_otra
        )
        with self.assertRaises(ValidationError) as context:
            vendedor.clean()
        self.assertIn('usuario', context.exception.message_dict)


class VendedorAPITest(APITestCase):
    """Tests para la API de Vendedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            empresa=self.empresa
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='facturador'
        )

        # Asignar permisos al usuario
        content_type = ContentType.objects.get_for_model(Vendedor)
        for codename in ['view_vendedor', 'add_vendedor', 'change_vendedor', 'delete_vendedor']:
            perm = Permission.objects.get(codename=codename, content_type=content_type)
            self.user.user_permissions.add(perm)

        self.vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Test',
            cedula='111-1111111-1',
            telefono='809-555-1234',
            comision_porcentaje=Decimal('5.00')
        )

        self.client = APIClient()

    def test_listar_vendedores(self):
        """Test: Listar vendedores"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/vendedores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_crear_vendedor(self):
        """Test: Crear vendedor"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nuevo Vendedor',
            'cedula': '222-2222222-2',
            'telefono': '809-555-5555',
            'comision_porcentaje': '10.00'
        }
        response = self.client.post('/api/v1/vendedores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Nuevo Vendedor')

    def test_obtener_vendedor(self):
        """Test: Obtener vendedor por ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Vendedor Test')

    def test_actualizar_vendedor(self):
        """Test: Actualizar vendedor"""
        self.client.force_authenticate(user=self.user)
        data = {'nombre': 'Vendedor Actualizado'}
        response = self.client.patch(f'/api/v1/vendedores/{self.vendedor.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Vendedor Actualizado')

    def test_buscar_vendedores(self):
        """Test: Buscar vendedores"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/vendedores/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_vendedores_activos(self):
        """Test: Filtrar vendedores activos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/vendedores/?activo=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for vendedor in response.data['results']:
            self.assertTrue(vendedor['activo'])

    def test_filtrar_vendedores_inactivos(self):
        """Test: Filtrar vendedores inactivos"""
        Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Inactivo',
            activo=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/vendedores/?activo=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for vendedor in response.data['results']:
            self.assertFalse(vendedor['activo'])

    def test_estadisticas_vendedor(self):
        """Test: Obtener estadísticas del vendedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/estadisticas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('vendedor', response.data)
        self.assertIn('estadisticas', response.data)
        self.assertIn('total_ventas', response.data['estadisticas'])
        self.assertIn('monto_total_ventas', response.data['estadisticas'])
        self.assertIn('monto_comisiones', response.data['estadisticas'])

    def test_ventas_vendedor(self):
        """Test: Obtener ventas del vendedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/ventas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ventas', response.data)
        self.assertIn('total_ventas', response.data)
        self.assertIn('monto_total', response.data)

    def test_cotizaciones_vendedor(self):
        """Test: Obtener cotizaciones del vendedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/cotizaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cotizaciones', response.data)
        self.assertIn('total_cotizaciones', response.data)

    def test_clientes_vendedor(self):
        """Test: Obtener clientes del vendedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/clientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('clientes', response.data)
        self.assertIn('total_clientes', response.data)

    def test_comisiones_vendedor(self):
        """Test: Calcular comisiones del vendedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/comisiones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumen', response.data)
        self.assertIn('detalle', response.data)
        self.assertIn('monto_total_comisiones', response.data['resumen'])

    def test_comisiones_con_fechas(self):
        """Test: Calcular comisiones con filtro de fechas"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f'/api/v1/vendedores/{self.vendedor.id}/comisiones/',
            {'fecha_inicio': '2024-01-01', 'fecha_fin': '2024-12-31'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['periodo']['fecha_inicio'], '2024-01-01')

    def test_comisiones_fecha_invalida(self):
        """Test: Calcular comisiones con fecha inválida"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f'/api/v1/vendedores/{self.vendedor.id}/comisiones/',
            {'fecha_inicio': 'fecha_invalida'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/vendedores/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crear_vendedor_comision_invalida(self):
        """Test: Crear vendedor con comisión inválida"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Vendedor Test',
            'comision_porcentaje': '150.00'
        }
        response = self.client.post('/api/v1/vendedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_vendedor_telefono_invalido(self):
        """Test: Crear vendedor con teléfono inválido"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Vendedor Test',
            'telefono': 'abc'
        }
        response = self.client.post('/api/v1/vendedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_vendedor_email_invalido(self):
        """Test: Crear vendedor con email inválido"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Vendedor Test',
            'correo': 'email_invalido'
        }
        response = self.client.post('/api/v1/vendedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendedor_empresa_asignada_automaticamente(self):
        """Test: La empresa se asigna automáticamente del usuario"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nuevo Vendedor Auto',
            'cedula': '333-3333333-3'
        }
        response = self.client.post('/api/v1/vendedores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vendedor = Vendedor.objects.get(id=response.data['id'])
        self.assertEqual(vendedor.empresa, self.empresa)

    def test_ordenar_vendedores_por_nombre(self):
        """Test: Ordenar vendedores por nombre"""
        Vendedor.objects.create(
            empresa=self.empresa,
            nombre='AAA Vendedor'
        )
        Vendedor.objects.create(
            empresa=self.empresa,
            nombre='ZZZ Vendedor'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/vendedores/?ordering=nombre')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nombres = [v['nombre'] for v in response.data['results']]
        self.assertEqual(nombres, sorted(nombres))

    def test_serializer_campos_calculados(self):
        """Test: Verificar campos calculados del serializer"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/vendedores/{self.vendedor.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_clientes', response.data)
        self.assertIn('total_ventas', response.data)

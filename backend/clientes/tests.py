from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from .models import Cliente, CategoriaCliente
from empresas.models import Empresa
from usuarios.models import User
from vendedores.models import Vendedor


class CategoriaClienteModelTest(TestCase):
    """Tests para el modelo CategoriaCliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_categoria(self):
        """Test: Crear categoría de cliente"""
        categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='VIP',
            descuento_porcentaje=10
        )
        self.assertEqual(categoria.nombre, 'VIP')
        self.assertEqual(categoria.descuento_porcentaje, 10)
        self.assertTrue(categoria.activa)

    def test_categoria_str(self):
        """Test: Representación string de categoría"""
        categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='Premium'
        )
        self.assertIn('Premium', str(categoria))

    def test_descuento_rango_valido(self):
        """Test: Descuento debe estar entre 0 y 100"""
        categoria = CategoriaCliente(
            empresa=self.empresa,
            nombre='Test',
            descuento_porcentaje=150
        )
        with self.assertRaises(ValidationError):
            categoria.clean()

    def test_nombre_unico_por_empresa(self):
        """Test: Nombre de categoría es único por empresa"""
        CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='VIP'
        )
        with self.assertRaises(Exception):
            CategoriaCliente.objects.create(
                empresa=self.empresa,
                nombre='VIP'
            )


class ClienteModelTest(TestCase):
    """Tests para el modelo Cliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='Regular'
        )

    def test_crear_cliente_basico(self):
        """Test: Crear cliente básico"""
        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='809-555-1234'
        )
        self.assertEqual(cliente.nombre, 'Cliente Test')
        self.assertTrue(cliente.activo)
        self.assertEqual(cliente.limite_credito, 0)

    def test_crear_cliente_completo(self):
        """Test: Crear cliente con todos los campos"""
        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Completo',
            tipo_identificacion='RNC',
            numero_identificacion='123456789',
            telefono='809-555-1234',
            correo_electronico='cliente@test.com',
            direccion='Calle Test #123',
            limite_credito=Decimal('50000.00'),
            categoria=self.categoria
        )
        self.assertEqual(cliente.tipo_identificacion, 'RNC')
        self.assertEqual(cliente.limite_credito, Decimal('50000.00'))

    def test_cliente_str(self):
        """Test: Representación string de cliente"""
        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Test S.A.',
            numero_identificacion='123456789'
        )
        self.assertIn('Test S.A.', str(cliente))
        self.assertIn('123456789', str(cliente))

    def test_validacion_rnc_requiere_numero(self):
        """Test: RNC requiere número de identificación"""
        cliente = Cliente(
            empresa=self.empresa,
            nombre='Test',
            tipo_identificacion='RNC',
            numero_identificacion=''
        )
        with self.assertRaises(ValidationError) as context:
            cliente.clean()
        self.assertIn('numero_identificacion', context.exception.message_dict)

    def test_validacion_limite_credito_no_negativo(self):
        """Test: Límite de crédito no puede ser negativo"""
        cliente = Cliente(
            empresa=self.empresa,
            nombre='Test',
            limite_credito=-100
        )
        with self.assertRaises(ValidationError) as context:
            cliente.clean()
        self.assertIn('limite_credito', context.exception.message_dict)

    def test_validacion_categoria_misma_empresa(self):
        """Test: Categoría debe ser de la misma empresa"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        categoria_otra = CategoriaCliente.objects.create(
            empresa=otra_empresa,
            nombre='Otra'
        )
        cliente = Cliente(
            empresa=self.empresa,
            nombre='Test',
            categoria=categoria_otra
        )
        with self.assertRaises(ValidationError) as context:
            cliente.clean()
        self.assertIn('categoria', context.exception.message_dict)

    def test_numero_identificacion_unico_por_empresa(self):
        """Test: Número de identificación es único por empresa"""
        Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente 1',
            numero_identificacion='123456789'
        )
        with self.assertRaises(Exception):
            Cliente.objects.create(
                empresa=self.empresa,
                nombre='Cliente 2',
                numero_identificacion='123456789'
            )

    def test_email_normalizado(self):
        """Test: Email se normaliza a minúsculas"""
        cliente = Cliente(
            empresa=self.empresa,
            nombre='Test',
            correo_electronico='  TEST@TEST.COM  '
        )
        cliente.clean()
        self.assertEqual(cliente.correo_electronico, 'test@test.com')


class ClienteAPITest(APITestCase):
    """Tests para la API de Cliente"""

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
        content_type = ContentType.objects.get_for_model(Cliente)
        for codename in ['view_cliente', 'add_cliente', 'change_cliente', 'delete_cliente']:
            perm = Permission.objects.get(codename=codename, content_type=content_type)
            self.user.user_permissions.add(perm)

        self.categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='VIP',
            descuento_porcentaje=10
        )

        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='111111111',
            telefono='809-555-1234',
            limite_credito=Decimal('10000.00'),
            categoria=self.categoria
        )

        self.client = APIClient()

    def test_listar_clientes(self):
        """Test: Listar clientes"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/clientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_crear_cliente(self):
        """Test: Crear cliente"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nuevo Cliente',
            'tipo_identificacion': 'CEDULA',
            'numero_identificacion': '001-0000000-0',
            'telefono': '809-555-5555',
            'limite_credito': '5000.00'
        }
        response = self.client.post('/api/v1/clientes/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Nuevo Cliente')

    def test_obtener_cliente(self):
        """Test: Obtener cliente por ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/clientes/{self.cliente.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Cliente Test')

    def test_actualizar_cliente(self):
        """Test: Actualizar cliente"""
        self.client.force_authenticate(user=self.user)
        data = {'nombre': 'Cliente Actualizado'}
        response = self.client.patch(f'/api/v1/clientes/{self.cliente.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Cliente Actualizado')

    def test_buscar_clientes(self):
        """Test: Buscar clientes"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/clientes/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_clientes_por_categoria(self):
        """Test: Filtrar clientes por categoría"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/clientes/?categoria={self.categoria.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cliente in response.data['results']:
            self.assertEqual(cliente['categoria'], self.categoria.id)

    def test_filtrar_clientes_activos(self):
        """Test: Filtrar clientes activos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/clientes/?activo=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cliente in response.data['results']:
            self.assertTrue(cliente['activo'])

    def test_historial_compras(self):
        """Test: Obtener historial de compras del cliente"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/clientes/{self.cliente.id}/historial_compras/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('facturas', response.data)
        self.assertIn('total_ventas', response.data)

    def test_historial_pagos(self):
        """Test: Obtener historial de pagos del cliente"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/clientes/{self.cliente.id}/historial_pagos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pagos', response.data)
        self.assertIn('total_monto', response.data)

    def test_resumen_cliente(self):
        """Test: Obtener resumen del cliente"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/clientes/{self.cliente.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cliente', response.data)
        self.assertIn('estadisticas', response.data)
        self.assertIn('saldo_actual', response.data['estadisticas'])
        self.assertIn('credito_disponible', response.data['estadisticas'])

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/clientes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoriaClienteAPITest(APITestCase):
    """Tests para la API de CategoriaCliente"""

    def setUp(self):
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

        self.categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='VIP',
            descuento_porcentaje=15
        )

        self.client = APIClient()

    def test_listar_categorias(self):
        """Test: Listar categorías de clientes"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/categorias-clientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_categoria(self):
        """Test: Crear categoría de cliente"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'nombre': 'Premium',
            'descripcion': 'Clientes premium',
            'descuento_porcentaje': '20.00'
        }
        response = self.client.post('/api/v1/categorias-clientes/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Premium')

    def test_filtrar_categorias_activas(self):
        """Test: Filtrar categorías activas"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/categorias-clientes/?activa=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cat in response.data['results']:
            self.assertTrue(cat['activa'])

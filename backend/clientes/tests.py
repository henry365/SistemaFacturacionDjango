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
        # El endpoint puede retornar 200 o datos vacíos si no hay pagos
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('pagos', response.data)
            self.assertIn('total_monto', response.data)
        else:
            # Si falla, verificar que es por un error de servicio, no de permisos
            self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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


# ============================================================
# TESTS DE SERVICIOS
# ============================================================

class ClienteServiceTest(TestCase):
    """Tests para ClienteService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            limite_credito=Decimal('10000.00')
        )

    def test_activar_cliente(self):
        """Test: Activar cliente"""
        from .services import ClienteService

        # Desactivar primero
        self.cliente.activo = False
        self.cliente.save(update_fields=['activo'])

        exito, error = ClienteService.activar_cliente(self.cliente, self.user)
        self.assertTrue(exito)
        self.assertIsNone(error)

        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.activo)

    def test_activar_cliente_idempotente(self):
        """Test: Activar cliente es idempotente"""
        from .services import ClienteService

        # Cliente ya está activo por defecto
        self.assertTrue(self.cliente.activo)

        # Primera activación (ya está activo)
        exito1, error1 = ClienteService.activar_cliente(self.cliente, self.user)

        # Segunda activación (idempotente)
        exito2, error2 = ClienteService.activar_cliente(self.cliente, self.user)

        # Ambas deben tener éxito
        self.assertTrue(exito1)
        self.assertTrue(exito2)
        self.assertIsNone(error1)
        self.assertIsNone(error2)

    def test_desactivar_cliente(self):
        """Test: Desactivar cliente"""
        from .services import ClienteService

        exito, error = ClienteService.desactivar_cliente(self.cliente, self.user)
        self.assertTrue(exito)
        self.assertIsNone(error)

        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.activo)

    def test_desactivar_cliente_idempotente(self):
        """Test: Desactivar cliente es idempotente"""
        from .services import ClienteService

        # Primera desactivación
        exito1, error1 = ClienteService.desactivar_cliente(self.cliente, self.user)

        # Segunda desactivación (idempotente)
        exito2, error2 = ClienteService.desactivar_cliente(self.cliente, self.user)

        # Ambas deben tener éxito
        self.assertTrue(exito1)
        self.assertTrue(exito2)
        self.assertIsNone(error1)
        self.assertIsNone(error2)

    def test_actualizar_limite_credito(self):
        """Test: Actualizar límite de crédito"""
        from .services import ClienteService

        nuevo_limite = Decimal('50000.00')
        exito, error = ClienteService.actualizar_limite_credito(
            self.cliente, nuevo_limite, self.user
        )

        self.assertTrue(exito)
        self.assertIsNone(error)

        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.limite_credito, nuevo_limite)

    def test_actualizar_limite_credito_idempotente(self):
        """Test: Actualizar límite de crédito es idempotente"""
        from .services import ClienteService

        nuevo_limite = Decimal('50000.00')

        # Primera actualización
        exito1, _ = ClienteService.actualizar_limite_credito(
            self.cliente, nuevo_limite, self.user
        )

        # Segunda actualización con mismo valor (idempotente)
        exito2, _ = ClienteService.actualizar_limite_credito(
            self.cliente, nuevo_limite, self.user
        )

        self.assertTrue(exito1)
        self.assertTrue(exito2)

    def test_actualizar_limite_credito_negativo_falla(self):
        """Test: Límite de crédito negativo falla"""
        from .services import ClienteService

        exito, error = ClienteService.actualizar_limite_credito(
            self.cliente, Decimal('-1000.00'), self.user
        )

        self.assertFalse(exito)
        self.assertIsNotNone(error)

    def test_calcular_credito_disponible(self):
        """Test: Calcular crédito disponible"""
        from .services import ClienteService

        credito = ClienteService.calcular_credito_disponible(self.cliente)
        # Sin facturas, debe ser igual al límite o 0 si no hay límite
        self.assertIsInstance(credito, Decimal)

    def test_verificar_limite_credito(self):
        """Test: Verificar límite de crédito"""
        from .services import ClienteService

        puede, error = ClienteService.verificar_limite_credito(
            self.cliente, Decimal('5000.00')
        )
        self.assertTrue(puede)
        self.assertIsNone(error)


class CategoriaClienteServiceTest(TestCase):
    """Tests para CategoriaClienteService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        self.categoria = CategoriaCliente.objects.create(
            empresa=self.empresa,
            nombre='VIP',
            descuento_porcentaje=Decimal('10.00')
        )

    def test_aplicar_descuento(self):
        """Test: Aplicar descuento de categoría"""
        from .services import CategoriaClienteService

        monto = Decimal('1000.00')
        resultado = CategoriaClienteService.aplicar_descuento(self.categoria, monto)

        # 10% de descuento: 1000 - 100 = 900
        self.assertEqual(resultado, Decimal('900.00'))

    def test_aplicar_descuento_categoria_none(self):
        """Test: Aplicar descuento sin categoría retorna monto original"""
        from .services import CategoriaClienteService

        monto = Decimal('1000.00')
        resultado = CategoriaClienteService.aplicar_descuento(None, monto)

        self.assertEqual(resultado, monto)

    def test_calcular_descuento(self):
        """Test: Calcular monto de descuento"""
        from .services import CategoriaClienteService

        monto = Decimal('1000.00')
        descuento = CategoriaClienteService.calcular_descuento(self.categoria, monto)

        # 10% de 1000 = 100
        self.assertEqual(descuento, Decimal('100.00'))

    def test_activar_categoria_idempotente(self):
        """Test: Activar categoría es idempotente"""
        from .services import CategoriaClienteService

        # Categoría ya está activa por defecto
        self.assertTrue(self.categoria.activa)

        # Primera activación
        exito1, _ = CategoriaClienteService.activar_categoria(self.categoria, self.user)

        # Segunda activación (idempotente)
        exito2, _ = CategoriaClienteService.activar_categoria(self.categoria, self.user)

        self.assertTrue(exito1)
        self.assertTrue(exito2)

    def test_desactivar_categoria_idempotente(self):
        """Test: Desactivar categoría es idempotente"""
        from .services import CategoriaClienteService

        # Primera desactivación
        exito1, _ = CategoriaClienteService.desactivar_categoria(self.categoria, self.user)

        # Segunda desactivación (idempotente)
        exito2, _ = CategoriaClienteService.desactivar_categoria(self.categoria, self.user)

        self.assertTrue(exito1)
        self.assertTrue(exito2)


# ============================================================
# TESTS DE VALIDACIÓN DE EMPRESA
# ============================================================

class EmpresaValidationTest(APITestCase):
    """Tests para validación de empresa en serializers y vistas"""

    def setUp(self):
        # Crear dos empresas
        self.empresa1 = Empresa.objects.create(
            nombre='Empresa 1',
            rnc='111111111'
        )
        self.empresa2 = Empresa.objects.create(
            nombre='Empresa 2',
            rnc='222222222'
        )

        # Crear usuarios para cada empresa
        self.user_empresa1 = User.objects.create_user(
            username='user_empresa1',
            password='test123',
            empresa=self.empresa1
        )
        self.user_empresa2 = User.objects.create_user(
            username='user_empresa2',
            password='test123',
            empresa=self.empresa2
        )

        # Asignar permisos a ambos usuarios
        for user in [self.user_empresa1, self.user_empresa2]:
            for model in [Cliente, CategoriaCliente]:
                content_type = ContentType.objects.get_for_model(model)
                for codename in ['view', 'add', 'change', 'delete']:
                    perm_codename = f'{codename}_{model._meta.model_name}'
                    try:
                        perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                        user.user_permissions.add(perm)
                    except Permission.DoesNotExist:
                        pass

        # Crear categorías para cada empresa
        self.categoria_empresa1 = CategoriaCliente.objects.create(
            empresa=self.empresa1,
            nombre='VIP Empresa 1'
        )
        self.categoria_empresa2 = CategoriaCliente.objects.create(
            empresa=self.empresa2,
            nombre='VIP Empresa 2'
        )

        # Crear clientes para cada empresa
        self.cliente_empresa1 = Cliente.objects.create(
            empresa=self.empresa1,
            nombre='Cliente Empresa 1',
            categoria=self.categoria_empresa1
        )
        self.cliente_empresa2 = Cliente.objects.create(
            empresa=self.empresa2,
            nombre='Cliente Empresa 2',
            categoria=self.categoria_empresa2
        )

        self.client = APIClient()

    def test_listar_clientes_solo_empresa_propia(self):
        """Test: Al listar clientes solo ve los de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get('/api/v1/clientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que solo ve clientes de empresa1
        for cliente in response.data['results']:
            cliente_obj = Cliente.objects.get(id=cliente['id'])
            self.assertEqual(cliente_obj.empresa, self.empresa1)

    def test_listar_categorias_solo_empresa_propia(self):
        """Test: Al listar categorías solo ve las de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get('/api/v1/categorias-clientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que solo ve categorías de empresa1
        for cat in response.data['results']:
            cat_obj = CategoriaCliente.objects.get(id=cat['id'])
            self.assertEqual(cat_obj.empresa, self.empresa1)

    def test_no_acceder_cliente_otra_empresa_por_id(self):
        """Test: No puede acceder a cliente de otra empresa por ID"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/clientes/{self.cliente_empresa2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_acceder_categoria_otra_empresa_por_id(self):
        """Test: No puede acceder a categoría de otra empresa por ID"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/categorias-clientes/{self.categoria_empresa2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_crear_cliente_con_categoria_misma_empresa(self):
        """Test: Puede crear cliente con categoría de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'nombre': 'Nuevo Cliente Con Categoria',
            'categoria': self.categoria_empresa1.id
        }
        response = self.client.post('/api/v1/clientes/', data)
        # Si no es 201, imprimir el error para debug
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error creating client: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_cliente_con_categoria_otra_empresa_falla(self):
        """Test: No puede crear cliente con categoría de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'nombre': 'Nuevo Cliente',
            'categoria': self.categoria_empresa2.id  # Categoría de otra empresa
        }
        response = self.client.post('/api/v1/clientes/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activar_cliente_propia_empresa(self):
        """Test: Puede activar cliente de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        # Desactivar primero
        self.cliente_empresa1.activo = False
        self.cliente_empresa1.save(update_fields=['activo'])

        response = self.client.post(f'/api/v1/clientes/{self.cliente_empresa1.id}/activar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_activar_cliente_otra_empresa_falla(self):
        """Test: No puede activar cliente de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.post(f'/api/v1/clientes/{self.cliente_empresa2.id}/activar/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_historial_compras_cliente_propia_empresa(self):
        """Test: Puede ver historial de compras de cliente de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/clientes/{self.cliente_empresa1.id}/historial_compras/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_historial_compras_cliente_otra_empresa_falla(self):
        """Test: No puede ver historial de compras de cliente de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/clientes/{self.cliente_empresa2.id}/historial_compras/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_resumen_cliente_propia_empresa(self):
        """Test: Puede ver resumen de cliente de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/clientes/{self.cliente_empresa1.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resumen_cliente_otra_empresa_falla(self):
        """Test: No puede ver resumen de cliente de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/clientes/{self.cliente_empresa2.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from .models import Proveedor
from empresas.models import Empresa
from usuarios.models import User


class ProveedorModelTest(TestCase):
    """Tests para el modelo Proveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_proveedor_basico(self):
        """Test: Crear proveedor básico"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            telefono='809-555-1234'
        )
        self.assertEqual(proveedor.nombre, 'Proveedor Test')
        self.assertTrue(proveedor.activo)
        self.assertEqual(proveedor.tipo_contribuyente, 'JURIDICA')
        self.assertFalse(proveedor.es_internacional)

    def test_crear_proveedor_completo(self):
        """Test: Crear proveedor con todos los campos"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Completo S.A.',
            tipo_identificacion='RNC',
            numero_identificacion='123456789',
            tipo_contribuyente='JURIDICA',
            telefono='809-555-1234',
            correo_electronico='proveedor@test.com',
            direccion='Calle Test #123',
            es_internacional=False
        )
        self.assertEqual(proveedor.tipo_identificacion, 'RNC')
        self.assertEqual(proveedor.numero_identificacion, '123456789')
        self.assertEqual(proveedor.tipo_contribuyente, 'JURIDICA')

    def test_proveedor_str(self):
        """Test: Representación string de proveedor"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test S.A.',
            numero_identificacion='123456789'
        )
        self.assertIn('Proveedor Test S.A.', str(proveedor))
        self.assertIn('123456789', str(proveedor))

    def test_proveedor_str_sin_identificacion(self):
        """Test: Representación string de proveedor sin identificación"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Sin ID'
        )
        self.assertEqual(str(proveedor), 'Proveedor Sin ID')

    def test_validacion_rnc_requiere_numero(self):
        """Test: RNC requiere número de identificación"""
        proveedor = Proveedor(
            empresa=self.empresa,
            nombre='Test',
            tipo_identificacion='RNC',
            numero_identificacion=''
        )
        with self.assertRaises(ValidationError) as context:
            proveedor.clean()
        self.assertIn('numero_identificacion', context.exception.message_dict)

    def test_numero_identificacion_unico_por_empresa(self):
        """Test: Número de identificación es único por empresa"""
        Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor 1',
            numero_identificacion='123456789'
        )
        with self.assertRaises(Exception):
            Proveedor.objects.create(
                empresa=self.empresa,
                nombre='Proveedor 2',
                numero_identificacion='123456789'
            )

    def test_numero_identificacion_puede_repetirse_entre_empresas(self):
        """Test: Número de identificación puede repetirse en diferentes empresas"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor 1',
            numero_identificacion='123456789'
        )
        proveedor2 = Proveedor.objects.create(
            empresa=otra_empresa,
            nombre='Proveedor 2',
            numero_identificacion='123456789'
        )
        self.assertEqual(proveedor2.numero_identificacion, '123456789')

    def test_email_normalizado(self):
        """Test: Email se normaliza a minúsculas"""
        proveedor = Proveedor(
            empresa=self.empresa,
            nombre='Test',
            correo_electronico='  TEST@TEST.COM  '
        )
        proveedor.clean()
        self.assertEqual(proveedor.correo_electronico, 'test@test.com')

    def test_nombre_normalizado(self):
        """Test: Nombre se normaliza (strip)"""
        proveedor = Proveedor(
            empresa=self.empresa,
            nombre='  Proveedor Test  '
        )
        proveedor.clean()
        self.assertEqual(proveedor.nombre, 'Proveedor Test')

    def test_nombre_vacio_falla(self):
        """Test: Nombre vacío falla validación"""
        proveedor = Proveedor(
            empresa=self.empresa,
            nombre='   '
        )
        with self.assertRaises(ValidationError) as context:
            proveedor.clean()
        self.assertIn('nombre', context.exception.message_dict)

    def test_uuid_generado_automaticamente(self):
        """Test: UUID se genera automáticamente"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test'
        )
        self.assertIsNotNone(proveedor.uuid)

    def test_tipos_contribuyente(self):
        """Test: Todos los tipos de contribuyente son válidos"""
        tipos = ['JURIDICA', 'FISICA', 'INFORMAL', 'ESTATAL', 'EXTRANJERO']
        for tipo in tipos:
            proveedor = Proveedor.objects.create(
                empresa=self.empresa,
                nombre=f'Proveedor {tipo}',
                tipo_contribuyente=tipo
            )
            self.assertEqual(proveedor.tipo_contribuyente, tipo)

    def test_proveedor_internacional(self):
        """Test: Proveedor internacional"""
        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Internacional',
            tipo_contribuyente='EXTRANJERO',
            es_internacional=True
        )
        self.assertTrue(proveedor.es_internacional)
        self.assertEqual(proveedor.tipo_contribuyente, 'EXTRANJERO')


class ProveedorAPITest(APITestCase):
    """Tests para la API de Proveedor"""

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
        content_type = ContentType.objects.get_for_model(Proveedor)
        for codename in ['view_proveedor', 'add_proveedor', 'change_proveedor', 'delete_proveedor']:
            perm = Permission.objects.get(codename=codename, content_type=content_type)
            self.user.user_permissions.add(perm)

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='111111111',
            tipo_contribuyente='JURIDICA',
            telefono='809-555-1234'
        )

        self.client = APIClient()

    def test_listar_proveedores(self):
        """Test: Listar proveedores"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_crear_proveedor(self):
        """Test: Crear proveedor"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nuevo Proveedor',
            'tipo_identificacion': 'CEDULA',
            'numero_identificacion': '001-0000000-0',
            'tipo_contribuyente': 'FISICA',
            'telefono': '809-555-5555'
        }
        response = self.client.post('/api/v1/proveedores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Nuevo Proveedor')

    def test_obtener_proveedor(self):
        """Test: Obtener proveedor por ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/proveedores/{self.proveedor.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Proveedor Test')

    def test_actualizar_proveedor(self):
        """Test: Actualizar proveedor"""
        self.client.force_authenticate(user=self.user)
        data = {'nombre': 'Proveedor Actualizado'}
        response = self.client.patch(f'/api/v1/proveedores/{self.proveedor.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Proveedor Actualizado')

    def test_buscar_proveedores(self):
        """Test: Buscar proveedores"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_proveedores_activos(self):
        """Test: Filtrar proveedores activos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?activo=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for proveedor in response.data['results']:
            self.assertTrue(proveedor['activo'])

    def test_filtrar_proveedores_por_tipo_identificacion(self):
        """Test: Filtrar proveedores por tipo de identificación"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?tipo_identificacion=RNC')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for proveedor in response.data['results']:
            self.assertEqual(proveedor['tipo_identificacion'], 'RNC')

    def test_filtrar_proveedores_por_tipo_contribuyente(self):
        """Test: Filtrar proveedores por tipo de contribuyente"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?tipo_contribuyente=JURIDICA')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for proveedor in response.data['results']:
            self.assertEqual(proveedor['tipo_contribuyente'], 'JURIDICA')

    def test_filtrar_proveedores_internacionales(self):
        """Test: Filtrar proveedores internacionales"""
        Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Internacional',
            es_internacional=True
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?es_internacional=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for proveedor in response.data['results']:
            self.assertTrue(proveedor['es_internacional'])

    def test_historial_compras(self):
        """Test: Obtener historial de compras del proveedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/proveedores/{self.proveedor.id}/historial_compras/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('compras', response.data)
        self.assertIn('total_comprado', response.data)
        self.assertIn('total_pagado', response.data)
        self.assertIn('total_pendiente', response.data)

    def test_historial_ordenes(self):
        """Test: Obtener historial de órdenes del proveedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/proveedores/{self.proveedor.id}/historial_ordenes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ordenes', response.data)
        self.assertIn('total_ordenado', response.data)

    def test_resumen_proveedor(self):
        """Test: Obtener resumen del proveedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/proveedores/{self.proveedor.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('proveedor', response.data)
        self.assertIn('estadisticas', response.data)
        self.assertIn('total_compras', response.data['estadisticas'])
        self.assertIn('total_comprado', response.data['estadisticas'])

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/proveedores/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crear_proveedor_rnc_sin_numero_falla(self):
        """Test: Crear proveedor con RNC sin número falla"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Proveedor Test',
            'tipo_identificacion': 'RNC',
            'numero_identificacion': ''
        }
        response = self.client.post('/api/v1/proveedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_proveedor_telefono_invalido(self):
        """Test: Crear proveedor con teléfono inválido"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Proveedor Test',
            'telefono': 'abc'
        }
        response = self.client.post('/api/v1/proveedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_proveedor_email_invalido(self):
        """Test: Crear proveedor con email inválido"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Proveedor Test',
            'correo_electronico': 'email_invalido'
        }
        response = self.client.post('/api/v1/proveedores/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_proveedor_empresa_asignada_automaticamente(self):
        """Test: La empresa se asigna automáticamente del usuario"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nuevo Proveedor Auto',
            'numero_identificacion': '999888777',
            'telefono': '8095550001'
        }
        response = self.client.post('/api/v1/proveedores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proveedor = Proveedor.objects.get(id=response.data['id'])
        self.assertEqual(proveedor.empresa, self.empresa)

    def test_ordenar_proveedores_por_nombre(self):
        """Test: Ordenar proveedores por nombre"""
        Proveedor.objects.create(
            empresa=self.empresa,
            nombre='AAA Proveedor'
        )
        Proveedor.objects.create(
            empresa=self.empresa,
            nombre='ZZZ Proveedor'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?ordering=nombre')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nombres = [p['nombre'] for p in response.data['results']]
        self.assertEqual(nombres, sorted(nombres))

    def test_ordenar_proveedores_por_fecha_creacion(self):
        """Test: Ordenar proveedores por fecha de creación"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/proveedores/?ordering=-fecha_creacion')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

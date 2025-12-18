"""
Tests para el módulo de Despachos
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date

from .models import Despacho, DetalleDespacho
from empresas.models import Empresa
from clientes.models import Cliente
from productos.models import Producto
from inventario.models import Almacen
from ventas.models import Factura

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class DespachoModelTest(TestCase):
    """Tests para el modelo Despacho"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.almacen = Almacen.objects.create(
            nombre='Almacen Test',
            empresa=self.empresa
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )
        self.factura = Factura.objects.create(
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('100.00'),
            total=Decimal('118.00'),
            empresa=self.empresa,
            usuario=self.user
        )

    def test_crear_despacho(self):
        """Test: Crear despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            usuario_creacion=self.user
        )
        self.assertIsNotNone(despacho.id)
        self.assertEqual(despacho.estado, 'PENDIENTE')
        self.assertEqual(despacho.cliente, self.cliente)

    def test_despacho_str(self):
        """Test: Representacion string de despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa
        )
        self.assertIn('Despacho', str(despacho))
        self.assertIn(self.factura.numero_factura, str(despacho))

    def test_despacho_estados(self):
        """Test: Cambio de estados de despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa
        )
        self.assertEqual(despacho.estado, 'PENDIENTE')

        despacho.estado = 'EN_PREPARACION'
        despacho.save()
        self.assertEqual(despacho.estado, 'EN_PREPARACION')

        despacho.estado = 'COMPLETADO'
        despacho.save()
        self.assertEqual(despacho.estado, 'COMPLETADO')


class DetalleDespachoModelTest(TestCase):
    """Tests para el modelo DetalleDespacho"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.almacen = Almacen.objects.create(
            nombre='Almacen Test',
            empresa=self.empresa
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )
        self.factura = Factura.objects.create(
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('100.00'),
            total=Decimal('118.00'),
            empresa=self.empresa,
            usuario=self.user
        )
        self.despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa
        )

    def test_crear_detalle(self):
        """Test: Crear detalle de despacho"""
        detalle = DetalleDespacho.objects.create(
            despacho=self.despacho,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            cantidad_despachada=Decimal('5')
        )
        self.assertIsNotNone(detalle.id)
        self.assertEqual(detalle.cantidad_solicitada, Decimal('10'))
        self.assertEqual(detalle.cantidad_despachada, Decimal('5'))

    def test_detalle_str(self):
        """Test: Representacion string de detalle"""
        detalle = DetalleDespacho.objects.create(
            despacho=self.despacho,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            cantidad_despachada=Decimal('5')
        )
        self.assertIn(self.producto.nombre, str(detalle))

    def test_cantidad_sincronizada(self):
        """Test: Cantidad se sincroniza con cantidad_despachada"""
        detalle = DetalleDespacho.objects.create(
            despacho=self.despacho,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            cantidad_despachada=Decimal('8')
        )
        self.assertEqual(detalle.cantidad, Decimal('8'))


# ========== TESTS DE API ==========

class DespachoAPITest(APITestCase):
    """Tests para las APIs de Despacho"""

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

        # Asignar permisos
        for model in [Despacho, DetalleDespacho]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

        self.almacen = Almacen.objects.create(
            nombre='Almacen Principal',
            empresa=self.empresa
        )

        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        self.factura = Factura.objects.create(
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('100.00'),
            total=Decimal('118.00'),
            empresa=self.empresa,
            usuario=self.user
        )

        self.client = APIClient()

    def test_listar_despachos(self):
        """Test: Listar despachos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/despachos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_despacho(self):
        """Test: Crear despacho"""
        self.client.force_authenticate(user=self.user)
        data = {
            'factura': self.factura.id,
            'cliente': self.cliente.id,
            'almacen': self.almacen.id
        }
        response = self.client.post('/api/v1/despachos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['estado'], 'PENDIENTE')

    def test_preparar_despacho(self):
        """Test: Preparar despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='PENDIENTE'
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/preparar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'EN_PREPARACION')

    def test_preparar_despacho_no_pendiente(self):
        """Test: No se puede preparar despacho que no está pendiente"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='EN_PREPARACION'
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/preparar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completar_despacho(self):
        """Test: Completar despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='EN_PREPARACION'
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/completar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'COMPLETADO')

    def test_cancelar_despacho(self):
        """Test: Cancelar despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='PENDIENTE'
        )

        self.client.force_authenticate(user=self.user)
        data = {'observaciones': 'Cancelado por pruebas'}
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/cancelar/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CANCELADO')

    def test_cancelar_despacho_completado(self):
        """Test: No se puede cancelar despacho completado"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='COMPLETADO'
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_despachar_productos(self):
        """Test: Despachar productos"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='PENDIENTE'
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'detalles': [
                {'producto_id': self.producto.id, 'cantidad': 5}
            ],
            'observaciones': 'Despacho de prueba'
        }
        response = self.client.post(f'/api/v1/despachos/{despacho.id}/despachar/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['estado'], ['PARCIAL', 'COMPLETADO'])

    def test_obtener_detalles_despacho(self):
        """Test: Obtener detalles de un despacho"""
        despacho = Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa
        )
        DetalleDespacho.objects.create(
            despacho=despacho,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            cantidad_despachada=Decimal('5')
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/despachos/{despacho.id}/detalles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filtrar_por_estado(self):
        """Test: Filtrar despachos por estado"""
        Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='PENDIENTE'
        )
        Despacho.objects.create(
            factura=self.factura,
            cliente=self.cliente,
            almacen=self.almacen,
            empresa=self.empresa,
            estado='COMPLETADO'
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/despachos/?estado=PENDIENTE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertTrue(all(d['estado'] == 'PENDIENTE' for d in results))

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/despachos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

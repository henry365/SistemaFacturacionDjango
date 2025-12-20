"""
Tests para Cuentas por Cobrar
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from empresas.models import Empresa
from clientes.models import Cliente
from ventas.models import Factura

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class CuentaPorCobrarModelTest(TestCase):
    """Tests para el modelo CuentaPorCobrar"""

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
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('1000.00'),
            total=Decimal('1180.00'),
            usuario=self.user
        )

    def test_crear_cuenta_por_cobrar(self):
        """Test: Crear cuenta por cobrar"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00')
        )
        self.assertIsNotNone(cxc.id)
        self.assertEqual(cxc.estado, 'PENDIENTE')
        self.assertEqual(cxc.monto_pendiente, Decimal('1180.00'))

    def test_cuenta_por_cobrar_str(self):
        """Test: Representacion string de CxC"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00')
        )
        self.assertIn('CxC', str(cxc))
        self.assertIn('FAC-001', str(cxc))

    def test_actualizar_estado_cobrada(self):
        """Test: Actualizar estado a COBRADA"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_cobrado=Decimal('1180.00'),
            monto_pendiente=Decimal('0.00')
        )
        cxc.actualizar_estado()
        self.assertEqual(cxc.estado, 'COBRADA')

    def test_actualizar_estado_parcial(self):
        """Test: Actualizar estado a PARCIAL"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_cobrado=Decimal('500.00'),
            monto_pendiente=Decimal('680.00')
        )
        cxc.actualizar_estado()
        self.assertEqual(cxc.estado, 'PARCIAL')


class CobroClienteModelTest(TestCase):
    """Tests para el modelo CobroCliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

    def test_crear_cobro_cliente(self):
        """Test: Crear cobro de cliente"""
        cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-001',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        self.assertIsNotNone(cobro.id)
        self.assertEqual(cobro.monto, Decimal('500.00'))

    def test_cobro_cliente_str(self):
        """Test: Representacion string de cobro"""
        cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-001',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        self.assertIn('Cobro', str(cobro))
        self.assertIn('REC-001', str(cobro))


class DetalleCobroClienteModelTest(TestCase):
    """Tests para el modelo DetalleCobroCliente"""

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
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('1000.00'),
            total=Decimal('1180.00'),
            usuario=self.user
        )
        self.cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00')
        )
        self.cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-001',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

    def test_crear_detalle_cobro(self):
        """Test: Crear detalle de cobro"""
        detalle = DetalleCobroCliente.objects.create(
            cobro=self.cobro,
            cuenta_por_cobrar=self.cxc,
            monto_aplicado=Decimal('500.00')
        )
        self.assertIsNotNone(detalle.id)
        self.assertEqual(detalle.monto_aplicado, Decimal('500.00'))

    def test_detalle_cobro_str(self):
        """Test: Representacion string de detalle"""
        detalle = DetalleCobroCliente.objects.create(
            cobro=self.cobro,
            cuenta_por_cobrar=self.cxc,
            monto_aplicado=Decimal('500.00')
        )
        self.assertIn('REC-001', str(detalle))
        self.assertIn('FAC-001', str(detalle))


# ========== TESTS DE API ==========

class CuentaPorCobrarAPITest(APITestCase):
    """Tests para las APIs de CuentaPorCobrar"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='contabilidad'
        )

        # Asignar permisos
        for model in [CuentaPorCobrar, CobroCliente, DetalleCobroCliente]:
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

        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('1000.00'),
            total=Decimal('1180.00'),
            usuario=self.user
        )

        self.client = APIClient()

    def test_listar_cuentas_por_cobrar(self):
        """Test: Listar cuentas por cobrar"""
        CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxc/cuentas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_cuenta_por_cobrar(self):
        """Test: Crear cuenta por cobrar via API"""
        factura2 = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-002',
            subtotal=Decimal('1500.00'),
            total=Decimal('1770.00'),
            usuario=self.user
        )
        self.client.force_authenticate(user=self.user)
        data = {
            'cliente': self.cliente.id,
            'factura': factura2.id,
            'numero_documento': 'FAC-002',
            'fecha_documento': date.today().isoformat(),
            'fecha_vencimiento': (date.today() + timedelta(days=30)).isoformat(),
            'monto_original': '1770.00',
            'monto_pendiente': '1770.00'
        }
        response = self.client.post('/api/v1/cxc/cuentas/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_endpoint_pendientes(self):
        """Test: Endpoint de cuentas pendientes"""
        CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00'),
            estado='PENDIENTE'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxc/cuentas/pendientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/cxc/cuentas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CobroClienteAPITest(APITestCase):
    """Tests para las APIs de CobroCliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='contabilidad'
        )

        # Asignar permisos
        for model in [CuentaPorCobrar, CobroCliente, DetalleCobroCliente]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        # Hacer al usuario staff para evitar problemas con permisos personalizados
        self.user.is_staff = True
        self.user.save()

        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('1000.00'),
            total=Decimal('1180.00'),
            usuario=self.user
        )

        self.cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1180.00'),
            monto_pendiente=Decimal('1180.00')
        )

        self.client = APIClient()

    def test_listar_cobros_clientes(self):
        """Test: Listar cobros de clientes"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxc/cobros/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_cobro_cliente(self):
        """Test: Crear cobro de cliente via API"""
        self.client.force_authenticate(user=self.user)
        data = {
            'cliente': self.cliente.id,
            'numero_recibo': 'REC-001',
            'fecha_cobro': date.today().isoformat(),
            'monto': '500.00',
            'metodo_pago': 'EFECTIVO'
        }
        response = self.client.post('/api/v1/cxc/cobros/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_aplicar_cobro(self):
        """Test: Aplicar cobro a cuentas por cobrar"""
        cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-002',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'detalles': [
                {'cuenta_por_cobrar_id': self.cxc.id, 'monto_aplicado': '500.00'}
            ]
        }
        response = self.client.post(f'/api/v1/cxc/cobros/{cobro.id}/aplicar/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que se actualizo la CxC
        self.cxc.refresh_from_db()
        self.assertEqual(self.cxc.monto_cobrado, Decimal('500.00'))
        self.assertEqual(self.cxc.monto_pendiente, Decimal('680.00'))
        self.assertEqual(self.cxc.estado, 'PARCIAL')

    def test_aplicar_cobro_excede_monto(self):
        """Test: Aplicar cobro que excede el monto del cobro"""
        cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-003',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'detalles': [
                {'cuenta_por_cobrar_id': self.cxc.id, 'monto_aplicado': '600.00'}
            ]
        }
        response = self.client.post(f'/api/v1/cxc/cobros/{cobro.id}/aplicar/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/cxc/cobros/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

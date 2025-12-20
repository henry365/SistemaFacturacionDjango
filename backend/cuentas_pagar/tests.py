"""
Tests para Cuentas por Pagar
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from empresas.models import Empresa
from proveedores.models import Proveedor
from compras.models import Compra

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class CuentaPorPagarModelTest(TestCase):
    """Tests para el modelo CuentaPorPagar"""

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
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PROV-001',
            total=Decimal('1000.00')
        )

    def test_crear_cuenta_por_pagar(self):
        """Test: Crear cuenta por pagar"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00')
        )
        self.assertIsNotNone(cxp.id)
        self.assertEqual(cxp.estado, 'PENDIENTE')
        self.assertEqual(cxp.monto_pendiente, Decimal('1000.00'))

    def test_cuenta_por_pagar_str(self):
        """Test: Representacion string de CxP"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00')
        )
        self.assertIn('CxP', str(cxp))
        self.assertIn('FAC-PROV-001', str(cxp))

    def test_actualizar_estado_pagada(self):
        """Test: Actualizar estado a PAGADA"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('1000.00'),
            monto_pendiente=Decimal('0.00')
        )
        cxp.actualizar_estado()
        self.assertEqual(cxp.estado, 'PAGADA')

    def test_actualizar_estado_parcial(self):
        """Test: Actualizar estado a PARCIAL"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('500.00'),
            monto_pendiente=Decimal('500.00')
        )
        cxp.actualizar_estado()
        self.assertEqual(cxp.estado, 'PARCIAL')


class PagoProveedorModelTest(TestCase):
    """Tests para el modelo PagoProveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

    def test_crear_pago_proveedor(self):
        """Test: Crear pago a proveedor"""
        pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-001',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        self.assertIsNotNone(pago.id)
        self.assertEqual(pago.monto, Decimal('500.00'))

    def test_pago_proveedor_str(self):
        """Test: Representacion string de pago"""
        pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-001',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        self.assertIn('Pago', str(pago))
        self.assertIn('PAG-001', str(pago))


class DetallePagoProveedorModelTest(TestCase):
    """Tests para el modelo DetallePagoProveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PROV-001',
            total=Decimal('1000.00')
        )
        self.cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00')
        )
        self.pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-001',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

    def test_crear_detalle_pago(self):
        """Test: Crear detalle de pago"""
        detalle = DetallePagoProveedor.objects.create(
            pago=self.pago,
            cuenta_por_pagar=self.cxp,
            monto_aplicado=Decimal('500.00')
        )
        self.assertIsNotNone(detalle.id)
        self.assertEqual(detalle.monto_aplicado, Decimal('500.00'))

    def test_detalle_pago_str(self):
        """Test: Representacion string de detalle"""
        detalle = DetallePagoProveedor.objects.create(
            pago=self.pago,
            cuenta_por_pagar=self.cxp,
            monto_aplicado=Decimal('500.00')
        )
        self.assertIn('PAG-001', str(detalle))
        self.assertIn('FAC-PROV-001', str(detalle))


# ========== TESTS DE API ==========

class CuentaPorPagarAPITest(APITestCase):
    """Tests para las APIs de CuentaPorPagar"""

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
        for model in [CuentaPorPagar, PagoProveedor, DetallePagoProveedor]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PROV-001',
            total=Decimal('1000.00')
        )

        self.client = APIClient()

    def test_listar_cuentas_por_pagar(self):
        """Test: Listar cuentas por pagar"""
        CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxp/cuentas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_cuenta_por_pagar(self):
        """Test: Crear cuenta por pagar via API"""
        self.client.force_authenticate(user=self.user)
        data = {
            'proveedor': self.proveedor.id,
            'compra': self.compra.id,
            'numero_documento': 'FAC-PROV-002',
            'fecha_documento': date.today().isoformat(),
            'fecha_vencimiento': (date.today() + timedelta(days=30)).isoformat(),
            'monto_original': '1500.00',
            'monto_pendiente': '1500.00'
        }
        response = self.client.post('/api/v1/cxp/cuentas/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_endpoint_pendientes(self):
        """Test: Endpoint de cuentas pendientes"""
        CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00'),
            estado='PENDIENTE'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxp/cuentas/pendientes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/cxp/cuentas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PagoProveedorAPITest(APITestCase):
    """Tests para las APIs de PagoProveedor"""

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
        for model in [CuentaPorPagar, PagoProveedor, DetallePagoProveedor]:
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

        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )

        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PROV-001',
            total=Decimal('1000.00')
        )

        self.cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PROV-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pendiente=Decimal('1000.00')
        )

        self.client = APIClient()

    def test_listar_pagos_proveedores(self):
        """Test: Listar pagos a proveedores"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/cxp/pagos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_pago_proveedor(self):
        """Test: Crear pago a proveedor via API"""
        self.client.force_authenticate(user=self.user)
        data = {
            'proveedor': self.proveedor.id,
            'numero_pago': 'PAG-001',
            'fecha_pago': date.today().isoformat(),
            'monto': '500.00',
            'metodo_pago': 'EFECTIVO'
        }
        response = self.client.post('/api/v1/cxp/pagos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_aplicar_pago(self):
        """Test: Aplicar pago a cuentas por pagar"""
        pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-002',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'detalles': [
                {'cuenta_por_pagar_id': self.cxp.id, 'monto_aplicado': '500.00'}
            ]
        }
        response = self.client.post(f'/api/v1/cxp/pagos/{pago.id}/aplicar/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que se actualizo la CxP
        self.cxp.refresh_from_db()
        self.assertEqual(self.cxp.monto_pagado, Decimal('500.00'))
        self.assertEqual(self.cxp.monto_pendiente, Decimal('500.00'))
        self.assertEqual(self.cxp.estado, 'PARCIAL')

    def test_aplicar_pago_excede_monto(self):
        """Test: Aplicar pago que excede el monto del pago"""
        pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-003',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'detalles': [
                {'cuenta_por_pagar_id': self.cxp.id, 'monto_aplicado': '600.00'}
            ]
        }
        response = self.client.post(f'/api/v1/cxp/pagos/{pago.id}/aplicar/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/cxp/pagos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

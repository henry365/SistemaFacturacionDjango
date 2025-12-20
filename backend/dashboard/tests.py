"""
Tests para el módulo de Dashboard.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import timedelta, date

from empresas.models import Empresa
from usuarios.models import User
from clientes.models import Cliente
from proveedores.models import Proveedor
from productos.models import Producto
from ventas.models import Factura, DetalleFactura
from compras.models import Compra
from cuentas_cobrar.models import CuentaPorCobrar
from cuentas_pagar.models import CuentaPorPagar
from inventario.models import Almacen, InventarioProducto, AlertaInventario


class DashboardAPITest(APITestCase):
    """Tests para la API del Dashboard"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        # Crear usuario admin
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            empresa=self.empresa
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            limite_credito=Decimal('100000.00')  # Permite ventas a crédito
        )

        # Crear proveedor
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='111222333'
        )

        # Crear producto
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        # Crear almacén
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal'
        )

        # Crear inventario con stock bajo
        self.inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('5.00'),
            stock_minimo=Decimal('10.00'),
            stock_maximo=Decimal('100.00'),
            costo_promedio=Decimal('50.00')
        )

        # Crear factura de hoy (para ventas)
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            subtotal=Decimal('1000.00'),
            itbis=Decimal('180.00'),
            total=Decimal('1180.00'),
            estado='PAGADA',
            tipo_venta='CONTADO',
            usuario=self.user
        )

        # Crear factura adicional para CxC (separada porque es OneToOne)
        self.factura_credito = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-002',
            subtotal=Decimal('5000.00'),
            total=Decimal('5000.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CREDITO',
            usuario=self.user
        )

        # Crear cuenta por cobrar vencida (requiere factura)
        self.cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura_credito,
            numero_documento='CXC-001',
            monto_original=Decimal('5000.00'),
            monto_pendiente=Decimal('5000.00'),
            fecha_documento=timezone.now().date() - timedelta(days=60),
            fecha_vencimiento=timezone.now().date() - timedelta(days=30),
            estado='VENCIDA'
        )

        # Crear compra para CxP
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today() - timedelta(days=30),
            numero_factura_proveedor='FAC-PROV-001',
            total=Decimal('3000.00'),
            estado='CXP'
        )

        # Crear cuenta por pagar (requiere compra)
        self.cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='CXP-001',
            monto_original=Decimal('3000.00'),
            monto_pendiente=Decimal('3000.00'),
            fecha_documento=timezone.now().date() - timedelta(days=30),
            fecha_vencimiento=timezone.now().date() - timedelta(days=5),
            estado='VENCIDA'
        )

        # Crear alerta de inventario (usa inventario FK, no producto/almacen)
        self.alerta = AlertaInventario.objects.create(
            empresa=self.empresa,
            inventario=self.inventario,
            tipo='STOCK_BAJO',
            mensaje='Stock bajo para Producto Test',
            prioridad='ALTA',
            resuelta=False
        )

        self.client = APIClient()

    def test_resumen_sin_autenticacion(self):
        """Test: Endpoint resumen requiere autenticación"""
        response = self.client.get('/api/v1/dashboard/resumen/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_resumen_completo(self):
        """Test: Endpoint resumen retorna todas las métricas"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/resumen/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura de respuesta
        self.assertIn('fecha', response.data)
        self.assertIn('ventas', response.data)
        self.assertIn('cuentas_por_cobrar', response.data)
        self.assertIn('cuentas_por_pagar', response.data)
        self.assertIn('inventario', response.data)

        # Verificar CxC vencidas
        self.assertEqual(response.data['cuentas_por_cobrar']['vencidas_cantidad'], 1)
        self.assertIn(response.data['cuentas_por_cobrar']['vencidas_total'], ['5000', '5000.00'])

        # Verificar CxP vencidas
        self.assertEqual(response.data['cuentas_por_pagar']['vencidas_cantidad'], 1)
        self.assertIn(response.data['cuentas_por_pagar']['vencidas_total'], ['3000', '3000.00'])

        # Verificar alertas de inventario
        self.assertEqual(response.data['inventario']['alertas_total'], 1)

    def test_ventas_periodo(self):
        """Test: Endpoint ventas_periodo retorna datos de ventas"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/ventas_periodo/?dias=30')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('periodo_dias', response.data)
        self.assertIn('datos', response.data)
        self.assertEqual(response.data['periodo_dias'], 30)

    def test_ventas_por_mes(self):
        """Test: Endpoint ventas_por_mes retorna datos mensuales"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/ventas_por_mes/?meses=6')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('periodo_meses', response.data)
        self.assertIn('datos', response.data)

    def test_top_productos(self):
        """Test: Endpoint top_productos retorna productos más vendidos"""
        # Crear detalle de factura
        DetalleFactura.objects.create(
            factura=self.factura,
            producto=self.producto,
            cantidad=Decimal('10.00'),
            precio_unitario=Decimal('100.00'),
            importe=Decimal('1000.00')
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/top_productos/?limite=5&dias=30')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('productos', response.data)

    def test_productos_stock_bajo(self):
        """Test: Endpoint productos_stock_bajo retorna productos con déficit"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/productos_stock_bajo/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('productos', response.data)

        # Debe encontrar el producto con stock bajo
        self.assertGreaterEqual(len(response.data['productos']), 1)
        if response.data['productos']:
            self.assertEqual(response.data['productos'][0]['codigo_sku'], 'PROD-001')

    def test_top_clientes(self):
        """Test: Endpoint top_clientes retorna clientes con más compras"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/top_clientes/?limite=5&dias=90')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('clientes', response.data)

    def test_cuentas_por_cobrar_detalle(self):
        """Test: Endpoint cuentas_por_cobrar retorna detalle de CxC"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/cuentas_por_cobrar/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumen_por_estado', response.data)
        self.assertIn('por_vencer', response.data)
        self.assertIn('vencidas_por_antiguedad', response.data)

    def test_cuentas_por_pagar_detalle(self):
        """Test: Endpoint cuentas_por_pagar retorna detalle de CxP"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/cuentas_por_pagar/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumen_por_estado', response.data)
        self.assertIn('por_vencer', response.data)

    def test_actividad_reciente(self):
        """Test: Endpoint actividad_reciente retorna últimas actividades"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/actividad_reciente/?limite=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actividades', response.data)
        self.assertIn('total', response.data)

    def test_indicadores_financieros(self):
        """Test: Endpoint indicadores_financieros retorna KPIs"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dashboard/indicadores_financieros/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('periodo', response.data)
        self.assertIn('ventas', response.data)
        self.assertIn('compras', response.data)
        self.assertIn('cuentas', response.data)
        self.assertIn('inventario', response.data)


class DashboardMultiEmpresaTest(APITestCase):
    """Tests para verificar aislamiento multi-tenant"""

    def setUp(self):
        """Configuración con múltiples empresas"""
        # Empresa 1
        self.empresa1 = Empresa.objects.create(
            nombre='Empresa 1',
            rnc='111111111'
        )
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123',
            empresa=self.empresa1,
            rol='admin'
        )
        self.cliente1 = Cliente.objects.create(
            empresa=self.empresa1,
            nombre='Cliente Empresa 1',
            tipo_identificacion='RNC',
            numero_identificacion='111000111',
            limite_credito=Decimal('100000.00')
        )

        # Empresa 2
        self.empresa2 = Empresa.objects.create(
            nombre='Empresa 2',
            rnc='222222222'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123',
            empresa=self.empresa2,
            rol='admin'
        )
        self.cliente2 = Cliente.objects.create(
            empresa=self.empresa2,
            nombre='Cliente Empresa 2',
            tipo_identificacion='RNC',
            numero_identificacion='222000222',
            limite_credito=Decimal('100000.00')
        )

        # Crear CxC para empresa 1 (no ventas del día porque fecha es auto_now_add)
        self.factura1 = Factura.objects.create(
            empresa=self.empresa1,
            cliente=self.cliente1,
            numero_factura='E1-FAC-001',
            subtotal=Decimal('5000.00'),
            total=Decimal('5000.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CREDITO',
            usuario=self.user1
        )
        self.cxc1 = CuentaPorCobrar.objects.create(
            empresa=self.empresa1,
            cliente=self.cliente1,
            factura=self.factura1,
            numero_documento='E1-CXC-001',
            monto_original=Decimal('5000.00'),
            monto_pendiente=Decimal('5000.00'),
            fecha_documento=date.today() - timedelta(days=60),
            fecha_vencimiento=date.today() - timedelta(days=30),
            estado='VENCIDA'
        )

        # Crear CxC para empresa 2
        self.factura2 = Factura.objects.create(
            empresa=self.empresa2,
            cliente=self.cliente2,
            numero_factura='E2-FAC-001',
            subtotal=Decimal('10000.00'),
            total=Decimal('10000.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CREDITO',
            usuario=self.user2
        )
        self.cxc2 = CuentaPorCobrar.objects.create(
            empresa=self.empresa2,
            cliente=self.cliente2,
            factura=self.factura2,
            numero_documento='E2-CXC-001',
            monto_original=Decimal('10000.00'),
            monto_pendiente=Decimal('10000.00'),
            fecha_documento=date.today() - timedelta(days=60),
            fecha_vencimiento=date.today() - timedelta(days=30),
            estado='VENCIDA'
        )

        self.client = APIClient()

    def test_usuario_solo_ve_cxc_su_empresa(self):
        """Test: Usuario de empresa 1 no ve CxC de empresa 2"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/v1/dashboard/resumen/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Usuario 1 debe ver solo CxC de su empresa ($5,000)
        self.assertIn(response.data['cuentas_por_cobrar']['vencidas_total'], ['5000', '5000.00'])
        self.assertEqual(response.data['cuentas_por_cobrar']['vencidas_cantidad'], 1)

    def test_usuario2_solo_ve_cxc_su_empresa(self):
        """Test: Usuario de empresa 2 no ve CxC de empresa 1"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/v1/dashboard/resumen/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Usuario 2 debe ver solo CxC de su empresa ($10,000)
        self.assertIn(response.data['cuentas_por_cobrar']['vencidas_total'], ['10000', '10000.00'])
        self.assertEqual(response.data['cuentas_por_cobrar']['vencidas_cantidad'], 1)

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from .models import (
    CotizacionCliente, DetalleCotizacion, ListaEsperaProducto,
    Factura, DetalleFactura, PagoCaja,
    NotaCredito, NotaDebito, DevolucionVenta, DetalleDevolucion
)
from empresas.models import Empresa
from clientes.models import Cliente
from productos.models import Producto
from vendedores.models import Vendedor
from usuarios.models import User


class CotizacionClienteModelTest(TestCase):
    """Tests para el modelo CotizacionCliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.vendedor = Vendedor.objects.create(
            empresa=self.empresa,
            nombre='Vendedor Test'
        )
        self.user = User.objects.create_user(
            username='testuser_cotizacion',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_cotizacion(self):
        """Test: Crear cotización"""
        cotizacion = CotizacionCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.vendedor,
            vigencia=date.today() + timedelta(days=30),
            total=Decimal('5000.00'),
            usuario=self.user
        )
        self.assertEqual(cotizacion.estado, 'PENDIENTE')

    def test_cotizacion_str(self):
        """Test: Representación string de cotización"""
        cotizacion = CotizacionCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vigencia=date.today() + timedelta(days=30),
            usuario=self.user
        )
        self.assertIn('Cliente Test', str(cotizacion))

    def test_validacion_cliente_misma_empresa(self):
        """Test: Cliente debe ser de la misma empresa"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        cliente_otro = Cliente.objects.create(
            empresa=otra_empresa,
            nombre='Otro Cliente',
            telefono='8095559999'
        )
        cotizacion = CotizacionCliente(
            empresa=self.empresa,
            cliente=cliente_otro,
            vigencia=date.today() + timedelta(days=30)
        )
        with self.assertRaises(ValidationError) as context:
            cotizacion.clean()
        self.assertIn('cliente', context.exception.message_dict)

    def test_validacion_total_negativo(self):
        """Test: Total negativo falla validación"""
        cotizacion = CotizacionCliente(
            empresa=self.empresa,
            cliente=self.cliente,
            vigencia=date.today() + timedelta(days=30),
            total=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            cotizacion.clean()
        self.assertIn('total', context.exception.message_dict)


class FacturaModelTest(TestCase):
    """Tests para el modelo Factura"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234',
            limite_credito=Decimal('50000.00')
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_factura(self):
        """Test: Crear factura"""
        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('5000.00'),
            monto_pendiente=Decimal('5000.00'),
            usuario=self.user
        )
        self.assertEqual(factura.estado, 'PENDIENTE_PAGO')
        self.assertEqual(factura.tipo_venta, 'CONTADO')

    def test_factura_str(self):
        """Test: Representación string de factura"""
        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('5000.00'),
            usuario=self.user
        )
        self.assertIn('FAC-001', str(factura))
        self.assertIn('Cliente Test', str(factura))

    def test_validacion_monto_pendiente_mayor_total(self):
        """Test: Monto pendiente mayor que total falla"""
        factura = Factura(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('5000.00'),
            monto_pendiente=Decimal('6000.00'),
            usuario=self.user
        )
        with self.assertRaises(ValidationError) as context:
            factura.clean()
        self.assertIn('monto_pendiente', context.exception.message_dict)

    def test_validacion_limite_credito(self):
        """Test: Venta a crédito excede límite"""
        factura = Factura(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            tipo_venta='CREDITO',
            total=Decimal('60000.00'),  # Excede límite de 50000
            usuario=self.user
        )
        with self.assertRaises(ValidationError) as context:
            factura.clean()
        self.assertIn('total', context.exception.message_dict)

    def test_factura_contado(self):
        """Test: Factura de contado"""
        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-002',
            tipo_venta='CONTADO',
            total=Decimal('10000.00'),
            usuario=self.user
        )
        self.assertEqual(factura.tipo_venta, 'CONTADO')

    def test_factura_credito(self):
        """Test: Factura a crédito"""
        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-003',
            tipo_venta='CREDITO',
            total=Decimal('10000.00'),
            usuario=self.user
        )
        self.assertEqual(factura.tipo_venta, 'CREDITO')


class PagoCajaModelTest(TestCase):
    """Tests para el modelo PagoCaja"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_pago(self):
        """Test: Crear pago en caja"""
        pago = PagoCaja.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('5000.00'),
            metodo_pago='EFECTIVO',
            usuario=self.user
        )
        self.assertEqual(pago.metodo_pago, 'EFECTIVO')

    def test_pago_str(self):
        """Test: Representación string de pago"""
        pago = PagoCaja.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('5000.00'),
            metodo_pago='EFECTIVO',
            usuario=self.user
        )
        self.assertIn('Cliente Test', str(pago))
        self.assertIn('Efectivo', str(pago))

    def test_validacion_monto_cero(self):
        """Test: Monto cero falla validación"""
        pago = PagoCaja(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('0'),
            metodo_pago='EFECTIVO',
            usuario=self.user
        )
        with self.assertRaises(ValidationError) as context:
            pago.clean()
        self.assertIn('monto', context.exception.message_dict)

    def test_metodos_pago(self):
        """Test: Todos los métodos de pago"""
        metodos = ['EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'CHEQUE', 'OTRO']
        for metodo in metodos:
            pago = PagoCaja.objects.create(
                empresa=self.empresa,
                cliente=self.cliente,
                monto=Decimal('1000.00'),
                metodo_pago=metodo,
                usuario=self.user
            )
            self.assertEqual(pago.metodo_pago, metodo)


class NotaCreditoModelTest(TestCase):
    """Tests para el modelo NotaCredito"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_nota_credito(self):
        """Test: Crear nota de crédito"""
        nc = NotaCredito.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('1000.00'),
            motivo='Devolución de producto defectuoso',
            usuario=self.user
        )
        self.assertFalse(nc.aplicada)

    def test_nota_credito_str(self):
        """Test: Representación string de nota de crédito"""
        nc = NotaCredito.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('1000.00'),
            motivo='Test',
            usuario=self.user
        )
        self.assertIn('Cliente Test', str(nc))

    def test_validacion_monto_cero(self):
        """Test: Monto cero falla validación"""
        nc = NotaCredito(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('0'),
            motivo='Test',
            usuario=self.user
        )
        with self.assertRaises(ValidationError) as context:
            nc.clean()
        self.assertIn('monto', context.exception.message_dict)


class NotaDebitoModelTest(TestCase):
    """Tests para el modelo NotaDebito"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_nota_debito(self):
        """Test: Crear nota de débito"""
        nd = NotaDebito.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('500.00'),
            motivo='Cargo adicional por envío',
            usuario=self.user
        )
        self.assertIsNotNone(nd.id)

    def test_nota_debito_str(self):
        """Test: Representación string de nota de débito"""
        nd = NotaDebito.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            monto=Decimal('500.00'),
            motivo='Test',
            usuario=self.user
        )
        self.assertIn('Cliente Test', str(nd))


class DevolucionVentaModelTest(TestCase):
    """Tests para el modelo DevolucionVenta"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('5000.00'),
            usuario=self.user
        )

    def test_crear_devolucion(self):
        """Test: Crear devolución de venta"""
        devolucion = DevolucionVenta.objects.create(
            empresa=self.empresa,
            factura=self.factura,
            cliente=self.cliente,
            motivo='Producto defectuoso',
            usuario=self.user
        )
        self.assertIsNotNone(devolucion.id)

    def test_devolucion_str(self):
        """Test: Representación string de devolución"""
        devolucion = DevolucionVenta.objects.create(
            empresa=self.empresa,
            factura=self.factura,
            cliente=self.cliente,
            motivo='Test',
            usuario=self.user
        )
        self.assertIn('FAC-001', str(devolucion))


class VentasAPITest(APITestCase):
    """Tests para las APIs de Ventas"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='facturador'
        )

        # Asignar permisos estándar
        for model in [CotizacionCliente, Factura, PagoCaja, NotaCredito, NotaDebito, DevolucionVenta, ListaEsperaProducto]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        # Asignar permisos personalizados de gestión
        permisos_custom = [
            ('ventas', 'cotizacioncliente', 'gestionar_cotizacion'),
            ('ventas', 'factura', 'gestionar_factura'),
            ('ventas', 'pagocaja', 'gestionar_pago_caja'),
            ('ventas', 'notacredito', 'gestionar_nota_credito'),
            ('ventas', 'notadebito', 'gestionar_nota_debito'),
            ('ventas', 'devolucionventa', 'gestionar_devolucion_venta'),
            ('ventas', 'listaesperaproducto', 'gestionar_lista_espera'),
        ]
        for app_label, model_name, codename in permisos_custom:
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                perm = Permission.objects.get(codename=codename, content_type=content_type)
                self.user.user_permissions.add(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234',
            limite_credito=Decimal('50000.00')
        )

        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('5000.00'),
            monto_pendiente=Decimal('5000.00'),
            usuario=self.user
        )

        self.client = APIClient()

    def test_listar_facturas(self):
        """Test: Listar facturas"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/facturas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_obtener_factura(self):
        """Test: Obtener factura por ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/ventas/facturas/{self.factura.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['numero_factura'], 'FAC-001')

    def test_filtrar_facturas_por_estado(self):
        """Test: Filtrar facturas por estado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/facturas/?estado=PENDIENTE_PAGO')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_facturas_por_cliente(self):
        """Test: Filtrar facturas por cliente"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/ventas/facturas/?cliente={self.cliente.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_cotizaciones(self):
        """Test: Listar cotizaciones"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/cotizaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_pagos(self):
        """Test: Listar pagos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/pagos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_notas_credito(self):
        """Test: Listar notas de crédito"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/notas-credito/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_notas_debito(self):
        """Test: Listar notas de débito"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/notas-debito/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_devoluciones(self):
        """Test: Listar devoluciones"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/ventas/devoluciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/ventas/facturas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ListaEsperaModelTest(TestCase):
    """Tests para el modelo ListaEsperaProducto"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            telefono='8095551234'
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )
        self.user = User.objects.create_user(
            username='testuser_lista',
            password='test123',
            empresa=self.empresa
        )

    def test_crear_lista_espera(self):
        """Test: Crear entrada en lista de espera"""
        lista = ListaEsperaProducto.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            usuario=self.user
        )
        self.assertEqual(lista.estado, 'PENDIENTE')
        self.assertEqual(lista.prioridad, 'NORMAL')

    def test_lista_espera_str(self):
        """Test: Representación string de lista de espera"""
        lista = ListaEsperaProducto.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            producto=self.producto,
            cantidad_solicitada=Decimal('10'),
            usuario=self.user
        )
        self.assertIn('Cliente Test', str(lista))
        self.assertIn('Producto Test', str(lista))

    def test_validacion_cantidad_cero(self):
        """Test: Cantidad cero falla validación"""
        lista = ListaEsperaProducto(
            empresa=self.empresa,
            cliente=self.cliente,
            producto=self.producto,
            cantidad_solicitada=Decimal('0')
        )
        with self.assertRaises(ValidationError) as context:
            lista.clean()
        self.assertIn('cantidad_solicitada', context.exception.message_dict)

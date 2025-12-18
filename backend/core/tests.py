"""
Tests para Django 6.0 Features - Background Tasks y Notificaciones

Estos tests verifican el funcionamiento de las tareas background y el
sistema de notificaciones por email implementados con Django Tasks.
"""
from django.test import TestCase, override_settings
from django.core import mail
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from empresas.models import Empresa


class EmailNotificationTaskTest(TestCase):
    """Tests para la tarea enviar_email_notificacion"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_enviar_email_texto_plano(self):
        """Test: Enviar email en texto plano"""
        from core.tasks import enviar_email_notificacion

        result = enviar_email_notificacion.call(
            destinatario='test@example.com',
            asunto='Test Subject',
            mensaje='Test message content'
        )

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_enviar_email_html(self):
        """Test: Enviar email con contenido HTML"""
        from core.tasks import enviar_email_notificacion

        result = enviar_email_notificacion.call(
            destinatario='test@example.com',
            asunto='Test HTML Subject',
            mensaje='Texto plano',
            mensaje_html='<html><body><h1>Test HTML</h1></body></html>'
        )

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(len(mail.outbox), 1)
        # Verificar que tiene alternativas HTML
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertEqual(mail.outbox[0].alternatives[0][1], 'text/html')


class NotificarFacturaCreadaTest(TestCase):
    """Tests para la tarea notificar_factura_creada"""

    def setUp(self):
        from clientes.models import Cliente
        from ventas.models import Factura
        from django.contrib.auth import get_user_model

        User = get_user_model()

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
            empresa=self.empresa,
            nombre='Cliente Test',
            email='cliente@test.com',
            tipo_identificacion='RNC',
            numero_identificacion='987654321'
        )

        self.cliente_sin_email = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Sin Email',
            tipo_identificacion='RNC',
            numero_identificacion='111222333'
        )

        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('1000.00'),
            itbis=Decimal('180.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CONTADO',
            usuario=self.user
        )

        self.factura_sin_email = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente_sin_email,
            numero_factura='FAC-002',
            total=Decimal('500.00'),
            itbis=Decimal('90.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CONTADO',
            usuario=self.user
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_notificar_factura_creada_exitoso(self):
        """Test: Notificar factura creada exitosamente"""
        from core.tasks import notificar_factura_creada

        result = notificar_factura_creada.call(factura_id=self.factura.id)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('FAC-001', mail.outbox[0].subject)

    def test_notificar_factura_cliente_sin_email(self):
        """Test: Notificar factura con cliente sin email"""
        from core.tasks import notificar_factura_creada

        result = notificar_factura_creada.call(factura_id=self.factura_sin_email.id)

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'Cliente sin email')

    def test_notificar_factura_inexistente(self):
        """Test: Notificar factura que no existe"""
        from core.tasks import notificar_factura_creada

        result = notificar_factura_creada.call(factura_id=99999)

        self.assertEqual(result['status'], 'error')
        self.assertIn('no encontrada', result['error'])


class NotificarCxCVencidaTest(TestCase):
    """Tests para la tarea notificar_cxc_vencida"""

    def setUp(self):
        from clientes.models import Cliente
        from ventas.models import Factura
        from cuentas_cobrar.models import CuentaPorCobrar
        from django.contrib.auth import get_user_model

        User = get_user_model()

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
            empresa=self.empresa,
            nombre='Cliente Test',
            email='cliente@test.com',
            tipo_identificacion='RNC',
            numero_identificacion='987654321'
        )

        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_factura='FAC-001',
            total=Decimal('1000.00'),
            itbis=Decimal('180.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CREDITO',
            usuario=self.user
        )

        self.cuenta = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('0.00'),
            fecha_vencimiento=date.today() - timedelta(days=30)
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_notificar_cxc_vencida_exitoso(self):
        """Test: Notificar CxC vencida exitosamente"""
        from core.tasks import notificar_cxc_vencida

        result = notificar_cxc_vencida.call(cuenta_id=self.cuenta.id)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('vencida', mail.outbox[0].subject.lower())

    def test_notificar_cxc_inexistente(self):
        """Test: Notificar CxC que no existe"""
        from core.tasks import notificar_cxc_vencida

        result = notificar_cxc_vencida.call(cuenta_id=99999)

        self.assertEqual(result['status'], 'error')
        self.assertIn('no encontrada', result['error'])


class DGIIReportTaskTest(TestCase):
    """Tests para las tareas de reportes DGII"""

    def setUp(self):
        from proveedores.models import Proveedor
        from compras.models import Compra

        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111222333'
        )

        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PROV-001',
            numero_ncf='B0100000001',
            tipo_gasto='02',
            total=Decimal('5000.00'),
            impuestos=Decimal('900.00'),
            estado='REGISTRADA'
        )

    def test_generar_reporte_606(self):
        """Test: Generar reporte 606"""
        from dgii.tasks import generar_reporte_606

        mes = date.today().month
        anio = date.today().year

        result = generar_reporte_606.call(
            empresa_id=self.empresa.id,
            anio=anio,
            mes=mes
        )

        self.assertEqual(result['status'], 'completed')
        self.assertIn('registros', result)
        self.assertEqual(result['registros'], 1)

    def test_generar_reporte_606_sin_datos(self):
        """Test: Generar reporte 606 sin datos"""
        from dgii.tasks import generar_reporte_606

        result = generar_reporte_606.call(
            empresa_id=self.empresa.id,
            anio=2020,
            mes=1
        )

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['registros'], 0)


class GeneratedFieldTest(TestCase):
    """Tests para verificar que los GeneratedField funcionan correctamente"""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa
        )

    def test_cuentaporcobrar_monto_pendiente(self):
        """Test: CuentaPorCobrar.monto_pendiente es GeneratedField"""
        from clientes.models import Cliente
        from ventas.models import Factura
        from cuentas_cobrar.models import CuentaPorCobrar

        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321'
        )

        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            numero_factura='FAC-001',
            total=Decimal('1000.00'),
            itbis=Decimal('180.00'),
            estado='PENDIENTE_PAGO',
            tipo_venta='CREDITO',
            usuario=self.user
        )

        cuenta = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            factura=factura,
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('300.00'),
            fecha_vencimiento=date.today() + timedelta(days=30)
        )

        # Refrescar desde la base de datos
        cuenta.refresh_from_db()

        # Verificar que monto_pendiente se calcula correctamente
        self.assertEqual(cuenta.monto_pendiente, Decimal('700.00'))

    def test_cuentaporpagar_monto_pendiente(self):
        """Test: CuentaPorPagar.monto_pendiente es GeneratedField"""
        from proveedores.models import Proveedor
        from compras.models import Compra
        from cuentas_pagar.models import CuentaPorPagar

        proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111222333'
        )

        compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00'),
            impuestos=Decimal('900.00'),
            estado='CXP'
        )

        cuenta = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=proveedor,
            compra=compra,
            monto_original=Decimal('5000.00'),
            monto_pagado=Decimal('2000.00'),
            fecha_vencimiento=date.today() + timedelta(days=30)
        )

        # Refrescar desde la base de datos
        cuenta.refresh_from_db()

        # Verificar que monto_pendiente se calcula correctamente
        self.assertEqual(cuenta.monto_pendiente, Decimal('3000.00'))

    def test_inventario_valor_inventario(self):
        """Test: InventarioProducto.valor_inventario es GeneratedField"""
        from productos.models import Producto
        from inventario.models import Almacen, InventarioProducto

        producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacen Principal',
            codigo='ALM-001'
        )

        inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=producto,
            almacen=almacen,
            cantidad_disponible=Decimal('50.00'),
            costo_promedio=Decimal('75.00')
        )

        # Refrescar desde la base de datos
        inventario.refresh_from_db()

        # Verificar que valor_inventario se calcula correctamente
        self.assertEqual(inventario.valor_inventario, Decimal('3750.00'))


class PaginationTest(TestCase):
    """Tests para verificar la paginación de reportes DGII"""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from proveedores.models import Proveedor
        from compras.models import Compra

        User = get_user_model()

        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa,
            rol='admin'
        )

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111222333'
        )

        # Crear varias compras
        for i in range(15):
            Compra.objects.create(
                empresa=self.empresa,
                proveedor=self.proveedor,
                fecha_compra=date.today(),
                numero_factura_proveedor=f'FAC-{i:03d}',
                numero_ncf=f'B01{i:08d}',
                tipo_gasto='02',
                total=Decimal('1000.00'),
                impuestos=Decimal('180.00'),
                estado='REGISTRADA'
            )

        self.client = APIClient()

    def test_formato_606_sin_paginacion(self):
        """Test: Formato 606 sin parámetros de paginación retorna todos"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(
            f'/api/v1/dgii/reportes/formato_606/?mes={mes}&anio={anio}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cantidad_registros'], 15)
        self.assertEqual(len(response.data['registros']), 15)
        # Sin paginación, page debe ser None
        self.assertIsNone(response.data['page'])

    def test_formato_606_con_paginacion(self):
        """Test: Formato 606 con paginación"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(
            f'/api/v1/dgii/reportes/formato_606/?mes={mes}&anio={anio}&page=1&page_size=5'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cantidad_registros'], 15)
        self.assertEqual(len(response.data['registros']), 5)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 5)
        self.assertEqual(response.data['total_pages'], 3)
        self.assertTrue(response.data['has_next'])
        self.assertFalse(response.data['has_previous'])

    def test_formato_606_ultima_pagina(self):
        """Test: Formato 606 última página"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(
            f'/api/v1/dgii/reportes/formato_606/?mes={mes}&anio={anio}&page=3&page_size=5'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['registros']), 5)
        self.assertEqual(response.data['page'], 3)
        self.assertFalse(response.data['has_next'])
        self.assertTrue(response.data['has_previous'])

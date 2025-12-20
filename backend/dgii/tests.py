"""
Tests para DGII (Comprobantes Fiscales)
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta

from .models import TipoComprobante, SecuenciaNCF
from empresas.models import Empresa

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class TipoComprobanteModelTest(TestCase):
    """Tests para el modelo TipoComprobante"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_tipo_comprobante(self):
        """Test: Crear tipo de comprobante"""
        tipo = TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura de Credito Fiscal',
            prefijo='B'
        )
        self.assertIsNotNone(tipo.id)
        self.assertEqual(tipo.codigo, '01')
        self.assertTrue(tipo.activo)

    def test_tipo_comprobante_str(self):
        """Test: Representacion string de tipo comprobante"""
        tipo = TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura de Credito Fiscal',
            prefijo='B'
        )
        self.assertIn('B01', str(tipo))
        self.assertIn('Factura', str(tipo))

    def test_tipo_comprobante_unique_per_empresa(self):
        """Test: Codigo unico por empresa"""
        TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura CF',
            prefijo='B'
        )
        # Crear otro tipo con mismo codigo en otra empresa deberia funcionar
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        tipo2 = TipoComprobante.objects.create(
            empresa=otra_empresa,
            codigo='01',
            nombre='Factura CF',
            prefijo='B'
        )
        self.assertIsNotNone(tipo2.id)


class SecuenciaNCFModelTest(TestCase):
    """Tests para el modelo SecuenciaNCF"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.tipo = TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura de Credito Fiscal',
            prefijo='B'
        )

    def test_crear_secuencia(self):
        """Test: Crear secuencia NCF"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Principal',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.assertIsNotNone(secuencia.id)
        self.assertEqual(secuencia.secuencia_actual, 0)
        self.assertFalse(secuencia.agotada)

    def test_secuencia_str(self):
        """Test: Representacion string de secuencia"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Principal',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.assertIn('0', str(secuencia))
        self.assertIn('100', str(secuencia))

    def test_siguiente_numero(self):
        """Test: Generar siguiente NCF"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Principal',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        ncf = secuencia.siguiente_numero()
        self.assertEqual(ncf, 'B0100000001')

    def test_secuencia_agotada(self):
        """Test: Detectar secuencia agotada"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Agotado',
            secuencia_inicial=1,
            secuencia_final=10,
            secuencia_actual=10,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.assertTrue(secuencia.agotada)

    def test_siguiente_numero_raises_when_agotada(self):
        """Test: Error al generar NCF de secuencia agotada"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Agotado',
            secuencia_inicial=1,
            secuencia_final=10,
            secuencia_actual=10,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        with self.assertRaises(ValueError):
            secuencia.siguiente_numero()


# ========== TESTS DE API ==========

class TipoComprobanteAPITest(APITestCase):
    """Tests para las APIs de TipoComprobante"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='admin'
        )

        # Asignar permisos
        for model in [TipoComprobante, SecuenciaNCF]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.client = APIClient()

    def test_listar_tipos_comprobante(self):
        """Test: Listar tipos de comprobante"""
        TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura CF',
            prefijo='B'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/tipos-comprobante/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_tipo_comprobante(self):
        """Test: Crear tipo de comprobante"""
        self.client.force_authenticate(user=self.user)
        data = {
            'codigo': '02',
            'nombre': 'Factura de Consumo',
            'prefijo': 'B'
        }
        response = self.client.post('/api/v1/dgii/tipos-comprobante/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo'], '02')

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/dgii/tipos-comprobante/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SecuenciaNCFAPITest(APITestCase):
    """Tests para las APIs de SecuenciaNCF"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='admin'
        )

        # Asignar permisos
        for model in [TipoComprobante, SecuenciaNCF]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.tipo = TipoComprobante.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='Factura CF',
            prefijo='B'
        )

        self.client = APIClient()

    def test_listar_secuencias(self):
        """Test: Listar secuencias NCF"""
        SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Test',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/secuencias/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_secuencia(self):
        """Test: Crear secuencia NCF"""
        self.client.force_authenticate(user=self.user)
        data = {
            'tipo_comprobante': self.tipo.id,
            'descripcion': 'Talonario Nuevo',
            'secuencia_inicial': 1,
            'secuencia_final': 500,
            'fecha_vencimiento': (date.today() + timedelta(days=365)).isoformat(),
            'alerta_cantidad': 50
        }
        response = self.client.post('/api/v1/dgii/secuencias/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['secuencia_final'], 500)

    def test_generar_ncf(self):
        """Test: Generar NCF desde secuencia"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Test',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/dgii/secuencias/{secuencia.id}/generar_ncf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ncf'], 'B0100000001')
        self.assertEqual(response.data['secuencia_actual'], 1)

    def test_generar_ncf_secuencia_agotada(self):
        """Test: Error al generar NCF de secuencia agotada"""
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Agotado',
            secuencia_inicial=1,
            secuencia_final=10,
            secuencia_actual=10,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/dgii/secuencias/{secuencia.id}/generar_ncf/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generar_ncf_secuencia_vencida(self):
        """Test: Error al generar NCF de secuencia vencida"""
        # Crear con fecha válida primero
        secuencia = SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Vencido',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=30)
        )
        # Actualizar fecha a pasada usando update() para bypass de validación
        SecuenciaNCF.objects.filter(pk=secuencia.pk).update(
            fecha_vencimiento=date.today() - timedelta(days=1)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/dgii/secuencias/{secuencia.id}/generar_ncf/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoint_activas(self):
        """Test: Endpoint de secuencias activas"""
        SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Activo',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/secuencias/activas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_endpoint_por_vencer(self):
        """Test: Endpoint de secuencias por vencer"""
        SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Por Vencer',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=15)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/secuencias/por_vencer/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_generar_por_tipo(self):
        """Test: Generar NCF por tipo de comprobante"""
        SecuenciaNCF.objects.create(
            empresa=self.empresa,
            tipo_comprobante=self.tipo,
            descripcion='Talonario Test',
            secuencia_inicial=1,
            secuencia_final=100,
            fecha_vencimiento=date.today() + timedelta(days=365)
        )
        self.client.force_authenticate(user=self.user)
        data = {'tipo_comprobante_id': self.tipo.id}
        response = self.client.post('/api/v1/dgii/secuencias/generar_por_tipo/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ncf', response.data)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/dgii/secuencias/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ========== TESTS DE REPORTES DGII ==========

class ReportesDGIIAPITest(APITestCase):
    """Tests para las APIs de Reportes DGII (606, 607, 608)"""

    def setUp(self):
        from proveedores.models import Proveedor
        from clientes.models import Cliente
        from compras.models import Compra
        from ventas.models import Factura
        from productos.models import Producto
        from decimal import Decimal

        self.empresa = Empresa.objects.create(
            nombre='Empresa Principal',
            rnc='123456789'
        )

        self.user = User.objects.create_user(
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='admin'
        )

        # Crear proveedor
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111222333'
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente Test',
            numero_identificacion='444555666',
            tipo_identificacion='RNC'
        )

        # Crear producto para el usuario
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        # Crear compra para 606
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

        # Crear factura para 607
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            ncf='B0100000001',
            numero_factura='FAC-001',
            total=Decimal('3000.00'),
            itbis=Decimal('540.00'),
            estado='PAGADA',
            tipo_venta='CONTADO',
            venta_sin_comprobante=False,
            usuario=self.user
        )

        # Crear factura cancelada para 608
        self.factura_cancelada = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            ncf='B0100000002',
            numero_factura='FAC-002',
            total=Decimal('1000.00'),
            itbis=Decimal('180.00'),
            estado='CANCELADA',
            tipo_venta='CONTADO',
            venta_sin_comprobante=False,
            usuario=self.user
        )

        self.client = APIClient()

    def test_formato_606_requiere_mes_y_anio(self):
        """Test: Formato 606 requiere mes y anio"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/reportes/formato_606/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mes', response.data['error'])

    def test_formato_606_json(self):
        """Test: Formato 606 retorna JSON"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_606/?mes={mes}&anio={anio}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('registros', response.data)
        self.assertIn('totales', response.data)
        self.assertEqual(response.data['cantidad_registros'], 1)

    def test_formato_606_txt(self):
        """Test: Formato 606 retorna TXT"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_606/?mes={mes}&anio={anio}&formato=txt')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('606_', response['Content-Disposition'])

    def test_formato_607_requiere_mes_y_anio(self):
        """Test: Formato 607 requiere mes y anio"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/reportes/formato_607/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mes', response.data['error'])

    def test_formato_607_json(self):
        """Test: Formato 607 retorna JSON"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_607/?mes={mes}&anio={anio}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('registros', response.data)
        self.assertIn('totales', response.data)
        self.assertEqual(response.data['cantidad_registros'], 1)

    def test_formato_607_txt(self):
        """Test: Formato 607 retorna TXT"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_607/?mes={mes}&anio={anio}&formato=txt')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('607_', response['Content-Disposition'])

    def test_formato_608_requiere_mes_y_anio(self):
        """Test: Formato 608 requiere mes y anio"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/reportes/formato_608/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mes', response.data['error'])

    def test_formato_608_json(self):
        """Test: Formato 608 retorna JSON con anulados"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_608/?mes={mes}&anio={anio}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('registros', response.data)
        self.assertEqual(response.data['cantidad_registros'], 1)

    def test_formato_608_txt(self):
        """Test: Formato 608 retorna TXT"""
        self.client.force_authenticate(user=self.user)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/dgii/reportes/formato_608/?mes={mes}&anio={anio}&formato=txt')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('608_', response['Content-Disposition'])

    def test_reportes_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/dgii/reportes/formato_606/?mes=12&anio=2024')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_formato_606_periodo_sin_registros(self):
        """Test: Formato 606 periodo sin registros retorna lista vacia"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/dgii/reportes/formato_606/?mes=1&anio=2020')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cantidad_registros'], 0)
        self.assertEqual(len(response.data['registros']), 0)

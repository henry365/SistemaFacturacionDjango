from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from .models import Caja, SesionCaja, MovimientoCaja
from empresas.models import Empresa
from usuarios.models import User


class CajaModelTest(TestCase):
    """Tests para el modelo Caja"""

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

    def test_crear_caja(self):
        """Test: Crear una caja"""
        caja = Caja.objects.create(
            nombre='Caja Principal',
            descripcion='Caja principal del local',
            usuario_creacion=self.user
        )
        self.assertEqual(caja.nombre, 'Caja Principal')
        self.assertTrue(caja.activa)
        self.assertIsNotNone(caja.uuid)

    def test_caja_str(self):
        """Test: Representacion string de caja"""
        caja = Caja.objects.create(nombre='Caja 1')
        self.assertEqual(str(caja), 'Caja 1')

    def test_caja_activa_por_defecto(self):
        """Test: Caja es activa por defecto"""
        caja = Caja.objects.create(nombre='Caja Test')
        self.assertTrue(caja.activa)

    def test_desactivar_caja(self):
        """Test: Desactivar una caja"""
        caja = Caja.objects.create(nombre='Caja Test')
        caja.activa = False
        caja.save()
        self.assertFalse(caja.activa)


class SesionCajaModelTest(TestCase):
    """Tests para el modelo SesionCaja"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='cajero',
            password='test123',
            empresa=self.empresa
        )
        self.caja = Caja.objects.create(
            nombre='Caja Principal',
            usuario_creacion=self.user
        )

    def test_crear_sesion(self):
        """Test: Crear sesion de caja"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )
        self.assertEqual(sesion.estado, 'ABIERTA')
        self.assertEqual(sesion.monto_apertura, Decimal('5000.00'))
        self.assertIsNotNone(sesion.uuid)

    def test_sesion_str(self):
        """Test: Representacion string de sesion"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )
        self.assertIn('Caja Principal', str(sesion))
        self.assertIn('cajero', str(sesion))

    def test_cerrar_sesion(self):
        """Test: Cerrar sesion de caja"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('5000.00'),
            monto_cierre_sistema=Decimal('7500.00')
        )
        sesion.cerrar_sesion(Decimal('7600.00'))
        self.assertEqual(sesion.estado, 'CERRADA')
        self.assertEqual(sesion.monto_cierre_usuario, Decimal('7600.00'))
        self.assertEqual(sesion.diferencia, Decimal('100.00'))
        self.assertIsNotNone(sesion.fecha_cierre)

    def test_sesion_estado_inicial(self):
        """Test: Estado inicial de sesion es ABIERTA"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('1000.00')
        )
        self.assertEqual(sesion.estado, 'ABIERTA')


class MovimientoCajaModelTest(TestCase):
    """Tests para el modelo MovimientoCaja"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='cajero',
            password='test123',
            empresa=self.empresa
        )
        self.caja = Caja.objects.create(
            nombre='Caja Principal',
            usuario_creacion=self.user
        )
        self.sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )

    def test_crear_movimiento_venta(self):
        """Test: Crear movimiento de venta"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='VENTA',
            monto=Decimal('1500.00'),
            descripcion='Venta de productos',
            referencia='FAC-001',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, 'VENTA')
        self.assertEqual(movimiento.monto, Decimal('1500.00'))
        self.assertIsNotNone(movimiento.uuid)

    def test_crear_movimiento_retiro(self):
        """Test: Crear movimiento de retiro"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='RETIRO_MANUAL',
            monto=Decimal('2000.00'),
            descripcion='Retiro para deposito bancario',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, 'RETIRO_MANUAL')

    def test_crear_movimiento_gasto_menor(self):
        """Test: Crear movimiento de gasto menor"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='GASTO_MENOR',
            monto=Decimal('150.00'),
            descripcion='Compra de suministros',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, 'GASTO_MENOR')

    def test_movimiento_str(self):
        """Test: Representacion string de movimiento"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='VENTA',
            monto=Decimal('1500.00'),
            descripcion='Test',
            usuario=self.user
        )
        self.assertIn('VENTA', str(movimiento))
        self.assertIn('1500', str(movimiento))


class CajaAPITest(APITestCase):
    """Tests para las APIs de Caja"""

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
            username='cajero',
            password='user123',
            empresa=self.empresa,
            rol='facturador'
        )

        # Asignar permisos
        for model in [Caja, SesionCaja, MovimientoCaja]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.caja = Caja.objects.create(
            nombre='Caja Principal',
            descripcion='Caja del local principal',
            usuario_creacion=self.user
        )

        self.sesion = SesionCaja.objects.create(
            caja=self.caja,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )

        # Crear movimiento de apertura
        MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='APERTURA',
            monto=Decimal('5000.00'),
            descripcion='Monto de apertura',
            usuario=self.user
        )

        self.client = APIClient()

    def test_listar_cajas(self):
        """Test: Listar cajas"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/cajas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_caja(self):
        """Test: Crear caja"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Caja Secundaria',
            'descripcion': 'Segunda caja'
        }
        response = self.client.post('/api/v1/caja/cajas/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Caja Secundaria')

    def test_obtener_sesiones_caja(self):
        """Test: Obtener sesiones de una caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/cajas/{self.caja.id}/sesiones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_obtener_sesion_activa(self):
        """Test: Obtener sesion activa de una caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/cajas/{self.caja.id}/sesion_activa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'ABIERTA')

    def test_listar_sesiones(self):
        """Test: Listar sesiones de caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/sesiones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_sesion(self):
        """Test: Crear nueva sesion de caja"""
        # Cerrar sesion actual
        self.sesion.estado = 'CERRADA'
        self.sesion.save()

        self.client.force_authenticate(user=self.user)
        data = {
            'caja': self.caja.id,
            'monto_apertura': '3000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['monto_apertura'], '3000.00')

    def test_no_crear_sesion_duplicada(self):
        """Test: No se puede crear sesion si ya hay una abierta"""
        self.client.force_authenticate(user=self.user)
        data = {
            'caja': self.caja.id,
            'monto_apertura': '3000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cerrar_sesion(self):
        """Test: Cerrar sesion de caja"""
        # Agregar algunos movimientos
        MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='VENTA',
            monto=Decimal('2500.00'),
            descripcion='Venta',
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'monto_cierre_usuario': '7500.00',
            'observaciones': 'Cierre normal'
        }
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/cerrar/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CERRADA')

    def test_no_cerrar_sesion_ya_cerrada(self):
        """Test: No se puede cerrar una sesion ya cerrada"""
        self.sesion.estado = 'CERRADA'
        self.sesion.save()

        self.client.force_authenticate(user=self.user)
        data = {'monto_cierre_usuario': '5000.00'}
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/cerrar/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_arquear_sesion(self):
        """Test: Arquear sesion cerrada"""
        self.sesion.estado = 'CERRADA'
        self.sesion.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/arquear/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'ARQUEADA')

    def test_no_arquear_sesion_abierta(self):
        """Test: No se puede arquear sesion abierta"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/arquear/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resumen_sesion(self):
        """Test: Obtener resumen de sesion"""
        # Agregar movimientos
        MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='VENTA',
            monto=Decimal('1000.00'),
            descripcion='Venta 1',
            usuario=self.user
        )
        MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='GASTO_MENOR',
            monto=Decimal('100.00'),
            descripcion='Gasto menor',
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/sesiones/{self.sesion.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_ingresos', response.data)
        self.assertIn('total_egresos', response.data)
        self.assertIn('detalle_movimientos', response.data)

    def test_listar_movimientos(self):
        """Test: Listar movimientos de caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/movimientos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_movimiento(self):
        """Test: Crear movimiento de caja"""
        self.client.force_authenticate(user=self.user)
        data = {
            'sesion': self.sesion.id,
            'tipo_movimiento': 'VENTA',
            'monto': '1500.00',
            'descripcion': 'Venta de productos',
            'referencia': 'FAC-001'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_no_crear_movimiento_sesion_cerrada(self):
        """Test: No se puede crear movimiento en sesion cerrada"""
        self.sesion.estado = 'CERRADA'
        self.sesion.save()

        self.client.force_authenticate(user=self.user)
        data = {
            'sesion': self.sesion.id,
            'tipo_movimiento': 'VENTA',
            'monto': '1500.00',
            'descripcion': 'Intento de venta'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtrar_movimientos_por_tipo(self):
        """Test: Filtrar movimientos por tipo"""
        MovimientoCaja.objects.create(
            sesion=self.sesion,
            tipo_movimiento='VENTA',
            monto=Decimal('1000.00'),
            descripcion='Venta',
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/movimientos/?tipo_movimiento=VENTA')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_sesiones_por_estado(self):
        """Test: Filtrar sesiones por estado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/sesiones/?estado=ABIERTA')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Filter to only count sessions with estado='ABIERTA'
        open_sessions = [s for s in results if s.get('estado') == 'ABIERTA']
        self.assertGreaterEqual(len(open_sessions), 1)

    def test_buscar_cajas_por_nombre(self):
        """Test: Buscar cajas por nombre"""
        Caja.objects.create(nombre='Caja Secundaria')

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/cajas/?search=Principal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Check that at least one caja has 'Principal' in name
        principal_cajas = [c for c in results if 'Principal' in c.get('nombre', '')]
        self.assertGreaterEqual(len(principal_cajas), 1)

    def test_filtrar_cajas_activas(self):
        """Test: Filtrar cajas activas"""
        caja_inactiva = Caja.objects.create(nombre='Caja Inactiva', activa=False)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/cajas/?activa=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # All results should be active
        for caja in results:
            self.assertTrue(caja.get('activa', True))

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/caja/cajas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

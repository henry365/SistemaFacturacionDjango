"""
Tests para el módulo de Caja

Este módulo contiene tests para modelos, servicios y APIs del módulo de Caja.
"""
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone

from .models import Caja, SesionCaja, MovimientoCaja
from .services import CajaService, SesionCajaService, MovimientoCajaService
from .constants import (
    ESTADO_ABIERTA, ESTADO_CERRADA, ESTADO_ARQUEADA,
    TIPO_VENTA, TIPO_APERTURA, TIPO_GASTO_MENOR, TIPO_RETIRO_MANUAL
)
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
            empresa=self.empresa,
            usuario_creacion=self.user
        )
        self.assertEqual(caja.nombre, 'Caja Principal')
        self.assertTrue(caja.activa)
        self.assertIsNotNone(caja.uuid)

    def test_caja_str(self):
        """Test: Representacion string de caja"""
        caja = Caja.objects.create(nombre='Caja 1', empresa=self.empresa)
        self.assertEqual(str(caja), 'Caja 1')

    def test_caja_activa_por_defecto(self):
        """Test: Caja es activa por defecto"""
        caja = Caja.objects.create(nombre='Caja Test', empresa=self.empresa)
        self.assertTrue(caja.activa)

    def test_desactivar_caja(self):
        """Test: Desactivar una caja"""
        caja = Caja.objects.create(nombre='Caja Test', empresa=self.empresa)
        caja.activa = False
        caja.save()
        self.assertFalse(caja.activa)

    def test_tiene_sesion_abierta(self):
        """Test: Verificar si caja tiene sesión abierta"""
        caja = Caja.objects.create(nombre='Caja Test', empresa=self.empresa)
        self.assertFalse(caja.tiene_sesion_abierta())

        SesionCaja.objects.create(
            caja=caja,
            empresa=self.empresa,
            usuario=self.user,
            monto_apertura=Decimal('1000.00')
        )
        self.assertTrue(caja.tiene_sesion_abierta())


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
            empresa=self.empresa,
            usuario_creacion=self.user
        )

    def test_crear_sesion(self):
        """Test: Crear sesion de caja"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            empresa=self.empresa,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )
        self.assertEqual(sesion.estado, ESTADO_ABIERTA)
        self.assertEqual(sesion.monto_apertura, Decimal('5000.00'))
        self.assertIsNotNone(sesion.uuid)

    def test_sesion_str(self):
        """Test: Representacion string de sesion"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            empresa=self.empresa,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )
        self.assertIn('Caja Principal', str(sesion))
        self.assertIn('cajero', str(sesion))

    def test_sesion_estado_inicial(self):
        """Test: Estado inicial de sesion es ABIERTA"""
        sesion = SesionCaja.objects.create(
            caja=self.caja,
            empresa=self.empresa,
            usuario=self.user,
            monto_apertura=Decimal('1000.00')
        )
        self.assertEqual(sesion.estado, ESTADO_ABIERTA)


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
            empresa=self.empresa,
            usuario_creacion=self.user
        )
        self.sesion = SesionCaja.objects.create(
            caja=self.caja,
            empresa=self.empresa,
            usuario=self.user,
            monto_apertura=Decimal('5000.00')
        )

    def test_crear_movimiento_venta(self):
        """Test: Crear movimiento de venta"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            empresa=self.empresa,
            tipo_movimiento=TIPO_VENTA,
            monto=Decimal('1500.00'),
            descripcion='Venta de productos',
            referencia='FAC-001',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, TIPO_VENTA)
        self.assertEqual(movimiento.monto, Decimal('1500.00'))
        self.assertIsNotNone(movimiento.uuid)
        self.assertTrue(movimiento.es_ingreso)
        self.assertFalse(movimiento.es_egreso)

    def test_crear_movimiento_retiro(self):
        """Test: Crear movimiento de retiro"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            empresa=self.empresa,
            tipo_movimiento=TIPO_RETIRO_MANUAL,
            monto=Decimal('2000.00'),
            descripcion='Retiro para deposito bancario',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, TIPO_RETIRO_MANUAL)
        self.assertTrue(movimiento.es_egreso)
        self.assertFalse(movimiento.es_ingreso)

    def test_crear_movimiento_gasto_menor(self):
        """Test: Crear movimiento de gasto menor"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            empresa=self.empresa,
            tipo_movimiento=TIPO_GASTO_MENOR,
            monto=Decimal('150.00'),
            descripcion='Compra de suministros',
            usuario=self.user
        )
        self.assertEqual(movimiento.tipo_movimiento, TIPO_GASTO_MENOR)

    def test_movimiento_str(self):
        """Test: Representacion string de movimiento"""
        movimiento = MovimientoCaja.objects.create(
            sesion=self.sesion,
            empresa=self.empresa,
            tipo_movimiento=TIPO_VENTA,
            monto=Decimal('1500.00'),
            descripcion='Test',
            usuario=self.user
        )
        self.assertIn('VENTA', str(movimiento))
        self.assertIn('1500', str(movimiento))


class SesionCajaServiceTest(TestCase):
    """Tests para SesionCajaService"""

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
            empresa=self.empresa,
            usuario_creacion=self.user
        )

    def test_abrir_sesion(self):
        """Test: Abrir sesion usando servicio"""
        sesion, error = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )
        self.assertIsNone(error)
        self.assertIsNotNone(sesion)
        self.assertEqual(sesion.estado, ESTADO_ABIERTA)
        self.assertEqual(sesion.monto_apertura, Decimal('5000.00'))

    def test_abrir_sesion_idempotente(self):
        """Test: Abrir sesion es idempotente para el mismo usuario"""
        sesion1, error1 = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )
        self.assertIsNone(error1)

        # Segunda llamada con el mismo usuario
        sesion2, error2 = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('3000.00'),
            usuario=self.user
        )
        self.assertIsNone(error2)
        self.assertEqual(sesion1.id, sesion2.id)  # Misma sesión

    def test_cerrar_sesion(self):
        """Test: Cerrar sesion usando servicio"""
        sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )

        exito, error = SesionCajaService.cerrar_sesion(
            sesion=sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )
        self.assertTrue(exito)
        self.assertIsNone(error)
        sesion.refresh_from_db()
        self.assertEqual(sesion.estado, ESTADO_CERRADA)

    def test_cerrar_sesion_idempotente(self):
        """Test: Cerrar sesion es idempotente"""
        sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )

        # Primera llamada
        exito1, error1 = SesionCajaService.cerrar_sesion(
            sesion=sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )
        self.assertTrue(exito1)

        # Segunda llamada (idempotente)
        exito2, error2 = SesionCajaService.cerrar_sesion(
            sesion=sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )
        self.assertTrue(exito2)
        self.assertIsNone(error2)

    def test_arquear_sesion(self):
        """Test: Arquear sesion usando servicio"""
        sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )
        SesionCajaService.cerrar_sesion(
            sesion=sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        exito, error = SesionCajaService.arquear_sesion(
            sesion=sesion,
            ejecutado_por=self.user
        )
        self.assertTrue(exito)
        sesion.refresh_from_db()
        self.assertEqual(sesion.estado, ESTADO_ARQUEADA)

    def test_calcular_saldo_sesion(self):
        """Test: Calcular saldo de sesion"""
        sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )

        # Agregar movimientos
        MovimientoCajaService.registrar_venta(
            sesion=sesion,
            monto=Decimal('1000.00'),
            usuario=self.user
        )
        MovimientoCajaService.registrar_gasto_menor(
            sesion=sesion,
            monto=Decimal('100.00'),
            descripcion='Gasto',
            usuario=self.user
        )

        saldo = SesionCajaService.calcular_saldo_sesion(sesion)
        # Apertura (5000) + Venta (1000) - Gasto (100) = 5900
        self.assertEqual(saldo, Decimal('5900.00'))


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
            empresa=self.empresa,
            usuario_creacion=self.user
        )

        self.sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
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

    def test_obtener_sesion_activa(self):
        """Test: Obtener sesion activa de una caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/cajas/{self.caja.id}/sesion_activa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], ESTADO_ABIERTA)

    def test_listar_sesiones(self):
        """Test: Listar sesiones de caja"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/sesiones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_sesion(self):
        """Test: Crear nueva sesion de caja"""
        # Cerrar sesion actual
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'caja': self.caja.id,
            'monto_apertura': '3000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['monto_apertura'], '3000.00')

    def test_crear_sesion_retorna_existente_si_mismo_usuario(self):
        """Test: Crear sesion retorna la existente si es el mismo usuario (idempotente)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'caja': self.caja.id,
            'monto_apertura': '3000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        # Debido a la idempotencia, retorna 201 pero con la sesión existente
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verificar que es la misma sesión
        self.assertEqual(response.data['id'], self.sesion.id)

    def test_cerrar_sesion(self):
        """Test: Cerrar sesion de caja"""
        # Agregar algunos movimientos
        MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('2500.00'),
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'monto_cierre_usuario': '7500.00',
            'observaciones': 'Cierre normal'
        }
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/cerrar/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], ESTADO_CERRADA)

    def test_no_cerrar_sesion_ya_cerrada(self):
        """Test: Cerrar sesion ya cerrada es idempotente"""
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {'monto_cierre_usuario': '5000.00'}
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/cerrar/', data)
        # Idempotente - retorna OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_arquear_sesion(self):
        """Test: Arquear sesion cerrada"""
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/arquear/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], ESTADO_ARQUEADA)

    def test_no_arquear_sesion_abierta(self):
        """Test: No se puede arquear sesion abierta"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/sesiones/{self.sesion.id}/arquear/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resumen_sesion(self):
        """Test: Obtener resumen de sesion"""
        # Agregar movimientos
        MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('1000.00'),
            usuario=self.user
        )
        MovimientoCajaService.registrar_gasto_menor(
            sesion=self.sesion,
            monto=Decimal('100.00'),
            descripcion='Gasto menor',
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/sesiones/{self.sesion.id}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('saldo_actual', response.data)
        self.assertIn('movimientos_por_tipo', response.data)

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
            'tipo_movimiento': TIPO_VENTA,
            'monto': '1500.00',
            'descripcion': 'Venta de productos',
            'referencia': 'FAC-001'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_no_crear_movimiento_sesion_cerrada(self):
        """Test: No se puede crear movimiento en sesion cerrada"""
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {
            'sesion': self.sesion.id,
            'tipo_movimiento': TIPO_VENTA,
            'monto': '1500.00',
            'descripcion': 'Intento de venta'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtrar_movimientos_por_tipo(self):
        """Test: Filtrar movimientos por tipo"""
        MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('1000.00'),
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/movimientos/?tipo_movimiento={TIPO_VENTA}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_sesiones_por_estado(self):
        """Test: Filtrar sesiones por estado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/caja/sesiones/?estado={ESTADO_ABIERTA}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        open_sessions = [s for s in results if s.get('estado') == ESTADO_ABIERTA]
        self.assertGreaterEqual(len(open_sessions), 1)

    def test_buscar_cajas_por_nombre(self):
        """Test: Buscar cajas por nombre"""
        Caja.objects.create(nombre='Caja Secundaria', empresa=self.empresa)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/cajas/?search=Principal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        principal_cajas = [c for c in results if 'Principal' in c.get('nombre', '')]
        self.assertGreaterEqual(len(principal_cajas), 1)

    def test_filtrar_cajas_activas(self):
        """Test: Filtrar cajas activas"""
        Caja.objects.create(nombre='Caja Inactiva', activa=False, empresa=self.empresa)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/caja/cajas/?activa=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for caja in results:
            self.assertTrue(caja.get('activa', True))

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/caja/cajas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activar_caja(self):
        """Test: Activar caja desactivada"""
        self.caja.activa = False
        self.caja.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/cajas/{self.caja.id}/activar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.caja.refresh_from_db()
        self.assertTrue(self.caja.activa)

    def test_desactivar_caja_sin_sesion_abierta(self):
        """Test: Desactivar caja sin sesión abierta"""
        # Cerrar la sesión primero
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/cajas/{self.caja.id}/desactivar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.caja.refresh_from_db()
        self.assertFalse(self.caja.activa)

    def test_no_desactivar_caja_con_sesion_abierta(self):
        """Test: No se puede desactivar caja con sesión abierta"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/caja/cajas/{self.caja.id}/desactivar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anular_movimiento(self):
        """Test: Anular movimiento de caja"""
        movimiento, _ = MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('1000.00'),
            usuario=self.user
        )

        self.client.force_authenticate(user=self.user)
        data = {'motivo': 'Error en el monto'}
        response = self.client.post(f'/api/v1/caja/movimientos/{movimiento.id}/anular/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MovimientoCajaServiceTest(TestCase):
    """Tests para MovimientoCajaService"""

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
            empresa=self.empresa,
            usuario_creacion=self.user
        )
        self.sesion, _ = SesionCajaService.abrir_sesion(
            caja=self.caja,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user
        )

    def test_registrar_venta(self):
        """Test: Registrar venta usando servicio"""
        movimiento, error = MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('1500.00'),
            usuario=self.user,
            referencia='FAC-001'
        )
        self.assertIsNone(error)
        self.assertIsNotNone(movimiento)
        self.assertEqual(movimiento.tipo_movimiento, TIPO_VENTA)

    def test_registrar_gasto_menor(self):
        """Test: Registrar gasto menor usando servicio"""
        movimiento, error = MovimientoCajaService.registrar_gasto_menor(
            sesion=self.sesion,
            monto=Decimal('100.00'),
            descripcion='Compra de suministros',
            usuario=self.user
        )
        self.assertIsNone(error)
        self.assertEqual(movimiento.tipo_movimiento, TIPO_GASTO_MENOR)

    def test_puede_eliminar_movimiento_normal(self):
        """Test: Se puede eliminar movimiento normal"""
        movimiento, _ = MovimientoCajaService.registrar_venta(
            sesion=self.sesion,
            monto=Decimal('1000.00'),
            usuario=self.user
        )
        puede, error = MovimientoCajaService.puede_eliminar(movimiento)
        self.assertTrue(puede)
        self.assertIsNone(error)

    def test_no_puede_eliminar_movimiento_apertura(self):
        """Test: No se puede eliminar movimiento de apertura"""
        movimiento = self.sesion.movimientos.filter(tipo_movimiento=TIPO_APERTURA).first()
        puede, error = MovimientoCajaService.puede_eliminar(movimiento)
        self.assertFalse(puede)
        self.assertIsNotNone(error)


class EmpresaValidationSerializerTest(APITestCase):
    """
    Tests para validación de empresa en serializers.

    Verifica que los serializers validen correctamente que los objetos
    referenciados (caja, sesion) pertenezcan a la empresa del usuario.
    """

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
            for model in [Caja, SesionCaja, MovimientoCaja]:
                content_type = ContentType.objects.get_for_model(model)
                for codename in ['view', 'add', 'change', 'delete']:
                    perm_codename = f'{codename}_{model._meta.model_name}'
                    try:
                        perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                        user.user_permissions.add(perm)
                    except Permission.DoesNotExist:
                        pass

        # Crear caja para empresa 1
        self.caja_empresa1 = Caja.objects.create(
            nombre='Caja Empresa 1',
            empresa=self.empresa1,
            usuario_creacion=self.user_empresa1
        )

        # Crear caja para empresa 2
        self.caja_empresa2 = Caja.objects.create(
            nombre='Caja Empresa 2',
            empresa=self.empresa2,
            usuario_creacion=self.user_empresa2
        )

        # Crear sesión para empresa 1
        self.sesion_empresa1, _ = SesionCajaService.abrir_sesion(
            caja=self.caja_empresa1,
            monto_apertura=Decimal('5000.00'),
            usuario=self.user_empresa1
        )

        # Crear sesión para empresa 2
        self.sesion_empresa2, _ = SesionCajaService.abrir_sesion(
            caja=self.caja_empresa2,
            monto_apertura=Decimal('3000.00'),
            usuario=self.user_empresa2
        )

        self.client = APIClient()

    def test_abrir_sesion_caja_misma_empresa(self):
        """Test: Puede abrir sesión en caja de su propia empresa"""
        # Cerrar sesión existente primero
        SesionCajaService.cerrar_sesion(
            sesion=self.sesion_empresa1,
            monto_cierre_usuario=Decimal('5000.00'),
            ejecutado_por=self.user_empresa1
        )

        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'caja': self.caja_empresa1.id,
            'monto_apertura': '1000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_abrir_sesion_caja_otra_empresa_falla(self):
        """Test: No puede abrir sesión en caja de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'caja': self.caja_empresa2.id,  # Caja de otra empresa
            'monto_apertura': '1000.00'
        }
        response = self.client.post('/api/v1/caja/sesiones/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa', str(response.data).lower())

    def test_crear_movimiento_sesion_misma_empresa(self):
        """Test: Puede crear movimiento en sesión de su propia empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'sesion': self.sesion_empresa1.id,
            'tipo_movimiento': TIPO_VENTA,
            'monto': '500.00',
            'descripcion': 'Venta de prueba'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_movimiento_sesion_otra_empresa_falla(self):
        """Test: No puede crear movimiento en sesión de otra empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        data = {
            'sesion': self.sesion_empresa2.id,  # Sesión de otra empresa
            'tipo_movimiento': TIPO_VENTA,
            'monto': '500.00',
            'descripcion': 'Intento de venta'
        }
        response = self.client.post('/api/v1/caja/movimientos/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa', str(response.data).lower())

    def test_listar_cajas_solo_empresa_propia(self):
        """Test: Al listar cajas solo ve las de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get('/api/v1/caja/cajas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Solo debe ver cajas de empresa1
        for caja in results:
            caja_obj = Caja.objects.get(id=caja['id'])
            self.assertEqual(caja_obj.empresa, self.empresa1)

    def test_listar_sesiones_solo_empresa_propia(self):
        """Test: Al listar sesiones solo ve las de su empresa"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get('/api/v1/caja/sesiones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Solo debe ver sesiones de empresa1
        for sesion in results:
            sesion_obj = SesionCaja.objects.get(id=sesion['id'])
            self.assertEqual(sesion_obj.empresa, self.empresa1)

    def test_listar_movimientos_solo_empresa_propia(self):
        """Test: Al listar movimientos solo ve los de su empresa"""
        # Crear movimientos en ambas empresas
        MovimientoCajaService.registrar_venta(
            sesion=self.sesion_empresa1,
            monto=Decimal('100.00'),
            usuario=self.user_empresa1
        )
        MovimientoCajaService.registrar_venta(
            sesion=self.sesion_empresa2,
            monto=Decimal('200.00'),
            usuario=self.user_empresa2
        )

        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get('/api/v1/caja/movimientos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Solo debe ver movimientos de empresa1
        for movimiento in results:
            mov_obj = MovimientoCaja.objects.get(id=movimiento['id'])
            self.assertEqual(mov_obj.empresa, self.empresa1)

    def test_no_acceder_caja_otra_empresa_por_id(self):
        """Test: No puede acceder a caja de otra empresa por ID"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/caja/cajas/{self.caja_empresa2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_acceder_sesion_otra_empresa_por_id(self):
        """Test: No puede acceder a sesión de otra empresa por ID"""
        self.client.force_authenticate(user=self.user_empresa1)
        response = self.client.get(f'/api/v1/caja/sesiones/{self.sesion_empresa2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

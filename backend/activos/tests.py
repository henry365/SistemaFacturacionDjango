"""
Tests para Activos Fijos
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from .models import TipoActivo, ActivoFijo, Depreciacion
from empresas.models import Empresa

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class TipoActivoModelTest(TestCase):
    """Tests para el modelo TipoActivo"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_tipo_activo(self):
        """Test: Crear tipo de activo"""
        tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )
        self.assertIsNotNone(tipo.id)
        self.assertEqual(tipo.nombre, 'Vehiculos')
        self.assertTrue(tipo.activo)

    def test_tipo_activo_str(self):
        """Test: Representacion string de tipo activo"""
        tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Mobiliario',
            porcentaje_depreciacion_anual=Decimal('10.00'),
            vida_util_anos=10
        )
        self.assertEqual(str(tipo), 'Mobiliario')


class ActivoFijoModelTest(TestCase):
    """Tests para el modelo ActivoFijo"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )

    def test_crear_activo_fijo(self):
        """Test: Crear activo fijo"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla 2023',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('50000.00')
        )
        self.assertIsNotNone(activo.id)
        self.assertEqual(activo.estado, 'ACTIVO')

    def test_activo_fijo_str(self):
        """Test: Representacion string de activo"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla 2023',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('50000.00')
        )
        self.assertIn('VEH-001', str(activo))
        self.assertIn('Toyota', str(activo))

    def test_depreciacion_acumulada_property(self):
        """Test: Propiedad depreciacion_acumulada"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('40000.00')
        )
        self.assertEqual(activo.depreciacion_acumulada, Decimal('10000.00'))

    def test_porcentaje_depreciado_property(self):
        """Test: Propiedad porcentaje_depreciado"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('40000.00')
        )
        self.assertEqual(activo.porcentaje_depreciado, 20.0)


class DepreciacionModelTest(TestCase):
    """Tests para el modelo Depreciacion"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )
        self.activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today() - timedelta(days=365),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('50000.00')
        )

    def test_crear_depreciacion(self):
        """Test: Crear registro de depreciacion"""
        depreciacion = Depreciacion.objects.create(
            activo=self.activo,
            fecha=date.today(),
            monto=Decimal('1041.67'),
            valor_libro_anterior=Decimal('50000.00'),
            valor_libro_nuevo=Decimal('48958.33')
        )
        self.assertIsNotNone(depreciacion.id)

    def test_depreciacion_str(self):
        """Test: Representacion string de depreciacion"""
        depreciacion = Depreciacion.objects.create(
            activo=self.activo,
            fecha=date.today(),
            monto=Decimal('1041.67'),
            valor_libro_anterior=Decimal('50000.00'),
            valor_libro_nuevo=Decimal('48958.33')
        )
        self.assertIn('VEH-001', str(depreciacion))

    def test_depreciacion_actualiza_valor_libro(self):
        """Test: Depreciacion actualiza valor libro del activo"""
        Depreciacion.objects.create(
            activo=self.activo,
            fecha=date.today(),
            monto=Decimal('1041.67'),
            valor_libro_anterior=Decimal('50000.00'),
            valor_libro_nuevo=Decimal('48958.33')
        )
        self.activo.refresh_from_db()
        self.assertEqual(self.activo.valor_libro_actual, Decimal('48958.33'))


# ========== TESTS DE API ==========

class TipoActivoAPITest(APITestCase):
    """Tests para las APIs de TipoActivo"""

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
        for model in [TipoActivo, ActivoFijo, Depreciacion]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.client = APIClient()

    def test_listar_tipos_activo(self):
        """Test: Listar tipos de activo"""
        TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/activos/tipos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_tipo_activo(self):
        """Test: Crear tipo de activo"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Equipos de Computo',
            'porcentaje_depreciacion_anual': '33.33',
            'vida_util_anos': 3
        }
        response = self.client.post('/api/v1/activos/tipos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Equipos de Computo')

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/activos/tipos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActivoFijoAPITest(APITestCase):
    """Tests para las APIs de ActivoFijo"""

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
        for model in [TipoActivo, ActivoFijo, Depreciacion]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )

        self.client = APIClient()

    def test_listar_activos(self):
        """Test: Listar activos fijos"""
        ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('50000.00'),
            valor_libro_actual=Decimal('50000.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/activos/activos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_activo(self):
        """Test: Crear activo fijo"""
        self.client.force_authenticate(user=self.user)
        data = {
            'tipo_activo': self.tipo.id,
            'codigo_interno': 'VEH-002',
            'nombre': 'Honda Civic',
            'fecha_adquisicion': date.today().isoformat(),
            'valor_adquisicion': '45000.00',
            'valor_libro_actual': '45000.00'
        }
        response = self.client.post('/api/v1/activos/activos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo_interno'], 'VEH-002')

    def test_depreciar_activo(self):
        """Test: Depreciar activo"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today() - timedelta(days=365),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )
        self.client.force_authenticate(user=self.user)
        data = {'fecha': date.today().isoformat()}
        response = self.client.post(f'/api/v1/activos/activos/{activo.id}/depreciar/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('depreciacion', response.data)
        self.assertIn('activo', response.data)

    def test_depreciar_activo_ya_depreciado(self):
        """Test: Error al depreciar activo totalmente depreciado"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today() - timedelta(days=365*5),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('0.00'),
            estado='DEPRECIADO'
        )
        self.client.force_authenticate(user=self.user)
        data = {'fecha': date.today().isoformat()}
        response = self.client.post(f'/api/v1/activos/activos/{activo.id}/depreciar/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_historial_depreciacion(self):
        """Test: Obtener historial de depreciacion"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today() - timedelta(days=365),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )
        Depreciacion.objects.create(
            activo=activo,
            fecha=date.today() - timedelta(days=30),
            monto=Decimal('1000.00'),
            valor_libro_anterior=Decimal('48000.00'),
            valor_libro_nuevo=Decimal('47000.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/activos/activos/{activo.id}/historial_depreciacion/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_cambiar_estado(self):
        """Test: Cambiar estado de activo"""
        activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )
        self.client.force_authenticate(user=self.user)
        data = {'estado': 'MANTENIMIENTO'}
        response = self.client.post(f'/api/v1/activos/activos/{activo.id}/cambiar_estado/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'MANTENIMIENTO')

    def test_endpoint_por_estado(self):
        """Test: Endpoint resumen por estado"""
        ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/activos/activos/por_estado/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_endpoint_por_tipo(self):
        """Test: Endpoint resumen por tipo"""
        ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today(),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/activos/activos/por_tipo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticacion recibe 401"""
        response = self.client.get('/api/v1/activos/activos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

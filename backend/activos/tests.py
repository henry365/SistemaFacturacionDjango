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


# ========== TESTS DE VALIDACIONES DE NEGOCIO ==========

class TipoActivoValidacionesTest(TestCase):
    """Tests para validaciones del modelo TipoActivo"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_porcentaje_negativo_error(self):
        """Test: Error al crear tipo con porcentaje negativo"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            TipoActivo.objects.create(
                empresa=self.empresa,
                nombre='Test',
                porcentaje_depreciacion_anual=Decimal('-10.00'),
                vida_util_anos=5
            )

    def test_porcentaje_mayor_100_error(self):
        """Test: Error al crear tipo con porcentaje mayor a 100"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            TipoActivo.objects.create(
                empresa=self.empresa,
                nombre='Test',
                porcentaje_depreciacion_anual=Decimal('150.00'),
                vida_util_anos=5
            )

    def test_vida_util_cero_error(self):
        """Test: Error al crear tipo con vida util cero"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            TipoActivo.objects.create(
                empresa=self.empresa,
                nombre='Test',
                porcentaje_depreciacion_anual=Decimal('25.00'),
                vida_util_anos=0
            )

    def test_vida_util_negativa_error(self):
        """Test: Error al crear tipo con vida util negativa"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            TipoActivo.objects.create(
                empresa=self.empresa,
                nombre='Test',
                porcentaje_depreciacion_anual=Decimal('25.00'),
                vida_util_anos=-5
            )


class ActivoFijoValidacionesTest(TestCase):
    """Tests para validaciones del modelo ActivoFijo"""

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

    def test_valor_adquisicion_negativo_error(self):
        """Test: Error al crear activo con valor de adquisicion negativo"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ActivoFijo.objects.create(
                empresa=self.empresa,
                tipo_activo=self.tipo,
                codigo_interno='VEH-001',
                nombre='Test',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('-50000.00'),
                valor_libro_actual=Decimal('50000.00')
            )

    def test_valor_libro_negativo_error(self):
        """Test: Error al crear activo con valor libro negativo"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ActivoFijo.objects.create(
                empresa=self.empresa,
                tipo_activo=self.tipo,
                codigo_interno='VEH-001',
                nombre='Test',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('50000.00'),
                valor_libro_actual=Decimal('-1000.00')
            )

    def test_valor_libro_mayor_adquisicion_error(self):
        """Test: Error si valor libro es mayor al valor de adquisicion"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ActivoFijo.objects.create(
                empresa=self.empresa,
                tipo_activo=self.tipo,
                codigo_interno='VEH-001',
                nombre='Test',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('50000.00'),
                valor_libro_actual=Decimal('60000.00')
            )

    def test_fecha_adquisicion_futura_error(self):
        """Test: Error si fecha de adquisicion es futura"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ActivoFijo.objects.create(
                empresa=self.empresa,
                tipo_activo=self.tipo,
                codigo_interno='VEH-001',
                nombre='Test',
                fecha_adquisicion=date.today() + timedelta(days=30),
                valor_adquisicion=Decimal('50000.00'),
                valor_libro_actual=Decimal('50000.00')
            )

    def test_tipo_activo_otra_empresa_error(self):
        """Test: Error si tipo_activo pertenece a otra empresa"""
        from django.core.exceptions import ValidationError
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        tipo_otra = TipoActivo.objects.create(
            empresa=otra_empresa,
            nombre='Mobiliario',
            porcentaje_depreciacion_anual=Decimal('10.00'),
            vida_util_anos=10
        )
        with self.assertRaises(ValidationError):
            ActivoFijo.objects.create(
                empresa=self.empresa,
                tipo_activo=tipo_otra,
                codigo_interno='MOB-001',
                nombre='Test',
                fecha_adquisicion=date.today(),
                valor_adquisicion=Decimal('5000.00'),
                valor_libro_actual=Decimal('5000.00')
            )


class DepreciacionValidacionesTest(TestCase):
    """Tests para validaciones del modelo Depreciacion"""

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

    def test_valor_libro_nuevo_negativo_error(self):
        """Test: Error si valor libro nuevo es negativo"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Depreciacion.objects.create(
                activo=self.activo,
                fecha=date.today(),
                monto=Decimal('1000.00'),
                valor_libro_anterior=Decimal('50000.00'),
                valor_libro_nuevo=Decimal('-100.00')
            )

    def test_monto_negativo_error(self):
        """Test: Error si monto de depreciacion es negativo"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Depreciacion.objects.create(
                activo=self.activo,
                fecha=date.today(),
                monto=Decimal('-1000.00'),
                valor_libro_anterior=Decimal('50000.00'),
                valor_libro_nuevo=Decimal('51000.00')
            )

    def test_inconsistencia_valores_error(self):
        """Test: Error si valores no son consistentes (nuevo != anterior - monto)"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Depreciacion.objects.create(
                activo=self.activo,
                fecha=date.today(),
                monto=Decimal('1000.00'),
                valor_libro_anterior=Decimal('50000.00'),
                valor_libro_nuevo=Decimal('45000.00')  # Deberia ser 49000
            )

    def test_fecha_anterior_adquisicion_error(self):
        """Test: Error si fecha es anterior a fecha de adquisicion"""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Depreciacion.objects.create(
                activo=self.activo,
                fecha=self.activo.fecha_adquisicion - timedelta(days=30),
                monto=Decimal('1000.00'),
                valor_libro_anterior=Decimal('50000.00'),
                valor_libro_nuevo=Decimal('49000.00')
            )


# ========== TESTS DE SERVICIOS ==========

class DepreciacionServiceTest(TestCase):
    """Tests para el servicio de depreciacion"""

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
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        self.activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-001',
            nombre='Toyota Corolla',
            fecha_adquisicion=date.today() - timedelta(days=365),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )

    def test_calcular_depreciacion_mensual_linea_recta(self):
        """Test: Calculo de depreciacion mensual metodo linea recta"""
        from .services import DepreciacionService
        monto = DepreciacionService.calcular_depreciacion_mensual(
            self.activo,
            metodo='linea_recta'
        )
        # 48000 * (25/12/100) = 1000
        self.assertEqual(monto, Decimal('1000.00'))

    def test_puede_depreciar_activo_activo(self):
        """Test: Puede depreciar activo en estado ACTIVO"""
        from .services import DepreciacionService
        puede, error = DepreciacionService.puede_depreciar(self.activo)
        self.assertTrue(puede)
        self.assertIsNone(error)

    def test_no_puede_depreciar_activo_vendido(self):
        """Test: No puede depreciar activo VENDIDO"""
        from .services import DepreciacionService
        self.activo.estado = 'VENDIDO'
        self.activo.save(update_fields=['estado'])
        puede, error = DepreciacionService.puede_depreciar(self.activo)
        self.assertFalse(puede)
        self.assertIsNotNone(error)

    def test_no_puede_depreciar_valor_libro_cero(self):
        """Test: No puede depreciar activo con valor libro 0"""
        from .services import DepreciacionService
        self.activo.valor_libro_actual = Decimal('0')
        self.activo.save(update_fields=['valor_libro_actual'])
        puede, error = DepreciacionService.puede_depreciar(self.activo)
        self.assertFalse(puede)

    def test_registrar_depreciacion(self):
        """Test: Registrar depreciacion via servicio"""
        from .services import DepreciacionService
        depreciacion, error = DepreciacionService.registrar_depreciacion(
            activo=self.activo,
            fecha=date.today(),
            usuario=self.user,
            observacion='Test de depreciacion'
        )
        self.assertIsNotNone(depreciacion)
        self.assertIsNone(error)
        self.assertEqual(depreciacion.monto, Decimal('1000.00'))

    def test_calcular_proyeccion_depreciacion(self):
        """Test: Calcular proyeccion de depreciaciones"""
        from .services import DepreciacionService
        proyeccion = DepreciacionService.calcular_proyeccion_depreciacion(
            self.activo,
            meses=12,
            metodo='linea_recta'
        )
        self.assertEqual(len(proyeccion), 12)
        self.assertEqual(proyeccion[0]['monto_depreciacion'], Decimal('1000.00'))


class PermisosActivosTest(TestCase):
    """Tests para permisos granulares en activos"""

    def setUp(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        self.empresa = Empresa.objects.create(
            nombre='Test Empresa',
            rnc='123456789'
        )
        self.tipo = TipoActivo.objects.create(
            empresa=self.empresa,
            nombre='Vehiculos',
            porcentaje_depreciacion_anual=Decimal('25.00'),
            vida_util_anos=4
        )
        # Usuario sin permisos especiales
        self.user_sin_permisos = User.objects.create_user(
            username='user_sin_permisos',
            password='test123',
            empresa=self.empresa
        )
        # Usuario con permisos de depreciación
        self.user_con_permisos = User.objects.create_user(
            username='user_con_permisos',
            password='test123',
            empresa=self.empresa
        )
        # Obtener y asignar permiso de depreciación
        content_type = ContentType.objects.get_for_model(ActivoFijo)
        perm_depreciar = Permission.objects.get(
            codename='depreciar_activofijo',
            content_type=content_type
        )
        perm_cambiar = Permission.objects.get(
            codename='cambiar_estado_activofijo',
            content_type=content_type
        )
        self.user_con_permisos.user_permissions.add(perm_depreciar, perm_cambiar)

        # Usuario staff
        self.user_staff = User.objects.create_user(
            username='user_staff',
            password='test123',
            empresa=self.empresa,
            is_staff=True
        )

        self.activo = ActivoFijo.objects.create(
            empresa=self.empresa,
            tipo_activo=self.tipo,
            codigo_interno='VEH-PERM-001',
            nombre='Toyota Test',
            fecha_adquisicion=date.today() - timedelta(days=365),
            valor_adquisicion=Decimal('48000.00'),
            valor_libro_actual=Decimal('48000.00')
        )

        self.client = APIClient()

    def test_depreciar_sin_permiso_denegado(self):
        """Test: Usuario sin permiso no puede depreciar"""
        self.client.force_authenticate(user=self.user_sin_permisos)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/depreciar/',
            {'fecha': str(date.today())}
        )
        self.assertEqual(response.status_code, 403)

    def test_depreciar_con_permiso_permitido(self):
        """Test: Usuario con permiso puede depreciar"""
        self.client.force_authenticate(user=self.user_con_permisos)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/depreciar/',
            {'fecha': str(date.today())}
        )
        self.assertEqual(response.status_code, 200)

    def test_depreciar_staff_permitido(self):
        """Test: Usuario staff puede depreciar"""
        self.client.force_authenticate(user=self.user_staff)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/depreciar/',
            {'fecha': str(date.today())}
        )
        self.assertEqual(response.status_code, 200)

    def test_cambiar_estado_sin_permiso_denegado(self):
        """Test: Usuario sin permiso no puede cambiar estado"""
        self.client.force_authenticate(user=self.user_sin_permisos)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/cambiar_estado/',
            {'estado': 'MANTENIMIENTO'}
        )
        self.assertEqual(response.status_code, 403)

    def test_cambiar_estado_con_permiso_permitido(self):
        """Test: Usuario con permiso puede cambiar estado"""
        self.client.force_authenticate(user=self.user_con_permisos)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/cambiar_estado/',
            {'estado': 'MANTENIMIENTO'}
        )
        self.assertEqual(response.status_code, 200)

    def test_cambiar_estado_staff_permitido(self):
        """Test: Usuario staff puede cambiar estado"""
        self.client.force_authenticate(user=self.user_staff)
        response = self.client.post(
            f'/api/v1/activos/activos/{self.activo.id}/cambiar_estado/',
            {'estado': 'MANTENIMIENTO'}
        )
        self.assertEqual(response.status_code, 200)

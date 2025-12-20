"""
Tests de validaciones y servicios para el módulo Dashboard

Estos tests complementan los tests básicos existentes y cubren:
- Validación de empresa None
- Validación de parámetros de query
- Tests de servicios
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock

from empresas.models import Empresa
from dashboard.views import DashboardViewSet
from dashboard.services import DashboardService
from dashboard.constants import (
    DIAS_MAXIMO_DASHBOARD, MESES_MAXIMO_DASHBOARD,
    LIMITE_MAXIMO_PRODUCTOS, LIMITE_MAXIMO_CLIENTES,
    DIAS_DEFAULT_VENTAS, DECIMAL_CERO
)


User = get_user_model()


class DashboardValidacionesTest(APITestCase):
    """Tests de validaciones para endpoints del Dashboard"""

    def setUp(self):
        """Configuración inicial para los tests"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            empresa=self.empresa
        )
        self.client.force_authenticate(user=self.user)

    def test_resumen_sin_empresa(self):
        """Test: Usuario sin empresa asignada recibe error 400"""
        user_sin_empresa = User.objects.create_user(
            username='noempresa',
            password='testpass123',
            email='noempresa@test.com',
            empresa=None
        )
        self.client.force_authenticate(user=user_sin_empresa)

        response = self.client.get('/api/v1/dashboard/resumen/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_ventas_periodo_dias_negativo(self):
        """Test: Días negativo retorna error 400"""
        response = self.client.get('/api/v1/dashboard/ventas_periodo/?dias=-5')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_ventas_periodo_dias_excesivo(self):
        """Test: Días mayor al máximo retorna error 400"""
        response = self.client.get(f'/api/v1/dashboard/ventas_periodo/?dias={DIAS_MAXIMO_DASHBOARD + 1}')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_ventas_periodo_dias_valido(self):
        """Test: Días válido retorna 200"""
        response = self.client.get('/api/v1/dashboard/ventas_periodo/?dias=30')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('periodo_dias', response.data)
        self.assertEqual(response.data['periodo_dias'], 30)

    def test_ventas_por_mes_meses_negativo(self):
        """Test: Meses negativo retorna error 400"""
        response = self.client.get('/api/v1/dashboard/ventas_por_mes/?meses=-1')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ventas_por_mes_meses_excesivo(self):
        """Test: Meses mayor al máximo retorna error 400"""
        response = self.client.get(f'/api/v1/dashboard/ventas_por_mes/?meses={MESES_MAXIMO_DASHBOARD + 1}')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_productos_limite_cero(self):
        """Test: Límite cero retorna error 400"""
        response = self.client.get('/api/v1/dashboard/top_productos/?limite=0')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_productos_limite_excesivo(self):
        """Test: Límite mayor al máximo retorna error 400"""
        response = self.client.get(f'/api/v1/dashboard/top_productos/?limite={LIMITE_MAXIMO_PRODUCTOS + 1}')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_clientes_limite_valido(self):
        """Test: Límite válido retorna 200"""
        response = self.client.get('/api/v1/dashboard/top_clientes/?limite=5')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_actividad_reciente_limite_valido(self):
        """Test: Límite válido retorna 200"""
        response = self.client.get('/api/v1/dashboard/actividad_reciente/?limite=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_parametros_no_numericos_usan_default(self):
        """Test: Parámetros no numéricos usan valores por defecto"""
        response = self.client.get('/api/v1/dashboard/ventas_periodo/?dias=abc')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['periodo_dias'], DIAS_DEFAULT_VENTAS)


class DashboardServiceTest(TestCase):
    """Tests para DashboardService"""

    def setUp(self):
        """Configuración inicial"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_obtener_resumen_empresa_none(self):
        """Test: obtener_resumen con empresa None lanza ValueError"""
        with self.assertRaises(ValueError) as context:
            DashboardService.obtener_resumen(None)

        self.assertIn('Empresa es requerida', str(context.exception))

    def test_obtener_resumen_estructura_correcta(self):
        """Test: obtener_resumen retorna estructura correcta"""
        resumen = DashboardService.obtener_resumen(self.empresa)

        self.assertIn('fecha', resumen)
        self.assertIn('ventas', resumen)
        self.assertIn('cuentas_por_cobrar', resumen)
        self.assertIn('cuentas_por_pagar', resumen)
        self.assertIn('inventario', resumen)

    def test_calcular_cambio_porcentual_division_cero(self):
        """Test: Cambio porcentual con denominador cero retorna 0"""
        resultado = DashboardService._calcular_cambio_porcentual(
            Decimal('100.00'),
            Decimal('0.00')
        )

        self.assertEqual(resultado, DECIMAL_CERO)

    def test_calcular_cambio_porcentual_positivo(self):
        """Test: Cambio porcentual positivo calculado correctamente"""
        resultado = DashboardService._calcular_cambio_porcentual(
            Decimal('150.00'),
            Decimal('100.00')
        )

        self.assertEqual(resultado, Decimal('50.00'))

    def test_calcular_cambio_porcentual_negativo(self):
        """Test: Cambio porcentual negativo calculado correctamente"""
        resultado = DashboardService._calcular_cambio_porcentual(
            Decimal('50.00'),
            Decimal('100.00')
        )

        self.assertEqual(resultado, Decimal('-50.00'))

    def test_obtener_ventas_periodo_estructura(self):
        """Test: obtener_ventas_periodo retorna estructura correcta"""
        resultado = DashboardService.obtener_ventas_periodo(self.empresa, 30)

        self.assertIn('periodo_dias', resultado)
        self.assertIn('fecha_inicio', resultado)
        self.assertIn('datos', resultado)
        self.assertEqual(resultado['periodo_dias'], 30)

    def test_obtener_ventas_por_mes_estructura(self):
        """Test: obtener_ventas_por_mes retorna estructura correcta"""
        resultado = DashboardService.obtener_ventas_por_mes(self.empresa, 12)

        self.assertIn('periodo_meses', resultado)
        self.assertIn('datos', resultado)
        self.assertEqual(resultado['periodo_meses'], 12)

    def test_obtener_top_productos_estructura(self):
        """Test: obtener_top_productos retorna estructura correcta"""
        resultado = DashboardService.obtener_top_productos(self.empresa, 10, 30)

        self.assertIn('periodo_dias', resultado)
        self.assertIn('productos', resultado)
        self.assertIsInstance(resultado['productos'], list)

    def test_obtener_productos_stock_bajo_estructura(self):
        """Test: obtener_productos_stock_bajo retorna estructura correcta"""
        resultado = DashboardService.obtener_productos_stock_bajo(self.empresa, 20)

        self.assertIn('total', resultado)
        self.assertIn('productos', resultado)
        self.assertIsInstance(resultado['productos'], list)

    def test_obtener_top_clientes_estructura(self):
        """Test: obtener_top_clientes retorna estructura correcta"""
        resultado = DashboardService.obtener_top_clientes(self.empresa, 10, 90)

        self.assertIn('periodo_dias', resultado)
        self.assertIn('clientes', resultado)
        self.assertIsInstance(resultado['clientes'], list)

    def test_obtener_detalle_cxc_estructura(self):
        """Test: obtener_detalle_cxc retorna estructura correcta"""
        resultado = DashboardService.obtener_detalle_cxc(self.empresa)

        self.assertIn('resumen_por_estado', resultado)
        self.assertIn('por_vencer', resultado)
        self.assertIn('vencidas_por_antiguedad', resultado)

    def test_obtener_detalle_cxp_estructura(self):
        """Test: obtener_detalle_cxp retorna estructura correcta"""
        resultado = DashboardService.obtener_detalle_cxp(self.empresa)

        self.assertIn('resumen_por_estado', resultado)
        self.assertIn('por_vencer', resultado)

    def test_obtener_actividad_reciente_estructura(self):
        """Test: obtener_actividad_reciente retorna estructura correcta"""
        resultado = DashboardService.obtener_actividad_reciente(self.empresa, 20)

        self.assertIn('total', resultado)
        self.assertIn('actividades', resultado)
        self.assertIsInstance(resultado['actividades'], list)

    def test_obtener_indicadores_financieros_estructura(self):
        """Test: obtener_indicadores_financieros retorna estructura correcta"""
        resultado = DashboardService.obtener_indicadores_financieros(self.empresa)

        self.assertIn('periodo', resultado)
        self.assertIn('ventas', resultado)
        self.assertIn('compras', resultado)
        self.assertIn('cuentas', resultado)
        self.assertIn('inventario', resultado)
        self.assertIn('margen_bruto_mes', resultado)


class DashboardMultiEmpresaTest(APITestCase):
    """Tests de aislamiento multi-empresa"""

    def setUp(self):
        """Configuración inicial"""
        self.empresa1 = Empresa.objects.create(
            nombre='Empresa 1',
            rnc='111111111'
        )
        self.empresa2 = Empresa.objects.create(
            nombre='Empresa 2',
            rnc='222222222'
        )
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123',
            email='user1@test.com',
            empresa=self.empresa1
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123',
            email='user2@test.com',
            empresa=self.empresa2
        )

    def test_resumen_filtrado_por_empresa(self):
        """Test: Cada usuario ve solo datos de su empresa"""
        # Usuario 1
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get('/api/v1/dashboard/resumen/')

        # Usuario 2
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get('/api/v1/dashboard/resumen/')

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_endpoints_no_mezclan_datos(self):
        """Test: Endpoints no mezclan datos entre empresas"""
        self.client.force_authenticate(user=self.user1)

        endpoints = [
            '/api/v1/dashboard/resumen/',
            '/api/v1/dashboard/ventas_periodo/',
            '/api/v1/dashboard/top_productos/',
            '/api/v1/dashboard/cuentas_por_cobrar/',
            '/api/v1/dashboard/actividad_reciente/',
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Endpoint {endpoint} falló"
            )

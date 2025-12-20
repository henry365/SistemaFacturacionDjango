"""
Tests de validaciones y servicios para Cuentas por Cobrar
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import CuentaPorCobrar, CobroCliente, DetalleCobroCliente
from .services import CuentaPorCobrarService, CobroClienteService
from empresas.models import Empresa
from clientes.models import Cliente
from ventas.models import Factura

User = get_user_model()


# ========== TESTS DE VALIDACIONES ==========

class CuentaPorCobrarValidationTest(TestCase):
    """Tests para validaciones del modelo CuentaPorCobrar"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.otra_empresa = Empresa.objects.create(nombre='Otra Empresa', rnc='111111111')
        self.user = User.objects.create_user(
            username='testval',
            password='testpass',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.cliente_otra = Cliente.objects.create(
            nombre='Cliente Otra',
            tipo_identificacion='RNC',
            numero_identificacion='222222222',
            empresa=self.otra_empresa
        )
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            usuario=self.user,
            fecha=date.today(),
            numero_factura='FAC-VAL-001',
            total=Decimal('1000.00')
        )

    def test_validacion_cliente_otra_empresa(self):
        """Test: Validar que cliente debe pertenecer a la misma empresa"""
        cxc = CuentaPorCobrar(
            empresa=self.empresa,
            cliente=self.cliente_otra,
            factura=self.factura,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxc.full_clean()
        self.assertIn('cliente', context.exception.message_dict)

    def test_validacion_monto_original_negativo(self):
        """Test: Validar que monto original no puede ser negativo"""
        cxc = CuentaPorCobrar(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-002',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxc.full_clean()
        self.assertIn('monto_original', context.exception.message_dict)

    def test_validacion_fecha_vencimiento_anterior_documento(self):
        """Test: Validar que fecha vencimiento no sea anterior a fecha documento"""
        cxc = CuentaPorCobrar(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-003',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() - timedelta(days=10),
            monto_original=Decimal('1000.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxc.full_clean()
        self.assertIn('fecha_vencimiento', context.exception.message_dict)

    def test_validacion_monto_cobrado_excede_original(self):
        """Test: Validar que monto cobrado no exceda monto original"""
        cxc = CuentaPorCobrar(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-004',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('1500.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxc.full_clean()
        self.assertIn('monto_cobrado', context.exception.message_dict)


class CobroClienteValidationTest(TestCase):
    """Tests para validaciones del modelo CobroCliente"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.otra_empresa = Empresa.objects.create(nombre='Otra Empresa', rnc='111111111')
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.cliente_otra = Cliente.objects.create(
            nombre='Cliente Otra',
            tipo_identificacion='RNC',
            numero_identificacion='222222222',
            empresa=self.otra_empresa
        )

    def test_validacion_cliente_otra_empresa(self):
        """Test: Validar que cliente debe pertenecer a la misma empresa"""
        cobro = CobroCliente(
            empresa=self.empresa,
            cliente=self.cliente_otra,
            numero_recibo='REC-VAL-001',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        with self.assertRaises(ValidationError) as context:
            cobro.full_clean()
        self.assertIn('cliente', context.exception.message_dict)

    def test_validacion_monto_cero(self):
        """Test: Validar que monto debe ser mayor a cero"""
        cobro = CobroCliente(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-VAL-002',
            fecha_cobro=date.today(),
            monto=Decimal('0.00'),
            metodo_pago='EFECTIVO'
        )
        with self.assertRaises(ValidationError) as context:
            cobro.full_clean()
        self.assertIn('monto', context.exception.message_dict)

    def test_validacion_transferencia_sin_referencia(self):
        """Test: Validar que transferencia requiere referencia"""
        cobro = CobroCliente(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-VAL-003',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='TRANSFERENCIA',
            referencia=''
        )
        with self.assertRaises(ValidationError) as context:
            cobro.full_clean()
        self.assertIn('referencia', context.exception.message_dict)

    def test_validacion_cheque_sin_referencia(self):
        """Test: Validar que cheque requiere referencia"""
        cobro = CobroCliente(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-VAL-004',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='CHEQUE',
            referencia=None
        )
        with self.assertRaises(ValidationError) as context:
            cobro.full_clean()
        self.assertIn('referencia', context.exception.message_dict)


# ========== TESTS DE SERVICIOS ==========

class CuentaPorCobrarServiceTest(TestCase):
    """Tests para CuentaPorCobrarService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.user = User.objects.create_user(
            username='testservice',
            password='testpass',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            usuario=self.user,
            fecha=date.today(),
            numero_factura='FAC-SVC-001',
            total=Decimal('1000.00')
        )

    def test_actualizar_estado_a_cobrada(self):
        """Test: Servicio actualiza estado a COBRADA cuando monto_pendiente = 0"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('1000.00')
        )
        nuevo_estado = CuentaPorCobrarService.actualizar_estado(cxc)
        self.assertEqual(nuevo_estado, 'COBRADA')

    def test_actualizar_estado_a_parcial(self):
        """Test: Servicio actualiza estado a PARCIAL con cobro parcial"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('300.00')
        )
        nuevo_estado = CuentaPorCobrarService.actualizar_estado(cxc)
        self.assertEqual(nuevo_estado, 'PARCIAL')

    def test_anular_cxc_sin_cobros(self):
        """Test: Servicio anula CxC sin cobros"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        cxc_anulada = CuentaPorCobrarService.anular(cxc, self.user, 'Test anulacion')
        self.assertEqual(cxc_anulada.estado, 'ANULADA')

    def test_anular_cxc_con_cobros_falla(self):
        """Test: Servicio no anula CxC con cobros aplicados"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_cobrado=Decimal('100.00')
        )
        with self.assertRaises(ValidationError):
            CuentaPorCobrarService.anular(cxc, self.user, 'Test')

    def test_anular_idempotencia(self):
        """Test: Anular es idempotente (no falla si ya esta anulada)"""
        cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            estado='ANULADA'
        )
        cxc_anulada = CuentaPorCobrarService.anular(cxc, self.user, 'Test')
        self.assertEqual(cxc_anulada.estado, 'ANULADA')

    def test_resumen_por_cliente(self):
        """Test: Servicio obtiene resumen por cliente"""
        CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        resumen = CuentaPorCobrarService.resumen_por_cliente(self.empresa)
        self.assertTrue(len(resumen) >= 1)
        self.assertEqual(resumen[0]['cliente__nombre'], 'Cliente Test')


class CobroClienteServiceTest(TestCase):
    """Tests para CobroClienteService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.user = User.objects.create_user(
            username='testservice2',
            password='testpass',
            empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            usuario=self.user,
            fecha=date.today(),
            numero_factura='FAC-COB-001',
            total=Decimal('1000.00')
        )
        self.cxc = CuentaPorCobrar.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            factura=self.factura,
            numero_documento='FAC-COB-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        self.cobro = CobroCliente.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            numero_recibo='REC-SVC-001',
            fecha_cobro=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

    def test_aplicar_cobro_exitoso(self):
        """Test: Servicio aplica cobro correctamente"""
        detalles = [{'cuenta_por_cobrar_id': self.cxc.id, 'monto_aplicado': '500.00'}]
        cobro = CobroClienteService.aplicar_cobro(self.cobro, detalles, self.user)
        self.cxc.refresh_from_db()
        self.assertEqual(self.cxc.monto_cobrado, Decimal('500.00'))
        self.assertEqual(self.cxc.estado, 'PARCIAL')

    def test_aplicar_cobro_excede_monto_cobro(self):
        """Test: Servicio rechaza si monto excede el cobro"""
        detalles = [{'cuenta_por_cobrar_id': self.cxc.id, 'monto_aplicado': '600.00'}]
        with self.assertRaises(ValidationError):
            CobroClienteService.aplicar_cobro(self.cobro, detalles, self.user)

    def test_obtener_monto_disponible(self):
        """Test: Servicio calcula monto disponible"""
        monto = CobroClienteService.obtener_monto_disponible(self.cobro)
        self.assertEqual(monto, Decimal('500.00'))

    def test_obtener_monto_disponible_con_detalles(self):
        """Test: Servicio calcula monto disponible con cobros aplicados"""
        DetalleCobroCliente.objects.create(
            cobro=self.cobro,
            cuenta_por_cobrar=self.cxc,
            monto_aplicado=Decimal('200.00'),
            empresa=self.empresa
        )
        monto = CobroClienteService.obtener_monto_disponible(self.cobro)
        self.assertEqual(monto, Decimal('300.00'))

    def test_reversar_cobro(self):
        """Test: Servicio reversa cobro correctamente"""
        # Aplicar cobro primero
        detalles = [{'cuenta_por_cobrar_id': self.cxc.id, 'monto_aplicado': '500.00'}]
        CobroClienteService.aplicar_cobro(self.cobro, detalles, self.user)
        self.cxc.refresh_from_db()
        self.assertEqual(self.cxc.monto_cobrado, Decimal('500.00'))

        # Reversar
        CobroClienteService.reversar_cobro(self.cobro, self.user, 'Test reversion')
        self.cxc.refresh_from_db()
        self.assertEqual(self.cxc.monto_cobrado, Decimal('0.00'))
        self.assertEqual(self.cxc.estado, 'PENDIENTE')

    def test_validar_referencia_transferencia(self):
        """Test: Validar referencia para transferencia"""
        self.assertTrue(CobroClienteService.validar_referencia('TRANSFERENCIA', 'REF-123'))
        self.assertFalse(CobroClienteService.validar_referencia('TRANSFERENCIA', ''))
        self.assertFalse(CobroClienteService.validar_referencia('TRANSFERENCIA', None))

    def test_validar_referencia_efectivo(self):
        """Test: Validar referencia para efectivo (no requerida)"""
        self.assertTrue(CobroClienteService.validar_referencia('EFECTIVO', ''))
        self.assertTrue(CobroClienteService.validar_referencia('EFECTIVO', None))

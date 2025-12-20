"""
Tests de validaciones y servicios para Cuentas por Pagar
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import CuentaPorPagar, PagoProveedor, DetallePagoProveedor
from .services import CuentaPorPagarService, PagoProveedorService
from empresas.models import Empresa
from proveedores.models import Proveedor
from compras.models import Compra

User = get_user_model()


# ========== TESTS DE VALIDACIONES ==========

class CuentaPorPagarValidationTest(TestCase):
    """Tests para validaciones del modelo CuentaPorPagar"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.otra_empresa = Empresa.objects.create(nombre='Otra Empresa', rnc='111111111')
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.proveedor_otra = Proveedor.objects.create(
            nombre='Proveedor Otra',
            tipo_identificacion='RNC',
            numero_identificacion='222222222',
            empresa=self.otra_empresa
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-VAL-001',
            total=Decimal('1000.00')
        )

    def test_validacion_proveedor_otra_empresa(self):
        """Test: Validar que proveedor debe pertenecer a la misma empresa"""
        cxp = CuentaPorPagar(
            empresa=self.empresa,
            proveedor=self.proveedor_otra,
            compra=self.compra,
            numero_documento='FAC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxp.full_clean()
        self.assertIn('proveedor', context.exception.message_dict)

    def test_validacion_monto_original_negativo(self):
        """Test: Validar que monto original no puede ser negativo"""
        cxp = CuentaPorPagar(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-002',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxp.full_clean()
        self.assertIn('monto_original', context.exception.message_dict)

    def test_validacion_fecha_vencimiento_anterior_documento(self):
        """Test: Validar que fecha vencimiento no sea anterior a fecha documento"""
        cxp = CuentaPorPagar(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-003',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() - timedelta(days=10),
            monto_original=Decimal('1000.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxp.full_clean()
        self.assertIn('fecha_vencimiento', context.exception.message_dict)

    def test_validacion_monto_pagado_excede_original(self):
        """Test: Validar que monto pagado no exceda monto original"""
        cxp = CuentaPorPagar(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-004',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('1500.00')
        )
        with self.assertRaises(ValidationError) as context:
            cxp.full_clean()
        self.assertIn('monto_pagado', context.exception.message_dict)


class PagoProveedorValidationTest(TestCase):
    """Tests para validaciones del modelo PagoProveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.otra_empresa = Empresa.objects.create(nombre='Otra Empresa', rnc='111111111')
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.proveedor_otra = Proveedor.objects.create(
            nombre='Proveedor Otra',
            tipo_identificacion='RNC',
            numero_identificacion='222222222',
            empresa=self.otra_empresa
        )

    def test_validacion_proveedor_otra_empresa(self):
        """Test: Validar que proveedor debe pertenecer a la misma empresa"""
        pago = PagoProveedor(
            empresa=self.empresa,
            proveedor=self.proveedor_otra,
            numero_pago='PAG-VAL-001',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )
        with self.assertRaises(ValidationError) as context:
            pago.full_clean()
        self.assertIn('proveedor', context.exception.message_dict)

    def test_validacion_monto_cero(self):
        """Test: Validar que monto debe ser mayor a cero"""
        pago = PagoProveedor(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-VAL-002',
            fecha_pago=date.today(),
            monto=Decimal('0.00'),
            metodo_pago='EFECTIVO'
        )
        with self.assertRaises(ValidationError) as context:
            pago.full_clean()
        self.assertIn('monto', context.exception.message_dict)

    def test_validacion_transferencia_sin_referencia(self):
        """Test: Validar que transferencia requiere referencia"""
        pago = PagoProveedor(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-VAL-003',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='TRANSFERENCIA',
            referencia=''
        )
        with self.assertRaises(ValidationError) as context:
            pago.full_clean()
        self.assertIn('referencia', context.exception.message_dict)

    def test_validacion_cheque_sin_referencia(self):
        """Test: Validar que cheque requiere referencia"""
        pago = PagoProveedor(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-VAL-004',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='CHEQUE',
            referencia=None
        )
        with self.assertRaises(ValidationError) as context:
            pago.full_clean()
        self.assertIn('referencia', context.exception.message_dict)


# ========== TESTS DE SERVICIOS ==========

class CuentaPorPagarServiceTest(TestCase):
    """Tests para CuentaPorPagarService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.user = User.objects.create_user(
            username='testservice',
            password='testpass',
            empresa=self.empresa
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-SVC-001',
            total=Decimal('1000.00')
        )

    def test_actualizar_estado_a_pagada(self):
        """Test: Servicio actualiza estado a PAGADA cuando monto_pendiente = 0"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('1000.00')
        )
        nuevo_estado = CuentaPorPagarService.actualizar_estado(cxp)
        self.assertEqual(nuevo_estado, 'PAGADA')

    def test_actualizar_estado_a_parcial(self):
        """Test: Servicio actualiza estado a PARCIAL con pago parcial"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('300.00')
        )
        nuevo_estado = CuentaPorPagarService.actualizar_estado(cxp)
        self.assertEqual(nuevo_estado, 'PARCIAL')

    def test_anular_cxp_sin_pagos(self):
        """Test: Servicio anula CxP sin pagos"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        cxp_anulada = CuentaPorPagarService.anular(cxp, self.user, 'Test anulacion')
        self.assertEqual(cxp_anulada.estado, 'ANULADA')

    def test_anular_cxp_con_pagos_falla(self):
        """Test: Servicio no anula CxP con pagos aplicados"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            monto_pagado=Decimal('100.00')
        )
        with self.assertRaises(ValidationError):
            CuentaPorPagarService.anular(cxp, self.user, 'Test')

    def test_anular_idempotencia(self):
        """Test: Anular es idempotente (no falla si ya esta anulada)"""
        cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00'),
            estado='ANULADA'
        )
        cxp_anulada = CuentaPorPagarService.anular(cxp, self.user, 'Test')
        self.assertEqual(cxp_anulada.estado, 'ANULADA')

    def test_resumen_por_proveedor(self):
        """Test: Servicio obtiene resumen por proveedor"""
        CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-SVC-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        resumen = CuentaPorPagarService.resumen_por_proveedor(self.empresa)
        self.assertTrue(len(resumen) >= 1)
        self.assertEqual(resumen[0]['proveedor__nombre'], 'Proveedor Test')


class PagoProveedorServiceTest(TestCase):
    """Tests para PagoProveedorService"""

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test', rnc='123456789')
        self.user = User.objects.create_user(
            username='testservice2',
            password='testpass',
            empresa=self.empresa
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            tipo_identificacion='RNC',
            numero_identificacion='987654321',
            empresa=self.empresa
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-PAG-001',
            total=Decimal('1000.00')
        )
        self.cxp = CuentaPorPagar.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            compra=self.compra,
            numero_documento='FAC-PAG-001',
            fecha_documento=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_original=Decimal('1000.00')
        )
        self.pago = PagoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            numero_pago='PAG-SVC-001',
            fecha_pago=date.today(),
            monto=Decimal('500.00'),
            metodo_pago='EFECTIVO'
        )

    def test_aplicar_pago_exitoso(self):
        """Test: Servicio aplica pago correctamente"""
        detalles = [{'cuenta_por_pagar_id': self.cxp.id, 'monto_aplicado': '500.00'}]
        pago = PagoProveedorService.aplicar_pago(self.pago, detalles, self.user)
        self.cxp.refresh_from_db()
        self.assertEqual(self.cxp.monto_pagado, Decimal('500.00'))
        self.assertEqual(self.cxp.estado, 'PARCIAL')

    def test_aplicar_pago_excede_monto_pago(self):
        """Test: Servicio rechaza si monto excede el pago"""
        detalles = [{'cuenta_por_pagar_id': self.cxp.id, 'monto_aplicado': '600.00'}]
        with self.assertRaises(ValidationError):
            PagoProveedorService.aplicar_pago(self.pago, detalles, self.user)

    def test_obtener_monto_disponible(self):
        """Test: Servicio calcula monto disponible"""
        monto = PagoProveedorService.obtener_monto_disponible(self.pago)
        self.assertEqual(monto, Decimal('500.00'))

    def test_obtener_monto_disponible_con_detalles(self):
        """Test: Servicio calcula monto disponible con pagos aplicados"""
        DetallePagoProveedor.objects.create(
            pago=self.pago,
            cuenta_por_pagar=self.cxp,
            monto_aplicado=Decimal('200.00'),
            empresa=self.empresa
        )
        monto = PagoProveedorService.obtener_monto_disponible(self.pago)
        self.assertEqual(monto, Decimal('300.00'))

    def test_reversar_pago(self):
        """Test: Servicio reversa pago correctamente"""
        # Aplicar pago primero
        detalles = [{'cuenta_por_pagar_id': self.cxp.id, 'monto_aplicado': '500.00'}]
        PagoProveedorService.aplicar_pago(self.pago, detalles, self.user)
        self.cxp.refresh_from_db()
        self.assertEqual(self.cxp.monto_pagado, Decimal('500.00'))

        # Reversar
        PagoProveedorService.reversar_pago(self.pago, self.user, 'Test reversion')
        self.cxp.refresh_from_db()
        self.assertEqual(self.cxp.monto_pagado, Decimal('0.00'))
        self.assertEqual(self.cxp.estado, 'PENDIENTE')

    def test_validar_referencia_transferencia(self):
        """Test: Validar referencia para transferencia"""
        self.assertTrue(PagoProveedorService.validar_referencia('TRANSFERENCIA', 'REF-123'))
        self.assertFalse(PagoProveedorService.validar_referencia('TRANSFERENCIA', ''))
        self.assertFalse(PagoProveedorService.validar_referencia('TRANSFERENCIA', None))

    def test_validar_referencia_efectivo(self):
        """Test: Validar referencia para efectivo (no requerida)"""
        self.assertTrue(PagoProveedorService.validar_referencia('EFECTIVO', ''))
        self.assertTrue(PagoProveedorService.validar_referencia('EFECTIVO', None))

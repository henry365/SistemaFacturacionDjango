"""
Tests para el servicio GeneradorReportesDGII.

Estos tests verifican la generación correcta de los reportes fiscales:
- 606: Compras de bienes y servicios
- 607: Ventas de bienes y servicios
- 608: Comprobantes fiscales anulados
"""
from django.test import TestCase
from decimal import Decimal
from datetime import date

from .services import GeneradorReportesDGII, _get_tipo_identificacion
from empresas.models import Empresa
from proveedores.models import Proveedor
from clientes.models import Cliente
from productos.models import Producto
from compras.models import Compra, DetalleCompra
from ventas.models import Factura
from usuarios.models import User


class TipoIdentificacionTest(TestCase):
    """Tests para la función auxiliar _get_tipo_identificacion"""

    def test_rnc_9_digitos(self):
        """Test: RNC de 9 dígitos retorna '1'"""
        self.assertEqual(_get_tipo_identificacion('123456789'), '1')

    def test_cedula_11_digitos(self):
        """Test: Cédula de 11 dígitos retorna '2'"""
        self.assertEqual(_get_tipo_identificacion('00123456789'), '2')

    def test_otro_formato(self):
        """Test: Otro formato retorna '3'"""
        self.assertEqual(_get_tipo_identificacion('12345'), '3')

    def test_valor_none(self):
        """Test: None retorna '3'"""
        self.assertEqual(_get_tipo_identificacion(None), '3')

    def test_valor_vacio(self):
        """Test: String vacío retorna '3'"""
        self.assertEqual(_get_tipo_identificacion(''), '3')

    def test_con_guiones(self):
        """Test: RNC con guiones se procesa correctamente"""
        self.assertEqual(_get_tipo_identificacion('123-456-789'), '1')

    def test_con_espacios(self):
        """Test: Cédula con espacios se procesa correctamente"""
        self.assertEqual(_get_tipo_identificacion('001 2345 6789'), '2')


class GeneradorReportesDGIITest(TestCase):
    """Tests para GeneradorReportesDGII"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test DGII',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor DGII Test',
            numero_identificacion='111222333'
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre='Cliente DGII Test',
            numero_identificacion='444555666',
            tipo_identificacion='RNC',
            limite_credito=Decimal('100000.00')  # Permite ventas a crédito en tests
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-DGII',
            nombre='Producto DGII Test',
            precio_venta_base=Decimal('100.00')
        )

    def _crear_compra(self, estado='REGISTRADA', ncf='B0100000001'):
        """Helper para crear compras de prueba"""
        return Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor=f'FAC-{Compra.objects.count() + 1}',
            numero_ncf=ncf,
            tipo_gasto='02',
            total=Decimal('5000.00'),
            impuestos=Decimal('900.00'),
            estado=estado
        )

    def _crear_factura(self, estado='PAGADA', ncf='B0100000001'):
        """Helper para crear facturas de prueba"""
        return Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            ncf=ncf,
            numero_factura=f'FAC-{Factura.objects.count() + 1}',
            total=Decimal('3000.00'),
            itbis=Decimal('540.00'),
            estado=estado,
            tipo_venta='CONTADO',
            venta_sin_comprobante=False,
            usuario=self.user
        )


class Generar606Test(GeneradorReportesDGIITest):
    """Tests específicos para generar_606"""

    def test_generar_606_basico(self):
        """Test: Generar reporte 606 con compras"""
        self._crear_compra()

        mes = date.today().month
        anio = date.today().year

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=anio,
            mes=mes
        )

        self.assertEqual(resultado['status'], 'completed')
        self.assertEqual(resultado['cantidad_registros'], 1)
        self.assertIn('registros', resultado)
        self.assertIn('totales', resultado)
        self.assertIn('contenido_txt', resultado)

    def test_generar_606_campos_requeridos(self):
        """Test: Registro 606 contiene todos los campos requeridos"""
        self._crear_compra()

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        registro = resultado['registros'][0]

        # Verificar campos obligatorios
        self.assertIn('rnc_cedula', registro)
        self.assertIn('tipo_identificacion', registro)
        self.assertIn('ncf', registro)
        self.assertIn('fecha_comprobante', registro)
        self.assertIn('monto_facturado', registro)
        self.assertIn('itbis_facturado', registro)

    def test_generar_606_formato_fecha(self):
        """Test: Fecha en formato YYYYMMDD"""
        self._crear_compra()

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        fecha = resultado['registros'][0]['fecha_comprobante']
        self.assertEqual(len(fecha), 8)
        self.assertTrue(fecha.isdigit())

    def test_generar_606_solo_estados_validos(self):
        """Test: Solo incluye compras en estados válidos"""
        self._crear_compra(estado='REGISTRADA')
        self._crear_compra(estado='CXP', ncf='B0100000002')
        self._crear_compra(estado='ANULADA', ncf='B0100000003')

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        # ANULADA no se incluye
        self.assertEqual(resultado['cantidad_registros'], 2)

    def test_generar_606_totales(self):
        """Test: Calcula totales correctamente"""
        self._crear_compra()
        self._crear_compra(ncf='B0100000002')

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        # 2 compras de 5000 cada una = 10000
        self.assertEqual(
            Decimal(resultado['totales']['monto_facturado']),
            Decimal('10000.00')
        )

    def test_generar_606_sin_registros(self):
        """Test: Maneja período sin compras"""
        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=2020,
            mes=1
        )

        self.assertEqual(resultado['cantidad_registros'], 0)
        self.assertEqual(len(resultado['registros']), 0)

    def test_generar_606_nombre_archivo(self):
        """Test: Nombre de archivo correcto"""
        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=2024,
            mes=12
        )

        self.assertEqual(
            resultado['nombre_archivo'],
            f'606_{self.empresa.rnc}_202412.txt'
        )


class Generar607Test(GeneradorReportesDGIITest):
    """Tests específicos para generar_607"""

    def test_generar_607_basico(self):
        """Test: Generar reporte 607 con ventas"""
        self._crear_factura()

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        self.assertEqual(resultado['status'], 'completed')
        self.assertEqual(resultado['cantidad_registros'], 1)
        self.assertIn('registros', resultado)
        self.assertIn('totales', resultado)

    def test_generar_607_campos_requeridos(self):
        """Test: Registro 607 contiene todos los campos requeridos"""
        self._crear_factura()

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        registro = resultado['registros'][0]

        self.assertIn('rnc_cedula', registro)
        self.assertIn('tipo_identificacion', registro)
        self.assertIn('ncf', registro)
        self.assertIn('tipo_ingreso', registro)
        self.assertIn('monto_facturado', registro)
        self.assertIn('itbis_facturado', registro)

    def test_generar_607_venta_contado(self):
        """Test: Venta de contado se registra en campo efectivo"""
        self._crear_factura(estado='PAGADA')

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        registro = resultado['registros'][0]
        self.assertEqual(registro['efectivo'], '3000.00')
        self.assertEqual(registro['venta_credito'], '0')

    def test_generar_607_venta_credito(self):
        """Test: Venta a crédito se registra correctamente"""
        factura = self._crear_factura()
        factura.tipo_venta = 'CREDITO'
        factura.save()

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        registro = resultado['registros'][0]
        self.assertEqual(registro['venta_credito'], '3000.00')
        self.assertEqual(registro['efectivo'], '0')

    def test_generar_607_excluye_sin_comprobante(self):
        """Test: Excluye ventas sin comprobante fiscal"""
        factura = self._crear_factura()
        factura.venta_sin_comprobante = True
        factura.save()

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        self.assertEqual(resultado['cantidad_registros'], 0)

    def test_generar_607_solo_estados_validos(self):
        """Test: Solo incluye facturas en estados válidos"""
        self._crear_factura(estado='PAGADA')
        self._crear_factura(estado='PENDIENTE_PAGO', ncf='B0100000002')
        self._crear_factura(estado='CANCELADA', ncf='B0100000003')

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        # CANCELADA no se incluye en 607 (va a 608)
        self.assertEqual(resultado['cantidad_registros'], 2)


class Generar608Test(GeneradorReportesDGIITest):
    """Tests específicos para generar_608"""

    def test_generar_608_basico(self):
        """Test: Generar reporte 608 con anulados"""
        self._crear_factura(estado='CANCELADA', ncf='B0100000001')

        resultado = GeneradorReportesDGII.generar_608(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        self.assertEqual(resultado['status'], 'completed')
        self.assertEqual(resultado['cantidad_registros'], 1)

    def test_generar_608_campos(self):
        """Test: Registro 608 contiene campos correctos"""
        self._crear_factura(estado='CANCELADA', ncf='B0100000001')

        resultado = GeneradorReportesDGII.generar_608(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        registro = resultado['registros'][0]

        self.assertIn('ncf', registro)
        self.assertIn('tipo_anulacion', registro)
        self.assertIn('fecha_comprobante', registro)
        self.assertEqual(registro['ncf'], 'B0100000001')

    def test_generar_608_solo_canceladas(self):
        """Test: Solo incluye facturas canceladas"""
        self._crear_factura(estado='PAGADA', ncf='B0100000001')
        self._crear_factura(estado='CANCELADA', ncf='B0100000002')

        resultado = GeneradorReportesDGII.generar_608(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        self.assertEqual(resultado['cantidad_registros'], 1)
        self.assertEqual(resultado['registros'][0]['ncf'], 'B0100000002')

    def test_generar_608_excluye_sin_ncf(self):
        """Test: Excluye facturas canceladas sin NCF"""
        factura = Factura.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            ncf='',
            numero_factura='FAC-SIN-NCF',
            total=Decimal('1000.00'),
            estado='CANCELADA',
            usuario=self.user
        )

        resultado = GeneradorReportesDGII.generar_608(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        self.assertEqual(resultado['cantidad_registros'], 0)


class GenerarTXTTest(GeneradorReportesDGIITest):
    """Tests para la generación del archivo TXT"""

    def test_generar_txt_formato_pipe(self):
        """Test: TXT usa separador pipe"""
        self._crear_compra()

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        contenido = resultado['contenido_txt']
        self.assertIn('|', contenido)

    def test_generar_txt_lineas(self):
        """Test: TXT tiene una línea por registro"""
        self._crear_compra(ncf='B0100000001')
        self._crear_compra(ncf='B0100000002')
        self._crear_compra(ncf='B0100000003')

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        lineas = resultado['contenido_txt'].strip().split('\n')
        self.assertEqual(len(lineas), 3)

    def test_generar_txt_campos_ordenados(self):
        """Test: TXT tiene campos en orden correcto"""
        self._crear_compra()

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        linea = resultado['contenido_txt'].strip().split('\n')[0]
        campos = linea.split('|')

        # El primer campo debe ser el RNC
        self.assertEqual(campos[0], '111222333')

    def test_totales_606_correctos(self):
        """Test: Totales del 606 son correctos"""
        self._crear_compra()
        self._crear_compra(ncf='B0100000002')

        resultado = GeneradorReportesDGII.generar_606(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        totales = resultado['totales']

        # 2 compras de 5000 c/u = 10000
        self.assertEqual(Decimal(totales['monto_facturado']), Decimal('10000.00'))

        # 2 compras con 900 de impuestos c/u = 1800
        self.assertEqual(Decimal(totales['itbis_facturado']), Decimal('1800.00'))

    def test_totales_607_correctos(self):
        """Test: Totales del 607 son correctos"""
        self._crear_factura(ncf='B0100000001')
        self._crear_factura(ncf='B0100000002')

        resultado = GeneradorReportesDGII.generar_607(
            empresa=self.empresa,
            anio=date.today().year,
            mes=date.today().month
        )

        totales = resultado['totales']

        # 2 facturas de 3000 c/u = 6000
        self.assertEqual(Decimal(totales['monto_facturado']), Decimal('6000.00'))

        # 2 facturas con 540 de ITBIS c/u = 1080
        self.assertEqual(Decimal(totales['itbis_facturado']), Decimal('1080.00'))

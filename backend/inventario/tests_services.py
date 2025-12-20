"""
Tests para los servicios de inventario refactorizados.

Estos tests verifican la lógica de negocio de:
- ServicioInventario: Operaciones de stock y movimientos
- ServicioAlertasInventario: Generación de alertas automáticas
- ServicioKardex: Cálculo de Kardex con saldos acumulados
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .services import ServicioInventario, ServicioAlertasInventario, ServicioKardex
from .models import (
    Almacen, InventarioProducto, MovimientoInventario,
    ReservaStock, Lote, AlertaInventario
)
from empresas.models import Empresa
from productos.models import Producto
from usuarios.models import User


class ServicioInventarioTest(TestCase):
    """Tests para ServicioInventario"""

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
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True,
            usuario_creacion=self.user
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE',
            controlar_stock=True
        )
        self.inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('100'),
            costo_promedio=Decimal('50.00'),
            stock_minimo=Decimal('10'),
            stock_maximo=Decimal('500'),
            punto_reorden=Decimal('20')
        )

    def test_puede_realizar_movimiento_entrada(self):
        """Test: Siempre se puede realizar entrada"""
        puede, mensaje = ServicioInventario.puede_realizar_movimiento(
            producto=self.producto,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('50'),
            almacen=self.almacen
        )
        self.assertTrue(puede)
        self.assertIsNone(mensaje)

    def test_puede_realizar_movimiento_salida_con_stock(self):
        """Test: Se puede realizar salida si hay stock suficiente"""
        puede, mensaje = ServicioInventario.puede_realizar_movimiento(
            producto=self.producto,
            tipo_movimiento='SALIDA_VENTA',
            cantidad=Decimal('50'),
            almacen=self.almacen
        )
        self.assertTrue(puede)

    def test_no_puede_realizar_movimiento_sin_stock(self):
        """Test: No se puede realizar salida sin stock suficiente"""
        puede, mensaje = ServicioInventario.puede_realizar_movimiento(
            producto=self.producto,
            tipo_movimiento='SALIDA_VENTA',
            cantidad=Decimal('200'),
            almacen=self.almacen
        )
        self.assertFalse(puede)
        self.assertIn('insuficiente', mensaje)

    def test_servicio_no_tiene_inventario(self):
        """Test: Servicios no tienen inventario"""
        producto_servicio = Producto.objects.create(
            codigo_sku='SERV-001',
            nombre='Servicio Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='SERVICIO',
            controlar_stock=False
        )
        puede, mensaje = ServicioInventario.puede_realizar_movimiento(
            producto=producto_servicio,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('50'),
            almacen=self.almacen
        )
        self.assertFalse(puede)
        self.assertIn('servicios', mensaje.lower())

    def test_registrar_movimiento_entrada(self):
        """Test: Registrar movimiento de entrada aumenta stock"""
        cantidad_inicial = self.inventario.cantidad_disponible

        movimiento = ServicioInventario.registrar_movimiento(
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('50'),
            costo_unitario=Decimal('55.00'),
            usuario=self.user,
            empresa=self.empresa,
            referencia='COMPRA-001'
        )

        self.inventario.refresh_from_db()
        self.assertEqual(
            self.inventario.cantidad_disponible,
            cantidad_inicial + Decimal('50')
        )
        self.assertEqual(movimiento.tipo_movimiento, 'ENTRADA_COMPRA')

    def test_registrar_movimiento_salida(self):
        """Test: Registrar movimiento de salida disminuye stock"""
        cantidad_inicial = self.inventario.cantidad_disponible

        movimiento = ServicioInventario.registrar_movimiento(
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='SALIDA_VENTA',
            cantidad=Decimal('30'),
            costo_unitario=Decimal('50.00'),
            usuario=self.user,
            empresa=self.empresa,
            referencia='FAC-001'
        )

        self.inventario.refresh_from_db()
        self.assertEqual(
            self.inventario.cantidad_disponible,
            cantidad_inicial - Decimal('30')
        )

    def test_registrar_movimiento_sin_stock_falla(self):
        """Test: Registrar salida sin stock falla"""
        with self.assertRaises(ValidationError):
            ServicioInventario.registrar_movimiento(
                producto=self.producto,
                almacen=self.almacen,
                tipo_movimiento='SALIDA_VENTA',
                cantidad=Decimal('500'),
                costo_unitario=Decimal('50.00'),
                usuario=self.user,
                empresa=self.empresa
            )

    def test_registrar_movimiento_actualiza_costo_promedio(self):
        """Test: Entrada de compra actualiza costo promedio"""
        costo_inicial = float(self.inventario.costo_promedio)

        ServicioInventario.registrar_movimiento(
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('100'),
            costo_unitario=Decimal('60.00'),
            usuario=self.user,
            empresa=self.empresa
        )

        self.inventario.refresh_from_db()
        nuevo_costo = float(self.inventario.costo_promedio)

        # El costo promedio debe cambiar después de una entrada con diferente costo
        self.assertNotEqual(costo_inicial, nuevo_costo)
        # El nuevo costo debe estar entre el costo inicial y el costo de la nueva entrada
        self.assertGreater(nuevo_costo, costo_inicial)  # 50 < nuevo
        self.assertLess(nuevo_costo, 60)  # nuevo < 60

    def test_crear_reserva_exitoso(self):
        """Test: Crear reserva de stock"""
        reserva = ServicioInventario.crear_reserva(
            inventario=self.inventario,
            cantidad=Decimal('20'),
            referencia='COTIZACION-001',
            usuario=self.user,
            empresa=self.empresa
        )

        self.assertEqual(reserva.cantidad_reservada, Decimal('20'))
        self.assertEqual(reserva.estado, 'PENDIENTE')

    def test_crear_reserva_sin_stock_falla(self):
        """Test: No se puede reservar más del stock disponible"""
        with self.assertRaises(ValidationError):
            ServicioInventario.crear_reserva(
                inventario=self.inventario,
                cantidad=Decimal('500'),
                referencia='COTIZACION-001',
                usuario=self.user
            )

    def test_confirmar_reserva(self):
        """Test: Confirmar reserva cambia estado"""
        reserva = ServicioInventario.crear_reserva(
            inventario=self.inventario,
            cantidad=Decimal('20'),
            referencia='COTIZACION-001',
            usuario=self.user,
            empresa=self.empresa
        )

        reserva = ServicioInventario.confirmar_reserva(reserva)
        self.assertEqual(reserva.estado, 'CONFIRMADA')

    def test_cancelar_reserva(self):
        """Test: Cancelar reserva cambia estado"""
        reserva = ServicioInventario.crear_reserva(
            inventario=self.inventario,
            cantidad=Decimal('20'),
            referencia='COTIZACION-001',
            usuario=self.user,
            empresa=self.empresa
        )

        reserva = ServicioInventario.cancelar_reserva(reserva)
        self.assertEqual(reserva.estado, 'CANCELADA')


class ServicioAlertasInventarioTest(TestCase):
    """Tests para ServicioAlertasInventario"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            empresa=self.empresa,
            is_active=True
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE',
            activo=True
        )

    def test_verificar_stock_bajo(self):
        """Test: Genera alerta para stock bajo"""
        inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('5'),
            stock_minimo=Decimal('10'),
            punto_reorden=Decimal('20')
        )

        alertas_creadas = ServicioAlertasInventario.verificar_stock_bajo()
        self.assertGreaterEqual(alertas_creadas, 1)

        # Verificar que se creó la alerta
        alerta = AlertaInventario.objects.filter(
            inventario=inventario,
            tipo='STOCK_BAJO'
        ).first()
        self.assertIsNotNone(alerta)

    def test_verificar_stock_agotado(self):
        """Test: Genera alerta CRITICA para stock agotado"""
        inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('0'),
            stock_minimo=Decimal('10')
        )

        ServicioAlertasInventario.verificar_stock_bajo()

        alerta = AlertaInventario.objects.filter(
            inventario=inventario,
            tipo='STOCK_AGOTADO'
        ).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.prioridad, 'CRITICA')

    def test_no_duplica_alertas(self):
        """Test: No crea alertas duplicadas"""
        inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('5'),
            stock_minimo=Decimal('10')
        )

        # Crear alerta inicial
        primera_vez = ServicioAlertasInventario.verificar_stock_bajo()

        # Intentar crear de nuevo
        segunda_vez = ServicioAlertasInventario.verificar_stock_bajo()

        # La segunda vez no debe crear nuevas alertas
        self.assertEqual(segunda_vez, 0)

    def test_verificar_vencimientos(self):
        """Test: Genera alertas para lotes próximos a vencer"""
        lote = Lote.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            codigo_lote='LOTE-001',
            fecha_vencimiento=date.today() + timedelta(days=15),
            cantidad_inicial=Decimal('100'),
            cantidad_disponible=Decimal('50'),
            costo_unitario=Decimal('50.00'),
            estado='DISPONIBLE'
        )

        alertas_creadas = ServicioAlertasInventario.verificar_vencimientos(dias_antes=30)
        self.assertGreaterEqual(alertas_creadas, 1)

        alerta = AlertaInventario.objects.filter(
            lote=lote,
            tipo='VENCIMIENTO_PROXIMO'
        ).first()
        self.assertIsNotNone(alerta)

    def test_verificar_lote_vencido(self):
        """Test: Genera alerta CRITICA para lote vencido"""
        lote = Lote.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            codigo_lote='LOTE-VENCIDO',
            fecha_vencimiento=date.today() - timedelta(days=5),
            cantidad_inicial=Decimal('100'),
            cantidad_disponible=Decimal('50'),
            costo_unitario=Decimal('50.00'),
            estado='DISPONIBLE'
        )

        ServicioAlertasInventario.verificar_vencimientos()

        alerta = AlertaInventario.objects.filter(
            lote=lote,
            tipo='VENCIMIENTO_VENCIDO'
        ).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.prioridad, 'CRITICA')

    def test_verificar_stock_excesivo(self):
        """Test: Genera alerta para stock excesivo"""
        inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('1000'),
            stock_maximo=Decimal('500')
        )

        alertas_creadas = ServicioAlertasInventario.verificar_stock_excesivo()
        self.assertGreaterEqual(alertas_creadas, 1)

        alerta = AlertaInventario.objects.filter(
            inventario=inventario,
            tipo='STOCK_EXCESIVO'
        ).first()
        self.assertIsNotNone(alerta)

    def test_generar_todas_las_alertas(self):
        """Test: Genera todos los tipos de alertas"""
        # Stock bajo
        InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('5'),
            stock_minimo=Decimal('10')
        )

        resultado = ServicioAlertasInventario.generar_todas_las_alertas()

        self.assertIn('stock_bajo', resultado)
        self.assertIn('vencimientos', resultado)
        self.assertIn('stock_excesivo', resultado)
        self.assertIn('total', resultado)
        self.assertGreater(resultado['total'], 0)


class ServicioKardexTest(TestCase):
    """Tests para ServicioKardex"""

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
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE'
        )
        self.inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('100'),
            costo_promedio=Decimal('50.00')
        )

        # Crear movimientos para el kardex
        self.mov1 = MovimientoInventario.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('100'),
            costo_unitario=Decimal('50.00'),
            referencia='COMPRA-001',
            usuario=self.user,
            usuario_creacion=self.user
        )
        self.mov2 = MovimientoInventario.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='SALIDA_VENTA',
            cantidad=Decimal('30'),
            costo_unitario=Decimal('50.00'),
            referencia='VENTA-001',
            usuario=self.user,
            usuario_creacion=self.user
        )
        self.mov3 = MovimientoInventario.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento='ENTRADA_COMPRA',
            cantidad=Decimal('50'),
            costo_unitario=Decimal('55.00'),
            referencia='COMPRA-002',
            usuario=self.user,
            usuario_creacion=self.user
        )

    def test_obtener_kardex_basico(self):
        """Test: Obtener kardex con movimientos"""
        resultado = ServicioKardex.obtener_kardex(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id
        )

        self.assertIn('movimientos', resultado)
        self.assertIn('saldo_inicial', resultado)
        self.assertIn('saldo_final', resultado)
        self.assertEqual(len(resultado['movimientos']), 3)

    def test_kardex_saldos_acumulados(self):
        """Test: Kardex calcula saldos acumulados correctamente"""
        resultado = ServicioKardex.obtener_kardex(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id
        )

        movimientos = resultado['movimientos']

        # Primer movimiento: entrada 100, saldo = 100
        self.assertEqual(movimientos[0]['saldo'], Decimal('100'))

        # Segundo movimiento: salida 30, saldo = 70
        self.assertEqual(movimientos[1]['saldo'], Decimal('70'))

        # Tercer movimiento: entrada 50, saldo = 120
        self.assertEqual(movimientos[2]['saldo'], Decimal('120'))

    def test_kardex_con_filtro_fechas(self):
        """Test: Kardex filtra por rango de fechas"""
        fecha_desde = date.today()
        fecha_hasta = date.today() + timedelta(days=1)

        resultado = ServicioKardex.obtener_kardex(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        self.assertIn('movimientos', resultado)
        self.assertEqual(resultado['fecha_desde'], fecha_desde)
        self.assertEqual(resultado['fecha_hasta'], fecha_hasta)

    def test_kardex_con_filtro_empresa(self):
        """Test: Kardex filtra por empresa"""
        resultado = ServicioKardex.obtener_kardex(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id,
            empresa=self.empresa
        )

        self.assertEqual(len(resultado['movimientos']), 3)

    def test_kardex_saldo_final(self):
        """Test: Kardex calcula saldo final correctamente"""
        resultado = ServicioKardex.obtener_kardex(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id
        )

        # 100 - 30 + 50 = 120
        self.assertEqual(resultado['saldo_final']['cantidad'], Decimal('120'))

    def test_obtener_resumen_rotacion(self):
        """Test: Calcular resumen de rotación"""
        resultado = ServicioKardex.obtener_resumen_rotacion(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id,
            dias=30,
            empresa=self.empresa
        )

        self.assertIn('indice_rotacion', resultado)
        self.assertIn('dias_inventario', resultado)
        self.assertIn('total_salidas', resultado)
        self.assertIn('inventario_promedio', resultado)

    def test_rotacion_con_salidas(self):
        """Test: Rotación se calcula con movimientos de salida"""
        resultado = ServicioKardex.obtener_resumen_rotacion(
            producto_id=self.producto.id,
            almacen_id=self.almacen.id,
            dias=30
        )

        # Tenemos una salida de 30 unidades
        self.assertEqual(resultado['total_salidas'], 30)

    def test_kardex_sin_movimientos(self):
        """Test: Kardex vacío para producto sin movimientos"""
        producto_nuevo = Producto.objects.create(
            codigo_sku='PROD-002',
            nombre='Producto Nuevo',
            precio_venta_base=Decimal('100.00')
        )

        resultado = ServicioKardex.obtener_kardex(
            producto_id=producto_nuevo.id,
            almacen_id=self.almacen.id
        )

        self.assertEqual(len(resultado['movimientos']), 0)
        self.assertEqual(resultado['saldo_final']['cantidad'], Decimal('0'))

"""
Tests para los servicios de compras refactorizados.

Estos tests verifican la lógica de negocio extraída de los ViewSets
siguiendo el principio SRP (Single Responsibility Principle).
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import date

from .services import (
    ServicioCompras,
    ServicioRecepciones,
    ServicioDevoluciones,
    ServicioLiquidaciones
)
from .models import (
    Compra, DetalleCompra, OrdenCompra, DetalleOrdenCompra,
    RecepcionCompra, DetalleRecepcion,
    DevolucionProveedor, DetalleDevolucionProveedor,
    LiquidacionImportacion, GastoImportacion
)
from empresas.models import Empresa
from proveedores.models import Proveedor
from productos.models import Producto
from usuarios.models import User
from inventario.models import Almacen, InventarioProducto, MovimientoInventario


class ServicioComprasTest(TestCase):
    """Tests para ServicioCompras"""

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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE',
            controlar_stock=True
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True,
            usuario_creacion=self.user
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00'),
            estado='REGISTRADA'
        )
        DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=Decimal('10'),
            costo_unitario=Decimal('500.00'),
            tipo_linea='ALMACENABLE'
        )

    def test_procesar_compra_exitoso(self):
        """Test: Procesar compra crea movimientos de inventario"""
        movimientos = ServicioCompras.procesar_compra(
            compra=self.compra,
            usuario=self.user,
            almacen=self.almacen
        )

        self.compra.refresh_from_db()
        self.assertEqual(self.compra.estado, 'CXP')
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].tipo_movimiento, 'ENTRADA_COMPRA')
        self.assertEqual(movimientos[0].cantidad, Decimal('10'))

    def test_procesar_compra_sin_almacen_usa_primero(self):
        """Test: Procesar compra sin almacén usa el primero disponible"""
        movimientos = ServicioCompras.procesar_compra(
            compra=self.compra,
            usuario=self.user,
            almacen=None
        )

        self.compra.refresh_from_db()
        self.assertEqual(self.compra.estado, 'CXP')
        self.assertEqual(len(movimientos), 1)

    def test_procesar_compra_estado_invalido(self):
        """Test: No se puede procesar compra que no está REGISTRADA"""
        self.compra.estado = 'PAGADA'
        self.compra.save()

        with self.assertRaises(ValidationError) as context:
            ServicioCompras.procesar_compra(
                compra=self.compra,
                usuario=self.user,
                almacen=self.almacen
            )
        self.assertIn('REGISTRADA', str(context.exception))

    def test_procesar_compra_almacen_otra_empresa(self):
        """Test: No se puede procesar compra con almacén de otra empresa"""
        otra_empresa = Empresa.objects.create(nombre='Otra', rnc='987654321')
        otro_almacen = Almacen.objects.create(
            empresa=otra_empresa,
            nombre='Otro Almacén',
            activo=True
        )

        with self.assertRaises(ValidationError) as context:
            ServicioCompras.procesar_compra(
                compra=self.compra,
                usuario=self.user,
                almacen=otro_almacen
            )
        self.assertIn('empresa', str(context.exception))

    def test_anular_compra_exitoso(self):
        """Test: Anular compra revierte movimientos de inventario"""
        # Primero procesar la compra
        ServicioCompras.procesar_compra(
            compra=self.compra,
            usuario=self.user,
            almacen=self.almacen
        )

        # Luego anularla
        ServicioCompras.anular_compra(
            compra=self.compra,
            usuario=self.user
        )

        self.compra.refresh_from_db()
        self.assertEqual(self.compra.estado, 'ANULADA')

        # Verificar que se crearon movimientos de reversión
        movimientos_salida = MovimientoInventario.objects.filter(
            empresa=self.empresa,
            tipo_movimiento='SALIDA_AJUSTE',
            referencia__startswith='ANUL-'
        )
        self.assertEqual(movimientos_salida.count(), 1)

    def test_anular_compra_ya_anulada(self):
        """Test: No se puede anular compra ya anulada"""
        self.compra.estado = 'ANULADA'
        self.compra.save()

        with self.assertRaises(ValidationError) as context:
            ServicioCompras.anular_compra(
                compra=self.compra,
                usuario=self.user
            )
        self.assertIn('anulada', str(context.exception))

    def test_anular_compra_pagada(self):
        """Test: No se puede anular compra pagada"""
        self.compra.estado = 'PAGADA'
        self.compra.save()

        with self.assertRaises(ValidationError) as context:
            ServicioCompras.anular_compra(
                compra=self.compra,
                usuario=self.user
            )
        self.assertIn('pagada', str(context.exception))

    def test_recibir_orden_compra_exitoso(self):
        """Test: Recibir orden de compra actualiza cantidades"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )
        detalle = DetalleOrdenCompra.objects.create(
            orden=orden,
            producto=self.producto,
            cantidad=Decimal('100'),
            cantidad_recibida=Decimal('0'),
            costo_unitario=Decimal('50.00')
        )

        orden = ServicioCompras.recibir_orden_compra(
            orden_compra=orden,
            detalles_recibidos={detalle.id: Decimal('50')},
            usuario=self.user
        )

        detalle.refresh_from_db()
        self.assertEqual(detalle.cantidad_recibida, Decimal('50'))
        self.assertEqual(orden.estado, 'RECIBIDA_PARCIAL')

    def test_recibir_orden_compra_total(self):
        """Test: Recibir orden completa cambia estado a RECIBIDA_TOTAL"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )
        detalle = DetalleOrdenCompra.objects.create(
            orden=orden,
            producto=self.producto,
            cantidad=Decimal('100'),
            cantidad_recibida=Decimal('0'),
            costo_unitario=Decimal('50.00')
        )

        orden = ServicioCompras.recibir_orden_compra(
            orden_compra=orden,
            detalles_recibidos={detalle.id: Decimal('100')},
            usuario=self.user
        )

        self.assertEqual(orden.estado, 'RECIBIDA_TOTAL')

    def test_recibir_orden_estado_invalido(self):
        """Test: No se puede recibir orden en estado BORRADOR"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='BORRADOR'
        )

        with self.assertRaises(ValidationError):
            ServicioCompras.recibir_orden_compra(
                orden_compra=orden,
                detalles_recibidos={},
                usuario=self.user
            )

    def test_recibir_cantidad_mayor_que_solicitada(self):
        """Test: No se puede recibir más de lo solicitado"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )
        detalle = DetalleOrdenCompra.objects.create(
            orden=orden,
            producto=self.producto,
            cantidad=Decimal('10'),
            costo_unitario=Decimal('50.00')
        )

        with self.assertRaises(ValidationError) as context:
            ServicioCompras.recibir_orden_compra(
                orden_compra=orden,
                detalles_recibidos={detalle.id: Decimal('15')},
                usuario=self.user
            )
        self.assertIn('mayor', str(context.exception))


class ServicioRecepcionesTest(TestCase):
    """Tests para ServicioRecepciones"""

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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE'
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True
        )
        self.orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )
        self.detalle_orden = DetalleOrdenCompra.objects.create(
            orden=self.orden,
            producto=self.producto,
            cantidad=Decimal('100'),
            costo_unitario=Decimal('50.00')
        )
        self.recepcion = RecepcionCompra.objects.create(
            empresa=self.empresa,
            orden_compra=self.orden,
            almacen=self.almacen,
            fecha_recepcion=date.today(),
            estado='PENDIENTE'
        )
        self.detalle_recepcion = DetalleRecepcion.objects.create(
            recepcion=self.recepcion,
            detalle_orden=self.detalle_orden,
            producto=self.producto,
            cantidad_ordenada=Decimal('100'),
            cantidad_recibida=Decimal('50')
        )

    def test_confirmar_recepcion_exitoso(self):
        """Test: Confirmar recepción crea movimientos y actualiza inventario"""
        resultado = ServicioRecepciones.confirmar_recepcion(
            recepcion=self.recepcion,
            usuario=self.user
        )

        self.recepcion.refresh_from_db()
        self.assertIn(self.recepcion.estado, ['COMPLETA', 'PARCIAL'])
        self.assertEqual(resultado['movimientos_creados'], 1)

        # Verificar inventario creado/actualizado
        inventario = InventarioProducto.objects.get(
            empresa=self.empresa,
            almacen=self.almacen,
            producto=self.producto
        )
        self.assertEqual(inventario.cantidad_disponible, Decimal('50'))

    def test_confirmar_recepcion_estado_invalido(self):
        """Test: No se puede confirmar recepción ya completada"""
        self.recepcion.estado = 'COMPLETA'
        self.recepcion.save()

        with self.assertRaises(ValidationError) as context:
            ServicioRecepciones.confirmar_recepcion(
                recepcion=self.recepcion,
                usuario=self.user
            )
        self.assertIn('PENDIENTE', str(context.exception))

    def test_confirmar_recepcion_actualiza_orden(self):
        """Test: Confirmar recepción actualiza estado de orden"""
        resultado = ServicioRecepciones.confirmar_recepcion(
            recepcion=self.recepcion,
            usuario=self.user
        )

        self.orden.refresh_from_db()
        self.assertIn(self.orden.estado, ['RECIBIDA_PARCIAL', 'RECIBIDA_TOTAL'])


class ServicioDevolucionesTest(TestCase):
    """Tests para ServicioDevoluciones"""

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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE'
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True
        )
        # Crear inventario con stock
        self.inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('100'),
            costo_promedio=Decimal('50.00')
        )
        self.devolucion = DevolucionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha=date.today(),
            estado='BORRADOR'
        )
        # Nota: almacen está en DetalleDevolucionProveedor, no en DevolucionProveedor
        self.detalle_devolucion = DetalleDevolucionProveedor.objects.create(
            devolucion=self.devolucion,
            producto=self.producto,
            almacen=self.almacen,
            cantidad=Decimal('10'),
            costo_unitario=Decimal('50.00')
        )

    def test_confirmar_devolucion_exitoso(self):
        """Test: Confirmar devolución registra salida de inventario"""
        resultado = ServicioDevoluciones.confirmar_devolucion(
            devolucion=self.devolucion,
            usuario=self.user
        )

        self.devolucion.refresh_from_db()
        self.assertEqual(self.devolucion.estado, 'CONFIRMADA')
        self.assertEqual(resultado['movimientos_creados'], 1)

        # Verificar inventario actualizado
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.cantidad_disponible, Decimal('90'))

    def test_confirmar_devolucion_sin_stock(self):
        """Test: No se puede confirmar devolución sin stock suficiente"""
        self.detalle_devolucion.cantidad = Decimal('200')
        self.detalle_devolucion.save()

        with self.assertRaises(ValidationError) as context:
            ServicioDevoluciones.confirmar_devolucion(
                devolucion=self.devolucion,
                usuario=self.user
            )
        self.assertIn('insuficiente', str(context.exception))

    def test_confirmar_devolucion_estado_invalido(self):
        """Test: No se puede confirmar devolución ya confirmada"""
        self.devolucion.estado = 'CONFIRMADA'
        self.devolucion.save()

        with self.assertRaises(ValidationError) as context:
            ServicioDevoluciones.confirmar_devolucion(
                devolucion=self.devolucion,
                usuario=self.user
            )
        self.assertIn('BORRADOR', str(context.exception))


class ServicioLiquidacionesTest(TestCase):
    """Tests para ServicioLiquidaciones"""

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
        self.proveedor_int = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Internacional',
            numero_identificacion='INT-001',
            es_internacional=True
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00'),
            tipo_producto='ALMACENABLE'
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal',
            activo=True
        )
        # Crear inventario
        self.inventario = InventarioProducto.objects.create(
            empresa=self.empresa,
            producto=self.producto,
            almacen=self.almacen,
            cantidad_disponible=Decimal('100'),
            costo_promedio=Decimal('50.00')
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor_int,
            fecha_compra=date.today(),
            numero_factura_proveedor='INT-001',
            total=Decimal('10000.00'),
            estado='REGISTRADA'
        )
        self.detalle_compra = DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=Decimal('100'),
            costo_unitario=Decimal('100.00')
        )
        self.liquidacion = LiquidacionImportacion.objects.create(
            empresa=self.empresa,
            compra=self.compra,
            fecha=date.today(),
            total_fob=Decimal('10000.00'),
            estado='BORRADOR'
        )
        # Agregar gastos de importación
        GastoImportacion.objects.create(
            liquidacion=self.liquidacion,
            tipo='FLETE',
            descripcion='Flete marítimo',
            monto=Decimal('500.00')
        )
        GastoImportacion.objects.create(
            liquidacion=self.liquidacion,
            tipo='SEGURO',
            descripcion='Seguro de carga',
            monto=Decimal('200.00')
        )
        self.liquidacion.calcular_totales()

    def test_liquidar_importacion_exitoso(self):
        """Test: Liquidar importación actualiza costos en inventario"""
        resultado = ServicioLiquidaciones.liquidar_importacion(
            liquidacion=self.liquidacion,
            usuario=self.user
        )

        self.liquidacion.refresh_from_db()
        self.assertEqual(self.liquidacion.estado, 'LIQUIDADA')
        self.assertGreater(resultado['productos_actualizados'], 0)

    def test_liquidar_importacion_estado_invalido(self):
        """Test: No se puede liquidar importación ya liquidada"""
        self.liquidacion.estado = 'LIQUIDADA'
        self.liquidacion.save()

        with self.assertRaises(ValidationError) as context:
            ServicioLiquidaciones.liquidar_importacion(
                liquidacion=self.liquidacion,
                usuario=self.user
            )
        self.assertIn('BORRADOR', str(context.exception))

    def test_calcular_costo_nacionalizado(self):
        """Test: Cálculo correcto de costo nacionalizado"""
        # Costo FOB = 100 * 100 = 10,000
        # Gastos = 700
        # Costo nacionalizado = (10,000 + 700) / 100 = 107

        class MockDetalle:
            cantidad = Decimal('100')
            costo_unitario = Decimal('100.00')

        costo = ServicioLiquidaciones._calcular_costo_nacionalizado(
            detalle=MockDetalle(),
            total_valor_fob=Decimal('10000.00'),
            total_gastos=Decimal('700.00')
        )

        self.assertEqual(costo, Decimal('107.00'))

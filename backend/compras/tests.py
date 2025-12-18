from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from .models import (
    SolicitudCotizacionProveedor, OrdenCompra, DetalleOrdenCompra,
    Compra, DetalleCompra, Gasto, RecepcionCompra, DetalleRecepcion,
    DevolucionProveedor, DetalleDevolucionProveedor, LiquidacionImportacion, GastoImportacion
)
from empresas.models import Empresa
from proveedores.models import Proveedor
from productos.models import Producto
from usuarios.models import User


class SolicitudCotizacionModelTest(TestCase):
    """Tests para el modelo SolicitudCotizacionProveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )

    def test_crear_solicitud(self):
        """Test: Crear solicitud de cotización"""
        solicitud = SolicitudCotizacionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            detalles='Necesito cotización de 100 unidades del producto X'
        )
        self.assertEqual(solicitud.estado, 'PENDIENTE')
        self.assertIsNotNone(solicitud.uuid)

    def test_solicitud_str(self):
        """Test: Representación string de solicitud"""
        solicitud = SolicitudCotizacionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            detalles='Test'
        )
        self.assertIn('Proveedor Test', str(solicitud))

    def test_validacion_proveedor_misma_empresa(self):
        """Test: Proveedor debe ser de la misma empresa"""
        otra_empresa = Empresa.objects.create(
            nombre='Otra Empresa',
            rnc='987654321'
        )
        proveedor_otro = Proveedor.objects.create(
            empresa=otra_empresa,
            nombre='Otro Proveedor',
            numero_identificacion='222222222'
        )
        solicitud = SolicitudCotizacionProveedor(
            empresa=self.empresa,
            proveedor=proveedor_otro,
            detalles='Test'
        )
        with self.assertRaises(ValidationError) as context:
            solicitud.clean()
        self.assertIn('proveedor', context.exception.message_dict)


class OrdenCompraModelTest(TestCase):
    """Tests para el modelo OrdenCompra"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )

    def test_crear_orden_compra(self):
        """Test: Crear orden de compra"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            condiciones_pago='30 días'
        )
        self.assertEqual(orden.estado, 'BORRADOR')
        self.assertIsNotNone(orden.uuid)

    def test_orden_str(self):
        """Test: Representación string de orden"""
        orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor
        )
        self.assertIn('Proveedor Test', str(orden))

    def test_validacion_total_negativo(self):
        """Test: Total negativo falla validación"""
        orden = OrdenCompra(
            empresa=self.empresa,
            proveedor=self.proveedor,
            total=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            orden.clean()
        self.assertIn('total', context.exception.message_dict)

    def test_validacion_tasa_cambio_cero(self):
        """Test: Tasa de cambio cero falla validación"""
        orden = OrdenCompra(
            empresa=self.empresa,
            proveedor=self.proveedor,
            tasa_cambio=Decimal('0')
        )
        with self.assertRaises(ValidationError) as context:
            orden.clean()
        self.assertIn('tasa_cambio', context.exception.message_dict)


class DetalleOrdenCompraModelTest(TestCase):
    """Tests para el modelo DetalleOrdenCompra"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )
        self.orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor
        )

    def test_crear_detalle(self):
        """Test: Crear detalle de orden de compra"""
        detalle = DetalleOrdenCompra.objects.create(
            orden=self.orden,
            producto=self.producto,
            cantidad=Decimal('10'),
            costo_unitario=Decimal('80.00')
        )
        self.assertEqual(detalle.tipo_linea, 'ALMACENABLE')

    def test_validacion_cantidad_cero(self):
        """Test: Cantidad cero falla validación"""
        detalle = DetalleOrdenCompra(
            orden=self.orden,
            producto=self.producto,
            cantidad=Decimal('0'),
            costo_unitario=Decimal('80.00')
        )
        with self.assertRaises(ValidationError) as context:
            detalle.clean()
        self.assertIn('cantidad', context.exception.message_dict)

    def test_validacion_cantidad_recibida_mayor(self):
        """Test: Cantidad recibida mayor que solicitada falla"""
        detalle = DetalleOrdenCompra(
            orden=self.orden,
            producto=self.producto,
            cantidad=Decimal('10'),
            cantidad_recibida=Decimal('15'),
            costo_unitario=Decimal('80.00')
        )
        with self.assertRaises(ValidationError) as context:
            detalle.clean()
        self.assertIn('cantidad_recibida', context.exception.message_dict)


class CompraModelTest(TestCase):
    """Tests para el modelo Compra"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )

    def test_crear_compra(self):
        """Test: Crear compra"""
        compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00')
        )
        self.assertEqual(compra.estado, 'REGISTRADA')
        self.assertEqual(compra.tipo_gasto, '02')
        self.assertIsNotNone(compra.uuid)

    def test_compra_str(self):
        """Test: Representación string de compra"""
        compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00')
        )
        self.assertIn('FAC-001', str(compra))
        self.assertIn('Proveedor Test', str(compra))

    def test_validacion_monto_pagado_mayor_total(self):
        """Test: Monto pagado mayor que total falla"""
        compra = Compra(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00'),
            monto_pagado=Decimal('6000.00')
        )
        with self.assertRaises(ValidationError) as context:
            compra.clean()
        self.assertIn('monto_pagado', context.exception.message_dict)

    def test_numero_factura_unico_por_empresa_proveedor(self):
        """Test: Número de factura es único por empresa y proveedor"""
        Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00')
        )
        with self.assertRaises(Exception):
            Compra.objects.create(
                empresa=self.empresa,
                proveedor=self.proveedor,
                fecha_compra=date.today(),
                numero_factura_proveedor='FAC-001',
                total=Decimal('3000.00')
            )


class GastoModelTest(TestCase):
    """Tests para el modelo Gasto"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_gasto(self):
        """Test: Crear gasto"""
        gasto = Gasto.objects.create(
            empresa=self.empresa,
            descripcion='Pago de electricidad',
            categoria='Servicios Públicos',
            fecha_gasto=date.today(),
            total=Decimal('1500.00')
        )
        self.assertEqual(gasto.estado, 'PENDIENTE')
        self.assertIsNotNone(gasto.uuid)

    def test_gasto_str(self):
        """Test: Representación string de gasto"""
        gasto = Gasto.objects.create(
            empresa=self.empresa,
            descripcion='Pago de electricidad',
            categoria='Servicios Públicos',
            fecha_gasto=date.today(),
            total=Decimal('1500.00')
        )
        self.assertIn('Pago de electricidad', str(gasto))

    def test_validacion_total_negativo(self):
        """Test: Total negativo falla validación"""
        gasto = Gasto(
            empresa=self.empresa,
            descripcion='Test',
            categoria='Test',
            fecha_gasto=date.today(),
            total=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            gasto.clean()
        self.assertIn('total', context.exception.message_dict)


class ComprasAPITest(APITestCase):
    """Tests para las APIs de Compras"""

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
            username='usuario',
            password='user123',
            empresa=self.empresa,
            rol='facturador'
        )

        # Asignar permisos
        for model in [SolicitudCotizacionProveedor, OrdenCompra, Compra, Gasto]:
            content_type = ContentType.objects.get_for_model(model)
            for codename in ['view', 'add', 'change', 'delete']:
                perm_codename = f'{codename}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    self.user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )

        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )

        self.orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            total=Decimal('1000.00')
        )

        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00')
        )

        self.gasto = Gasto.objects.create(
            empresa=self.empresa,
            descripcion='Gasto Test',
            categoria='Servicios',
            fecha_gasto=date.today(),
            total=Decimal('500.00')
        )

        self.client = APIClient()

    def test_listar_ordenes_compra(self):
        """Test: Listar órdenes de compra"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/compras/ordenes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_orden_compra(self):
        """Test: Crear orden de compra"""
        self.client.force_authenticate(user=self.user)
        data = {
            'proveedor': self.proveedor.id,
            'condiciones_pago': '30 días'
        }
        response = self.client.post('/api/v1/compras/ordenes/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_aprobar_orden_compra(self):
        """Test: Aprobar orden de compra"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/compras/ordenes/{self.orden.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'APROBADA')

    def test_aprobar_orden_no_borrador(self):
        """Test: No se puede aprobar orden que no está en borrador"""
        self.orden.estado = 'APROBADA'
        self.orden.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/compras/ordenes/{self.orden.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelar_orden_compra(self):
        """Test: Cancelar orden de compra"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/compras/ordenes/{self.orden.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CANCELADA')

    def test_listar_compras(self):
        """Test: Listar compras"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/compras/facturas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_compras_por_proveedor(self):
        """Test: Filtrar compras por proveedor"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/compras/facturas/?proveedor={self.proveedor.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_compras_por_estado(self):
        """Test: Filtrar compras por estado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/compras/facturas/?estado=REGISTRADA')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_gastos(self):
        """Test: Listar gastos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/compras/gastos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_gasto(self):
        """Test: Crear gasto"""
        self.client.force_authenticate(user=self.user)
        data = {
            'descripcion': 'Nuevo Gasto',
            'categoria': 'Servicios',
            'fecha_gasto': str(date.today()),
            'total': '1000.00'
        }
        response = self.client.post('/api/v1/compras/gastos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_marcar_gasto_pagado(self):
        """Test: Marcar gasto como pagado"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/compras/gastos/{self.gasto.id}/marcar_pagado/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'PAGADO')

    def test_filtrar_gastos_por_categoria(self):
        """Test: Filtrar gastos por categoría"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/compras/gastos/?categoria=Servicios')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/compras/facturas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ======================= TESTS NUEVOS MODELOS =======================

class RecepcionCompraModelTest(TestCase):
    """Tests para el modelo RecepcionCompra"""

    def setUp(self):
        from inventario.models import Almacen
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal'
        )
        self.orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )

    def test_crear_recepcion(self):
        """Test: Crear recepción de compra"""
        recepcion = RecepcionCompra.objects.create(
            empresa=self.empresa,
            orden_compra=self.orden,
            almacen=self.almacen,
            fecha_recepcion=date.today()
        )
        self.assertEqual(recepcion.estado, 'PENDIENTE')
        self.assertIsNotNone(recepcion.numero_recepcion)
        self.assertIn('REC-', recepcion.numero_recepcion)

    def test_recepcion_str(self):
        """Test: Representación string de recepción"""
        recepcion = RecepcionCompra.objects.create(
            empresa=self.empresa,
            orden_compra=self.orden,
            almacen=self.almacen,
            fecha_recepcion=date.today()
        )
        self.assertIn('REC-', str(recepcion))

    def test_validacion_orden_empresa_diferente(self):
        """Test: Orden debe ser de la misma empresa"""
        otra_empresa = Empresa.objects.create(nombre='Otra Empresa', rnc='987654321')
        otro_proveedor = Proveedor.objects.create(
            empresa=otra_empresa,
            nombre='Otro Proveedor',
            numero_identificacion='222222222'
        )
        otra_orden = OrdenCompra.objects.create(
            empresa=otra_empresa,
            proveedor=otro_proveedor,
            estado='APROBADA'
        )
        recepcion = RecepcionCompra(
            empresa=self.empresa,
            orden_compra=otra_orden,
            almacen=self.almacen,
            fecha_recepcion=date.today()
        )
        with self.assertRaises(ValidationError) as context:
            recepcion.clean()
        self.assertIn('orden_compra', context.exception.message_dict)

    def test_validacion_orden_estado_borrador(self):
        """Test: Orden debe estar aprobada o enviada"""
        orden_borrador = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='BORRADOR'
        )
        recepcion = RecepcionCompra(
            empresa=self.empresa,
            orden_compra=orden_borrador,
            almacen=self.almacen,
            fecha_recepcion=date.today()
        )
        with self.assertRaises(ValidationError) as context:
            recepcion.clean()
        self.assertIn('orden_compra', context.exception.message_dict)


class DevolucionProveedorModelTest(TestCase):
    """Tests para el modelo DevolucionProveedor"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-001',
            total=Decimal('5000.00')
        )

    def test_crear_devolucion(self):
        """Test: Crear devolución a proveedor"""
        devolucion = DevolucionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha=date.today(),
            motivo='DEFECTO'
        )
        self.assertEqual(devolucion.estado, 'BORRADOR')
        self.assertIsNotNone(devolucion.numero_devolucion)
        self.assertIn('DEV-', devolucion.numero_devolucion)

    def test_devolucion_str(self):
        """Test: Representación string de devolución"""
        devolucion = DevolucionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha=date.today()
        )
        self.assertIn('DEV-', str(devolucion))
        self.assertIn('Proveedor Test', str(devolucion))

    def test_validacion_compra_proveedor_diferente(self):
        """Test: Compra debe ser del mismo proveedor"""
        otro_proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Otro Proveedor',
            numero_identificacion='222222222'
        )
        devolucion = DevolucionProveedor(
            empresa=self.empresa,
            proveedor=otro_proveedor,
            compra=self.compra,
            fecha=date.today()
        )
        with self.assertRaises(ValidationError) as context:
            devolucion.clean()
        self.assertIn('compra', context.exception.message_dict)

    def test_validacion_total_negativo(self):
        """Test: Total negativo falla validación"""
        devolucion = DevolucionProveedor(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha=date.today(),
            total=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            devolucion.clean()
        self.assertIn('total', context.exception.message_dict)


class LiquidacionImportacionModelTest(TestCase):
    """Tests para el modelo LiquidacionImportacion"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor_int = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Internacional',
            numero_identificacion='INT-001',
            es_internacional=True
        )
        self.proveedor_local = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Local',
            numero_identificacion='LOC-001',
            es_internacional=False
        )
        self.compra_int = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor_int,
            fecha_compra=date.today(),
            numero_factura_proveedor='INT-001',
            total=Decimal('10000.00')
        )
        self.compra_local = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor_local,
            fecha_compra=date.today(),
            numero_factura_proveedor='LOC-001',
            total=Decimal('5000.00')
        )

    def test_crear_liquidacion(self):
        """Test: Crear liquidación de importación"""
        liquidacion = LiquidacionImportacion.objects.create(
            empresa=self.empresa,
            compra=self.compra_int,
            fecha=date.today(),
            total_fob=Decimal('10000.00'),
            incoterm='FOB'
        )
        self.assertEqual(liquidacion.estado, 'BORRADOR')
        self.assertIsNotNone(liquidacion.numero_liquidacion)
        self.assertIn('LIQ-', liquidacion.numero_liquidacion)

    def test_liquidacion_str(self):
        """Test: Representación string de liquidación"""
        liquidacion = LiquidacionImportacion.objects.create(
            empresa=self.empresa,
            compra=self.compra_int,
            fecha=date.today(),
            total_fob=Decimal('10000.00')
        )
        self.assertIn('LIQ-', str(liquidacion))

    def test_validacion_proveedor_no_internacional(self):
        """Test: Solo aplica para proveedores internacionales"""
        liquidacion = LiquidacionImportacion(
            empresa=self.empresa,
            compra=self.compra_local,
            fecha=date.today(),
            total_fob=Decimal('5000.00')
        )
        with self.assertRaises(ValidationError) as context:
            liquidacion.clean()
        self.assertIn('compra', context.exception.message_dict)

    def test_validacion_tasa_cambio_cero(self):
        """Test: Tasa de cambio debe ser mayor a cero"""
        liquidacion = LiquidacionImportacion(
            empresa=self.empresa,
            compra=self.compra_int,
            fecha=date.today(),
            total_fob=Decimal('10000.00'),
            tasa_cambio=Decimal('0')
        )
        with self.assertRaises(ValidationError) as context:
            liquidacion.clean()
        self.assertIn('tasa_cambio', context.exception.message_dict)

    def test_agregar_gasto_importacion(self):
        """Test: Agregar gastos a liquidación"""
        liquidacion = LiquidacionImportacion.objects.create(
            empresa=self.empresa,
            compra=self.compra_int,
            fecha=date.today(),
            total_fob=Decimal('10000.00')
        )
        GastoImportacion.objects.create(
            liquidacion=liquidacion,
            tipo='FLETE',
            descripcion='Flete marítimo',
            monto=Decimal('500.00')
        )
        GastoImportacion.objects.create(
            liquidacion=liquidacion,
            tipo='SEGURO',
            descripcion='Seguro de carga',
            monto=Decimal('200.00')
        )
        liquidacion.calcular_totales()
        self.assertEqual(liquidacion.total_gastos, Decimal('700.00'))
        self.assertEqual(liquidacion.total_cif, Decimal('10700.00'))


class RecepcionCompraAPITest(APITestCase):
    """Tests para la API de RecepcionCompra"""

    def setUp(self):
        from inventario.models import Almacen
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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.almacen = Almacen.objects.create(
            empresa=self.empresa,
            nombre='Almacén Principal'
        )
        self.orden = OrdenCompra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            estado='APROBADA'
        )
        self.recepcion = RecepcionCompra.objects.create(
            empresa=self.empresa,
            orden_compra=self.orden,
            almacen=self.almacen,
            fecha_recepcion=date.today()
        )
        self.client = APIClient()

    def test_listar_recepciones(self):
        """Test: Listar recepciones de compra"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/recepciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_recepcion(self):
        """Test: Crear recepción de compra"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'orden_compra': self.orden.id,
            'almacen': self.almacen.id,
            'fecha_recepcion': str(date.today())
        }
        response = self.client.post('/api/v1/compras/recepciones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cancelar_recepcion(self):
        """Test: Cancelar recepción de compra"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(f'/api/v1/compras/recepciones/{self.recepcion.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CANCELADA')


class DevolucionProveedorAPITest(APITestCase):
    """Tests para la API de DevolucionProveedor"""

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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.devolucion = DevolucionProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha=date.today(),
            motivo='DEFECTO'
        )
        self.client = APIClient()

    def test_listar_devoluciones(self):
        """Test: Listar devoluciones a proveedores"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/devoluciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_devolucion(self):
        """Test: Crear devolución a proveedor"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'proveedor': self.proveedor.id,
            'fecha': str(date.today()),
            'motivo': 'ERROR'
        }
        response = self.client.post('/api/v1/compras/devoluciones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cancelar_devolucion(self):
        """Test: Cancelar devolución"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(f'/api/v1/compras/devoluciones/{self.devolucion.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CANCELADA')

    def test_filtrar_devoluciones_por_motivo(self):
        """Test: Filtrar devoluciones por motivo"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/devoluciones/?motivo=DEFECTO')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LiquidacionImportacionAPITest(APITestCase):
    """Tests para la API de LiquidacionImportacion"""

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
        self.proveedor_int = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Internacional',
            numero_identificacion='INT-001',
            es_internacional=True
        )
        self.compra_int = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor_int,
            fecha_compra=date.today(),
            numero_factura_proveedor='INT-001',
            total=Decimal('10000.00')
        )
        self.liquidacion = LiquidacionImportacion.objects.create(
            empresa=self.empresa,
            compra=self.compra_int,
            fecha=date.today(),
            total_fob=Decimal('10000.00'),
            incoterm='FOB'
        )
        self.client = APIClient()

    def test_listar_liquidaciones(self):
        """Test: Listar liquidaciones de importación"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/liquidaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_liquidacion(self):
        """Test: Crear liquidación de importación"""
        otra_compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor_int,
            fecha_compra=date.today(),
            numero_factura_proveedor='INT-002',
            total=Decimal('8000.00')
        )
        self.client.force_authenticate(user=self.superuser)
        data = {
            'compra': otra_compra.id,
            'fecha': str(date.today()),
            'total_fob': '8000.00',
            'incoterm': 'CIF'
        }
        response = self.client.post('/api/v1/compras/liquidaciones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cancelar_liquidacion(self):
        """Test: Cancelar liquidación"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(f'/api/v1/compras/liquidaciones/{self.liquidacion.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'CANCELADA')

    def test_agregar_gasto_via_api(self):
        """Test: Agregar gasto a liquidación via API"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'tipo': 'FLETE',
            'descripcion': 'Flete marítimo',
            'monto': '500.00'
        }
        response = self.client.post(f'/api/v1/compras/liquidaciones/{self.liquidacion.id}/agregar_gasto/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filtrar_liquidaciones_por_incoterm(self):
        """Test: Filtrar liquidaciones por incoterm"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/liquidaciones/?incoterm=FOB')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ======================= TESTS RETENCIONES FISCALES =======================

class TipoRetencionModelTest(TestCase):
    """Tests para el modelo TipoRetencion"""

    def setUp(self):
        from compras.models import TipoRetencion
        self.TipoRetencion = TipoRetencion
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )

    def test_crear_tipo_retencion_isr(self):
        """Test: Crear tipo de retención ISR"""
        tipo = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='ISR Personas Físicas',
            categoria='ISR',
            porcentaje=Decimal('10.00'),
            aplica_a_persona_fisica=True
        )
        self.assertEqual(tipo.categoria, 'ISR')
        self.assertEqual(tipo.porcentaje, Decimal('10.00'))
        self.assertTrue(tipo.activo)

    def test_crear_tipo_retencion_itbis(self):
        """Test: Crear tipo de retención ITBIS"""
        tipo = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='02',
            nombre='ITBIS Retenido 30%',
            categoria='ITBIS',
            porcentaje=Decimal('30.00'),
            aplica_a_persona_juridica=True
        )
        self.assertEqual(tipo.categoria, 'ITBIS')
        self.assertEqual(tipo.porcentaje, Decimal('30.00'))

    def test_tipo_retencion_str(self):
        """Test: Representación string de tipo retención"""
        tipo = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='ISR Personas Físicas',
            categoria='ISR',
            porcentaje=Decimal('10.00')
        )
        self.assertIn('01', str(tipo))
        self.assertIn('ISR', str(tipo))
        self.assertIn('10.00', str(tipo))

    def test_validacion_porcentaje_negativo(self):
        """Test: Porcentaje negativo falla validación"""
        from django.core.exceptions import ValidationError
        tipo = self.TipoRetencion(
            empresa=self.empresa,
            codigo='99',
            nombre='Retención Inválida',
            categoria='ISR',
            porcentaje=Decimal('-5.00')
        )
        with self.assertRaises(ValidationError):
            tipo.clean()

    def test_validacion_porcentaje_mayor_100(self):
        """Test: Porcentaje mayor a 100 falla validación"""
        from django.core.exceptions import ValidationError
        tipo = self.TipoRetencion(
            empresa=self.empresa,
            codigo='99',
            nombre='Retención Inválida',
            categoria='ISR',
            porcentaje=Decimal('150.00')
        )
        with self.assertRaises(ValidationError):
            tipo.clean()


class RetencionCompraModelTest(TestCase):
    """Tests para el modelo RetencionCompra"""

    def setUp(self):
        from compras.models import TipoRetencion, RetencionCompra
        self.TipoRetencion = TipoRetencion
        self.RetencionCompra = RetencionCompra
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-RET-001',
            subtotal=Decimal('10000.00'),
            total=Decimal('11800.00')
        )
        self.tipo_isr = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='ISR Personas Físicas',
            categoria='ISR',
            porcentaje=Decimal('10.00')
        )

    def test_crear_retencion(self):
        """Test: Crear retención en compra"""
        retencion = self.RetencionCompra.objects.create(
            empresa=self.empresa,
            compra=self.compra,
            tipo_retencion=self.tipo_isr,
            base_imponible=Decimal('10000.00'),
            porcentaje=Decimal('10.00'),
            monto_retenido=Decimal('1000.00')
        )
        self.assertEqual(retencion.monto_retenido, Decimal('1000.00'))
        self.assertIsNotNone(retencion.uuid)

    def test_auto_calculo_monto(self):
        """Test: Cálculo automático del monto retenido"""
        retencion = self.RetencionCompra(
            empresa=self.empresa,
            compra=self.compra,
            tipo_retencion=self.tipo_isr,
            base_imponible=Decimal('5000.00'),
            porcentaje=Decimal('10.00'),
            monto_retenido=Decimal('0')
        )
        retencion.save()
        self.assertEqual(retencion.monto_retenido, Decimal('500.00'))

    def test_actualiza_totales_compra(self):
        """Test: Retención actualiza totales de ISR en compra"""
        self.RetencionCompra.objects.create(
            empresa=self.empresa,
            compra=self.compra,
            tipo_retencion=self.tipo_isr,
            base_imponible=Decimal('10000.00'),
            porcentaje=Decimal('10.00'),
            monto_retenido=Decimal('1000.00')
        )
        self.compra.refresh_from_db()
        self.assertEqual(self.compra.isr_retenido, Decimal('1000.00'))

    def test_retencion_str(self):
        """Test: Representación string de retención"""
        retencion = self.RetencionCompra.objects.create(
            empresa=self.empresa,
            compra=self.compra,
            tipo_retencion=self.tipo_isr,
            base_imponible=Decimal('10000.00'),
            porcentaje=Decimal('10.00'),
            monto_retenido=Decimal('1000.00')
        )
        self.assertIn('FAC-RET-001', str(retencion))
        self.assertIn('ISR', str(retencion))


class TipoRetencionAPITest(APITestCase):
    """Tests para la API de TipoRetencion"""

    def setUp(self):
        from compras.models import TipoRetencion
        self.TipoRetencion = TipoRetencion
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
        self.tipo = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='ISR Personas Físicas',
            categoria='ISR',
            porcentaje=Decimal('10.00')
        )
        self.client = APIClient()

    def test_listar_tipos_retencion(self):
        """Test: Listar tipos de retención"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/tipos-retencion/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_tipo_retencion(self):
        """Test: Crear tipo de retención"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'codigo': '02',
            'nombre': 'ITBIS Retenido 30%',
            'categoria': 'ITBIS',
            'porcentaje': '30.00'
        }
        response = self.client.post('/api/v1/compras/tipos-retencion/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filtrar_por_categoria(self):
        """Test: Filtrar tipos por categoría"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/tipos-retencion/?categoria=ISR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RetencionCompraAPITest(APITestCase):
    """Tests para la API de RetencionCompra"""

    def setUp(self):
        from compras.models import TipoRetencion, RetencionCompra
        self.TipoRetencion = TipoRetencion
        self.RetencionCompra = RetencionCompra
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
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre='Proveedor Test',
            numero_identificacion='111111111'
        )
        self.compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-API-001',
            subtotal=Decimal('10000.00'),
            total=Decimal('11800.00')
        )
        self.tipo_isr = self.TipoRetencion.objects.create(
            empresa=self.empresa,
            codigo='01',
            nombre='ISR Personas Físicas',
            categoria='ISR',
            porcentaje=Decimal('10.00')
        )
        self.retencion = self.RetencionCompra.objects.create(
            empresa=self.empresa,
            compra=self.compra,
            tipo_retencion=self.tipo_isr,
            base_imponible=Decimal('10000.00'),
            porcentaje=Decimal('10.00'),
            monto_retenido=Decimal('1000.00')
        )
        self.client = APIClient()

    def test_listar_retenciones(self):
        """Test: Listar retenciones"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/compras/retenciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_retencion(self):
        """Test: Crear retención"""
        otra_compra = Compra.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            fecha_compra=date.today(),
            numero_factura_proveedor='FAC-API-002',
            subtotal=Decimal('5000.00'),
            total=Decimal('5900.00')
        )
        self.client.force_authenticate(user=self.superuser)
        data = {
            'compra': otra_compra.id,
            'tipo_retencion': self.tipo_isr.id,
            'base_imponible': '5000.00',
            'porcentaje': '10.00',
            'monto_retenido': '500.00'
        }
        response = self.client.post('/api/v1/compras/retenciones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_por_compra_endpoint(self):
        """Test: Endpoint por_compra"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/api/v1/compras/retenciones/por_compra/?compra_id={self.compra.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_resumen_periodo_endpoint(self):
        """Test: Endpoint resumen_periodo"""
        self.client.force_authenticate(user=self.superuser)
        mes = date.today().month
        anio = date.today().year
        response = self.client.get(f'/api/v1/compras/retenciones/resumen_periodo/?mes={mes}&anio={anio}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('isr_retenido', response.data)
        self.assertIn('itbis_retenido', response.data)

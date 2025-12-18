from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from .models import Categoria, Producto
from .serializers import ProductoSerializer
from empresas.models import Empresa
from usuarios.models import User


class CategoriaModelTest(TestCase):
    """Tests para el modelo Categoria"""

    def test_crear_categoria(self):
        """Test: Crear categoría"""
        categoria = Categoria.objects.create(
            nombre='Electrónicos',
            descripcion='Productos electrónicos'
        )
        self.assertEqual(categoria.nombre, 'Electrónicos')
        self.assertTrue(categoria.activa)

    def test_categoria_str(self):
        """Test: Representación string de categoría"""
        categoria = Categoria.objects.create(nombre='Ropa')
        self.assertEqual(str(categoria), 'Ropa')

    def test_nombre_normalizado(self):
        """Test: Nombre se normaliza (strip)"""
        categoria = Categoria(nombre='  Electrónicos  ')
        categoria.clean()
        self.assertEqual(categoria.nombre, 'Electrónicos')

    def test_nombre_vacio_falla(self):
        """Test: Nombre vacío falla validación"""
        categoria = Categoria(nombre='   ')
        with self.assertRaises(ValidationError) as context:
            categoria.clean()
        self.assertIn('nombre', context.exception.message_dict)


class ProductoModelTest(TestCase):
    """Tests para el modelo Producto"""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Test')

    def test_crear_producto_basico(self):
        """Test: Crear producto básico"""
        producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Producto Test',
            precio_venta_base=Decimal('100.00')
        )
        self.assertEqual(producto.codigo_sku, 'PROD-001')
        self.assertEqual(producto.nombre, 'Producto Test')
        self.assertTrue(producto.activo)
        self.assertEqual(producto.tipo_producto, 'ALMACENABLE')
        self.assertTrue(producto.controlar_stock)

    def test_crear_producto_servicio(self):
        """Test: Crear producto tipo servicio"""
        producto = Producto.objects.create(
            codigo_sku='SERV-001',
            nombre='Servicio Test',
            precio_venta_base=Decimal('500.00'),
            tipo_producto='SERVICIO'
        )
        self.assertEqual(producto.tipo_producto, 'SERVICIO')
        self.assertFalse(producto.controlar_stock)  # Auto-configurado

    def test_crear_producto_activo_fijo(self):
        """Test: Crear producto tipo activo fijo"""
        producto = Producto.objects.create(
            codigo_sku='ACTIVO-001',
            nombre='Computadora',
            precio_venta_base=Decimal('25000.00'),
            tipo_producto='ACTIVO_FIJO'
        )
        self.assertEqual(producto.tipo_producto, 'ACTIVO_FIJO')
        self.assertFalse(producto.controlar_stock)  # Auto-configurado

    def test_producto_str(self):
        """Test: Representación string de producto"""
        producto = Producto.objects.create(
            codigo_sku='TEST-001',
            nombre='Test Product',
            precio_venta_base=Decimal('100.00')
        )
        self.assertEqual(str(producto), 'TEST-001 - Test Product')

    def test_validacion_precio_negativo(self):
        """Test: Precio negativo falla validación"""
        producto = Producto(
            codigo_sku='TEST-001',
            nombre='Test',
            precio_venta_base=Decimal('-100.00')
        )
        with self.assertRaises(ValidationError) as context:
            producto.clean()
        self.assertIn('precio_venta_base', context.exception.message_dict)

    def test_validacion_itbis_rango(self):
        """Test: ITBIS fuera de rango falla validación"""
        producto = Producto(
            codigo_sku='TEST-001',
            nombre='Test',
            precio_venta_base=Decimal('100.00'),
            impuesto_itbis=Decimal('150.00')
        )
        with self.assertRaises(ValidationError) as context:
            producto.clean()
        self.assertIn('impuesto_itbis', context.exception.message_dict)

    def test_validacion_descuento_rango(self):
        """Test: Descuento fuera de rango falla validación"""
        producto = Producto(
            codigo_sku='TEST-001',
            nombre='Test',
            precio_venta_base=Decimal('100.00'),
            porcentaje_descuento_promocional=Decimal('120.00')
        )
        with self.assertRaises(ValidationError) as context:
            producto.clean()
        self.assertIn('porcentaje_descuento_promocional', context.exception.message_dict)

    def test_producto_exento_itbis_cero(self):
        """Test: Producto exento tiene ITBIS en 0"""
        producto = Producto(
            codigo_sku='EXENTO-001',
            nombre='Libro',
            precio_venta_base=Decimal('500.00'),
            es_exento=True,
            impuesto_itbis=Decimal('18.00')  # Se forzará a 0
        )
        producto.clean()
        self.assertEqual(producto.impuesto_itbis, Decimal('0.00'))

    def test_producto_sin_garantia_meses_cero(self):
        """Test: Producto sin garantía tiene meses en 0"""
        producto = Producto(
            codigo_sku='TEST-001',
            nombre='Test',
            precio_venta_base=Decimal('100.00'),
            tiene_garantia=False,
            meses_garantia=12  # Se forzará a 0
        )
        producto.clean()
        self.assertEqual(producto.meses_garantia, 0)

    def test_producto_con_garantia(self):
        """Test: Producto con garantía"""
        producto = Producto.objects.create(
            codigo_sku='GAR-001',
            nombre='Electrodoméstico',
            precio_venta_base=Decimal('5000.00'),
            tiene_garantia=True,
            meses_garantia=12
        )
        self.assertTrue(producto.tiene_garantia)
        self.assertEqual(producto.meses_garantia, 12)

    def test_nombre_normalizado(self):
        """Test: Nombre se normaliza (strip)"""
        producto = Producto(
            codigo_sku='TEST-001',
            nombre='  Producto Test  ',
            precio_venta_base=Decimal('100.00')
        )
        producto.clean()
        self.assertEqual(producto.nombre, 'Producto Test')

    def test_sku_normalizado(self):
        """Test: SKU se normaliza (strip)"""
        producto = Producto(
            codigo_sku='  TEST-001  ',
            nombre='Test',
            precio_venta_base=Decimal('100.00')
        )
        producto.clean()
        self.assertEqual(producto.codigo_sku, 'TEST-001')

    def test_producto_con_categorias(self):
        """Test: Producto con múltiples categorías"""
        cat1 = Categoria.objects.create(nombre='Electrónicos')
        cat2 = Categoria.objects.create(nombre='Hogar')
        producto = Producto.objects.create(
            codigo_sku='MULTI-001',
            nombre='TV Smart',
            precio_venta_base=Decimal('15000.00')
        )
        producto.categorias.add(cat1, cat2)
        self.assertEqual(producto.categorias.count(), 2)


class ProductoSerializerTest(TestCase):
    """Tests para el serializer de Producto"""

    def test_calculo_precio_final(self):
        """Prueba que el precio final se calcule correctamente con el ITBIS"""
        producto = Producto.objects.create(
            codigo_sku="TEST-001",
            nombre="Producto Test",
            precio_venta_base=Decimal('100.00'),
            impuesto_itbis=Decimal('18.00'),
            tipo_producto='ALMACENABLE'
        )
        serializer = ProductoSerializer(producto)
        # 100 + 18% = 118.00
        self.assertEqual(serializer.data['precio_final_estimado'], 118.00)

    def test_calculo_precio_final_con_descuento(self):
        """Prueba precio final con descuento promocional del 10%"""
        producto = Producto.objects.create(
            codigo_sku="TEST-DESC",
            nombre="Producto Descuento",
            precio_venta_base=Decimal('100.00'),
            impuesto_itbis=Decimal('18.00'),
            porcentaje_descuento_promocional=Decimal('10.00'),
            tipo_producto='ALMACENABLE'
        )
        serializer = ProductoSerializer(producto)
        # Precio Base: 100
        # Descuento 10%: -10 -> Nuevo Base: 90
        # ITBIS 18% sobre 90: 16.2
        # Total: 90 + 16.2 = 106.20
        self.assertEqual(serializer.data['precio_final_estimado'], 106.20)

    def test_calculo_precio_final_producto_exento(self):
        """Prueba precio final de producto exento (sin ITBIS)"""
        producto = Producto.objects.create(
            codigo_sku="EXENTO-001",
            nombre="Libro",
            precio_venta_base=Decimal('500.00'),
            es_exento=True,
            tipo_producto='ALMACENABLE'
        )
        serializer = ProductoSerializer(producto)
        # Sin ITBIS
        self.assertEqual(serializer.data['precio_final_estimado'], 500.00)

    def test_validacion_sku_invalido(self):
        """Prueba que el SKU rechace caracteres especiales"""
        data = {
            'codigo_sku': 'INVALIDO/SKU',  # Caracter / no permitido
            'nombre': 'Test',
            'precio_venta_base': 100,
            'impuesto_itbis': 18
        }
        serializer = ProductoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('codigo_sku', serializer.errors)

    def test_validacion_sku_valido(self):
        """Prueba que el SKU acepte caracteres válidos"""
        data = {
            'codigo_sku': 'PROD-001_ABC',
            'nombre': 'Test',
            'precio_venta_base': 100,
            'impuesto_itbis': 18
        }
        serializer = ProductoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validacion_impuesto_rango(self):
        """Prueba que el ITBIS no pueda ser mayor a 100"""
        data = {
            'codigo_sku': 'TEST-002',
            'nombre': 'Test',
            'precio_venta_base': 100,
            'impuesto_itbis': 150  # Invalido
        }
        serializer = ProductoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('impuesto_itbis', serializer.errors)

    def test_validacion_descuento_rango(self):
        """Prueba que el descuento no pueda ser mayor a 100"""
        data = {
            'codigo_sku': 'TEST-003',
            'nombre': 'Test',
            'precio_venta_base': 100,
            'impuesto_itbis': 18,
            'porcentaje_descuento_promocional': 120  # Invalido
        }
        serializer = ProductoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('porcentaje_descuento_promocional', serializer.errors)


class ProductoAPITest(APITestCase):
    """Tests para la API de Producto"""

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

        # Asignar permisos al usuario
        content_type = ContentType.objects.get_for_model(Producto)
        for codename in ['view_producto', 'add_producto', 'change_producto', 'delete_producto']:
            perm = Permission.objects.get(codename=codename, content_type=content_type)
            self.user.user_permissions.add(perm)

        content_type_cat = ContentType.objects.get_for_model(Categoria)
        for codename in ['view_categoria', 'add_categoria', 'change_categoria', 'delete_categoria']:
            perm = Permission.objects.get(codename=codename, content_type=content_type_cat)
            self.user.user_permissions.add(perm)

        self.categoria = Categoria.objects.create(
            nombre='Electrónicos'
        )

        self.producto = Producto.objects.create(
            codigo_sku='PROD-001',
            nombre='Laptop',
            precio_venta_base=Decimal('25000.00'),
            impuesto_itbis=Decimal('18.00'),
            tipo_producto='ALMACENABLE'
        )
        self.producto.categorias.add(self.categoria)

        self.client = APIClient()

    def test_listar_productos(self):
        """Test: Listar productos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/productos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_crear_producto(self):
        """Test: Crear producto"""
        self.client.force_authenticate(user=self.user)
        data = {
            'codigo_sku': 'NEW-001',
            'nombre': 'Nuevo Producto',
            'precio_venta_base': '1500.00',
            'impuesto_itbis': '18.00',
            'tipo_producto': 'ALMACENABLE'
        }
        response = self.client.post('/api/v1/productos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Nuevo Producto')

    def test_obtener_producto(self):
        """Test: Obtener producto por ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/productos/{self.producto.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Laptop')

    def test_actualizar_producto(self):
        """Test: Actualizar producto"""
        self.client.force_authenticate(user=self.user)
        data = {'nombre': 'Laptop Gaming'}
        response = self.client.patch(f'/api/v1/productos/{self.producto.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Laptop Gaming')

    def test_buscar_productos(self):
        """Test: Buscar productos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/productos/?search=Laptop')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación recibe 401"""
        response = self.client.get('/api/v1/productos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crear_producto_sku_invalido(self):
        """Test: Crear producto con SKU inválido"""
        self.client.force_authenticate(user=self.user)
        data = {
            'codigo_sku': 'INVALID/SKU',
            'nombre': 'Test',
            'precio_venta_base': '100.00'
        }
        response = self.client.post('/api/v1/productos/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_producto_precio_negativo(self):
        """Test: Crear producto con precio negativo"""
        self.client.force_authenticate(user=self.user)
        data = {
            'codigo_sku': 'NEG-001',
            'nombre': 'Test',
            'precio_venta_base': '-100.00'
        }
        response = self.client.post('/api/v1/productos/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_categorias(self):
        """Test: Listar categorías"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/categorias/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_categoria(self):
        """Test: Crear categoría"""
        self.client.force_authenticate(user=self.user)
        data = {
            'nombre': 'Nueva Categoría',
            'descripcion': 'Descripción de prueba'
        }
        response = self.client.post('/api/v1/categorias/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ordenar_productos_por_nombre(self):
        """Test: Ordenar productos por nombre"""
        Producto.objects.create(
            codigo_sku='AAA-001',
            nombre='AAA Producto',
            precio_venta_base=Decimal('100.00')
        )
        Producto.objects.create(
            codigo_sku='ZZZ-001',
            nombre='ZZZ Producto',
            precio_venta_base=Decimal('100.00')
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/productos/?ordering=nombre')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nombres = [p['nombre'] for p in response.data['results']]
        self.assertEqual(nombres, sorted(nombres))


# ======================= TESTS IMAGEN PRODUCTO =======================

class ImagenProductoModelTest(TestCase):
    """Tests para el modelo ImagenProducto"""

    def setUp(self):
        from productos.models import ImagenProducto
        self.ImagenProducto = ImagenProducto
        self.producto = Producto.objects.create(
            codigo_sku='IMG-001',
            nombre='Producto con Imagen',
            precio_venta_base=Decimal('100.00')
        )

    def test_primera_imagen_es_principal(self):
        """Test: Primera imagen se marca como principal automáticamente"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Crear una imagen falsa
        imagen = self.ImagenProducto(
            producto=self.producto,
            titulo='Imagen Principal',
            orden=0
        )
        # Sin imagen real, solo verificamos la lógica del save
        imagen.imagen = 'test.jpg'
        imagen.save()
        self.assertTrue(imagen.es_principal)

    def test_imagen_str(self):
        """Test: Representación string de imagen"""
        imagen = self.ImagenProducto(
            producto=self.producto,
            titulo='Imagen Test',
            orden=1
        )
        imagen.imagen = 'test.jpg'
        imagen.save()
        self.assertIn('IMG-001', str(imagen))
        self.assertIn('Imagen', str(imagen))

    def test_orden_imagenes(self):
        """Test: Orden de imágenes"""
        img1 = self.ImagenProducto(producto=self.producto, titulo='Primera', orden=0)
        img1.imagen = 'test1.jpg'
        img1.save()

        img2 = self.ImagenProducto(producto=self.producto, titulo='Segunda', orden=1)
        img2.imagen = 'test2.jpg'
        img2.save()

        img3 = self.ImagenProducto(producto=self.producto, titulo='Tercera', orden=2)
        img3.imagen = 'test3.jpg'
        img3.save()

        imagenes = self.ImagenProducto.objects.filter(producto=self.producto).order_by('orden')
        self.assertEqual(imagenes[0].titulo, 'Primera')
        self.assertEqual(imagenes[1].titulo, 'Segunda')
        self.assertEqual(imagenes[2].titulo, 'Tercera')


class ImagenProductoAPITest(APITestCase):
    """Tests para la API de ImagenProducto"""

    def setUp(self):
        from productos.models import ImagenProducto
        self.ImagenProducto = ImagenProducto
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
        self.producto = Producto.objects.create(
            codigo_sku='API-IMG-001',
            nombre='Producto API Imagen',
            precio_venta_base=Decimal('100.00')
        )
        self.imagen = self.ImagenProducto(
            producto=self.producto,
            titulo='Imagen Test',
            orden=0
        )
        self.imagen.imagen = 'test.jpg'
        self.imagen.save()
        self.client = APIClient()

    def test_listar_imagenes(self):
        """Test: Listar imágenes"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/imagenes-producto/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_por_producto_endpoint(self):
        """Test: Endpoint por_producto"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/api/v1/imagenes-producto/por_producto/?producto_id={self.producto.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_marcar_principal(self):
        """Test: Marcar imagen como principal"""
        # Crear segunda imagen
        img2 = self.ImagenProducto(producto=self.producto, titulo='Segunda', orden=1)
        img2.imagen = 'test2.jpg'
        img2.save()

        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(f'/api/v1/imagenes-producto/{img2.id}/marcar_principal/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        img2.refresh_from_db()
        self.assertTrue(img2.es_principal)


# ======================= TESTS REFERENCIAS CRUZADAS =======================

class ReferenciasCruzadasModelTest(TestCase):
    """Tests para el modelo ReferenciasCruzadas"""

    def setUp(self):
        from productos.models import ReferenciasCruzadas
        self.ReferenciasCruzadas = ReferenciasCruzadas
        self.producto1 = Producto.objects.create(
            codigo_sku='REF-001',
            nombre='Producto 1',
            precio_venta_base=Decimal('100.00')
        )
        self.producto2 = Producto.objects.create(
            codigo_sku='REF-002',
            nombre='Producto 2',
            precio_venta_base=Decimal('150.00')
        )

    def test_crear_referencia_relacionado(self):
        """Test: Crear referencia de producto relacionado"""
        ref = self.ReferenciasCruzadas.objects.create(
            producto_origen=self.producto1,
            producto_destino=self.producto2,
            tipo='RELACIONADO'
        )
        self.assertEqual(ref.tipo, 'RELACIONADO')
        self.assertTrue(ref.bidireccional)
        self.assertTrue(ref.activa)

    def test_crear_referencia_sustituto(self):
        """Test: Crear referencia de producto sustituto"""
        ref = self.ReferenciasCruzadas.objects.create(
            producto_origen=self.producto1,
            producto_destino=self.producto2,
            tipo='SUSTITUTO'
        )
        self.assertEqual(ref.tipo, 'SUSTITUTO')

    def test_referencia_str(self):
        """Test: Representación string de referencia"""
        ref = self.ReferenciasCruzadas.objects.create(
            producto_origen=self.producto1,
            producto_destino=self.producto2,
            tipo='ACCESORIO'
        )
        self.assertIn('REF-001', str(ref))
        self.assertIn('REF-002', str(ref))
        self.assertIn('Accesorio', str(ref))

    def test_validacion_mismo_producto(self):
        """Test: No se puede crear referencia al mismo producto"""
        ref = self.ReferenciasCruzadas(
            producto_origen=self.producto1,
            producto_destino=self.producto1,
            tipo='RELACIONADO'
        )
        with self.assertRaises(ValidationError):
            ref.clean()


class ReferenciasCruzadasAPITest(APITestCase):
    """Tests para la API de ReferenciasCruzadas"""

    def setUp(self):
        from productos.models import ReferenciasCruzadas
        self.ReferenciasCruzadas = ReferenciasCruzadas
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
        self.producto1 = Producto.objects.create(
            codigo_sku='API-REF-001',
            nombre='Producto API 1',
            precio_venta_base=Decimal('100.00')
        )
        self.producto2 = Producto.objects.create(
            codigo_sku='API-REF-002',
            nombre='Producto API 2',
            precio_venta_base=Decimal('150.00')
        )
        self.referencia = self.ReferenciasCruzadas.objects.create(
            producto_origen=self.producto1,
            producto_destino=self.producto2,
            tipo='RELACIONADO'
        )
        self.client = APIClient()

    def test_listar_referencias(self):
        """Test: Listar referencias"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/v1/referencias-producto/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_referencia(self):
        """Test: Crear referencia"""
        producto3 = Producto.objects.create(
            codigo_sku='API-REF-003',
            nombre='Producto API 3',
            precio_venta_base=Decimal('200.00')
        )
        self.client.force_authenticate(user=self.superuser)
        data = {
            'producto_origen': self.producto1.id,
            'producto_destino': producto3.id,
            'tipo': 'SUSTITUTO'
        }
        response = self.client.post('/api/v1/referencias-producto/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_por_producto_endpoint(self):
        """Test: Endpoint por_producto"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/api/v1/referencias-producto/por_producto/?producto_id={self.producto1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sustitutos_endpoint(self):
        """Test: Endpoint sustitutos"""
        # Crear un sustituto
        producto3 = Producto.objects.create(
            codigo_sku='SUST-001',
            nombre='Sustituto',
            precio_venta_base=Decimal('120.00')
        )
        self.ReferenciasCruzadas.objects.create(
            producto_origen=self.producto1,
            producto_destino=producto3,
            tipo='SUSTITUTO'
        )

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f'/api/v1/referencias-producto/sustitutos/?producto_id={self.producto1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['codigo_sku'], 'SUST-001')

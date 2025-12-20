from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from productos.models import Producto, Categoria
from empresas.models import Empresa
from io import StringIO
import pandas as pd

User = get_user_model()

class UploadCatalogTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create empresa first
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test Upload',
            rnc='123456789'
        )
        # Create user with empresa
        self.user = User.objects.create_user(
            username='testuser',
            password='password',
            rol='admin',
            is_superuser=True,
            empresa=self.empresa
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/productos/upload-catalog/'

    def test_upload_catalog_multiple_categories(self):
        # Create CSV content
        data = {
            'codigo_sku': ['TEST-MULTI-CAT'],
            'nombre': ['Producto Multi Categoria'],
            'precio_venta_base': [100.0],
            'categoria': ['Electronica, Hogar, Ofertas']  # 3 categories
        }
        df = pd.DataFrame(data)

        # Save to a temporary buffer
        csv_file = StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)

        # Prepare file for upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test_catalog.csv", csv_file.getvalue().encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/v1/productos/upload-catalog/', {'file': file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)

        # Verify Product
        product = Producto.objects.get(codigo_sku='TEST-MULTI-CAT', empresa=self.empresa)
        self.assertEqual(product.nombre, 'Producto Multi Categoria')

        # Verify Categories
        self.assertEqual(product.categorias.count(), 3)
        cat_names = list(product.categorias.values_list('nombre', flat=True))
        self.assertIn('Electronica', cat_names)
        self.assertIn('Hogar', cat_names)
        self.assertIn('Ofertas', cat_names)

        # Verify all categories belong to the same empresa
        for cat in product.categorias.all():
            self.assertEqual(cat.empresa, self.empresa)

    def test_upload_catalog_update_existing(self):
        # Create initial product with empresa
        p = Producto.objects.create(
            empresa=self.empresa,
            codigo_sku='UPDATE-ME',
            nombre='Old Name',
            precio_venta_base=50
        )

        data = {
            'codigo_sku': ['UPDATE-ME'],
            'nombre': ['New Name'],
            'precio_venta_base': [75.0],
            'categoria': ['NuevaCat']
        }
        df = pd.DataFrame(data)
        csv_file = StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("update.csv", csv_file.getvalue().encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/v1/productos/upload-catalog/', {'file': file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated'], 1)

        p.refresh_from_db()
        self.assertEqual(p.nombre, 'New Name')
        self.assertEqual(float(p.precio_venta_base), 75.0)
        self.assertTrue(p.categorias.filter(nombre='NuevaCat').exists())

        # Verify category belongs to the same empresa
        cat = p.categorias.get(nombre='NuevaCat')
        self.assertEqual(cat.empresa, self.empresa)

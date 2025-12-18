from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from productos.models import Producto, Categoria
from io import StringIO
import pandas as pd

User = get_user_model()

class UploadCatalogTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password', rol='admin', is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/productos/upload-catalog/' # This might need adjustment based on router registration

    def test_upload_catalog_multiple_categories(self):
        # Create CSV content
        data = {
            'codigo_sku': ['TEST-MULTI-CAT'],
            'nombre': ['Producto Multi Categoria'],
            'precio_venta_base': [100.0],
            'categoria': ['Electronica, Hogar, Ofertas'] # 3 categories
        }
        df = pd.DataFrame(data)
        
        # Save to a temporary buffer
        csv_file = StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)
        
        # Prepare file for upload
        # We need to simulate a file object that Django accepts
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test_catalog.csv", csv_file.getvalue().encode('utf-8'), content_type="text/csv")
        
        # Determine the correct URL. usually router registers as 'productos' -> 'productos-upload-catalog' or similar
        # But let's try to find the URL name or just use the path if we know it.
        # Assuming router is registered at /api/v1/productos/
        
        response = self.client.post('/api/v1/productos/upload-catalog/', {'file': file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        
        # Verify Product
        product = Producto.objects.get(codigo_sku='TEST-MULTI-CAT')
        self.assertEqual(product.nombre, 'Producto Multi Categoria')
        
        # Verify Categories
        self.assertEqual(product.categorias.count(), 3)
        cat_names = list(product.categorias.values_list('nombre', flat=True))
        self.assertIn('Electronica', cat_names)
        self.assertIn('Hogar', cat_names)
        self.assertIn('Ofertas', cat_names)

    def test_upload_catalog_update_existing(self):
        # Create initial product
        p = Producto.objects.create(codigo_sku='UPDATE-ME', nombre='Old Name', precio_venta_base=50)
        
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
        self.assertEqual(p.precio_venta_base, 75.0)
        self.assertTrue(p.categorias.filter(nombre='NuevaCat').exists())

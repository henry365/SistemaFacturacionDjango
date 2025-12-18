from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas
from .serializers import (
    CategoriaSerializer,
    ProductoSerializer,
    ImagenProductoSerializer,
    ImagenProductoListSerializer,
    ReferenciasCruzadasSerializer,
    ReferenciasCruzadasListSerializer
)
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
import pandas as pd

class CategoriaViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering = ['nombre']

class ProductoViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'codigo_sku', 'descripcion']
    ordering_fields = ['nombre', 'precio_venta_base']

    @action(detail=False, methods=['post'], url_path='upload-catalog')
    def upload_catalog(self, request):
        """
        Carga masiva de productos desde archivo Excel (.xlsx) o CSV.
        Columnas esperadas: codigo_sku, nombre, precio_venta_base, impuesto_itbis, categoria (separadas por coma), es_servicio
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No se proporcionó ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Leer archivo con pandas
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Formato no soportado. Use .csv o .xlsx'}, status=status.HTTP_400_BAD_REQUEST)

            # Normalizar columnas a minúsculas
            df.columns = df.columns.str.lower().str.strip()
            
            required_cols = ['codigo_sku', 'nombre', 'precio_venta_base']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                return Response({'error': f'Faltan columnas requeridas: {", ".join(missing)}'}, status=status.HTTP_400_BAD_REQUEST)

            created_count = 0
            updated_count = 0
            errors = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        sku = str(row['codigo_sku']).strip()
                        if not sku or sku.lower() == 'nan':
                            continue

                        # Datos base
                        defaults = {
                            'nombre': row['nombre'],
                            'precio_venta_base': float(row['precio_venta_base']),
                            'descripcion': row.get('descripcion', ''),
                            'impuesto_itbis': float(row.get('impuesto_itbis', 18.00)),
                            'porcentaje_descuento_promocional': float(row.get('porcentaje_descuento_promocional', 0.00)),
                            'porcentaje_descuento_maximo': float(row.get('porcentaje_descuento_maximo', 0.00)),
                        }

                        # Mapear campos booleanos y opciones
                        es_servicio = str(row.get('es_servicio', '')).lower() in ['si', 'true', 'yes', '1']
                        if es_servicio:
                            defaults['tipo_producto'] = 'SERVICIO'
                            defaults['controlar_stock'] = False
                        else:
                             # Default is ALMACENABLE and controlar_stock=True
                             pass

                        # Actualizar o Crear
                        producto, created = Producto.objects.update_or_create(
                            codigo_sku=sku,
                            defaults=defaults
                        )

                        # Manejo de Categorías (Múltiples separadas por coma)
                        categoria_raw = row.get('categoria')
                        if categoria_raw and str(categoria_raw).lower() != 'nan':
                            # Convertir a string y separar por comas
                            categorias_nombres = [c.strip() for c in str(categoria_raw).split(',') if c.strip()]
                            
                            for cat_nombre in categorias_nombres:
                                categoria_obj, _ = Categoria.objects.get_or_create(
                                    nombre=cat_nombre
                                )
                                producto.categorias.add(categoria_obj)

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        errors.append(f"Fila {index + 2}: {str(e)}")
                
                if errors:
                    raise Exception(f"Errores encontrados: {'; '.join(errors[:5])}...")

            return Response({
                'message': 'Catálogo procesado correctamente',
                'created': created_count,
                'updated': updated_count
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImagenProductoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar imágenes de productos"""
    queryset = ImagenProducto.objects.select_related('producto').all()
    serializer_class = ImagenProductoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['producto', 'es_principal', 'activa']
    ordering_fields = ['orden', 'fecha_creacion']
    ordering = ['producto', 'orden']

    def get_serializer_class(self):
        if self.action == 'list':
            return ImagenProductoListSerializer
        return ImagenProductoSerializer

    @action(detail=False, methods=['get'])
    def por_producto(self, request):
        """Retorna todas las imágenes de un producto específico"""
        producto_id = request.query_params.get('producto_id')
        if not producto_id:
            return Response(
                {'error': 'Debe especificar producto_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        imagenes = self.get_queryset().filter(
            producto_id=producto_id,
            activa=True
        ).order_by('orden')
        serializer = ImagenProductoListSerializer(imagenes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_principal(self, request, pk=None):
        """Marca una imagen como principal del producto"""
        imagen = self.get_object()

        # Desmarcar otras como principal
        ImagenProducto.objects.filter(
            producto=imagen.producto,
            es_principal=True
        ).update(es_principal=False)

        # Marcar esta como principal
        imagen.es_principal = True
        imagen.save()

        return Response({'message': 'Imagen marcada como principal'})

    @action(detail=False, methods=['post'])
    def reordenar(self, request):
        """
        Reordena las imágenes de un producto.
        Espera: { "ordenamiento": [{"id": 1, "orden": 0}, {"id": 2, "orden": 1}, ...] }
        """
        ordenamiento = request.data.get('ordenamiento', [])
        if not ordenamiento:
            return Response(
                {'error': 'Debe proporcionar el ordenamiento'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for item in ordenamiento:
                ImagenProducto.objects.filter(id=item['id']).update(orden=item['orden'])

        return Response({'message': 'Imágenes reordenadas correctamente'})


class ReferenciasCruzadasViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar referencias cruzadas entre productos"""
    queryset = ReferenciasCruzadas.objects.select_related(
        'producto_origen', 'producto_destino'
    ).all()
    serializer_class = ReferenciasCruzadasSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['producto_origen', 'producto_destino', 'tipo', 'activa', 'bidireccional']
    ordering_fields = ['tipo', 'fecha_creacion']
    ordering = ['producto_origen', 'tipo']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReferenciasCruzadasListSerializer
        return ReferenciasCruzadasSerializer

    @action(detail=False, methods=['get'])
    def por_producto(self, request):
        """
        Retorna todas las referencias de un producto (como origen o destino si bidireccional).
        """
        producto_id = request.query_params.get('producto_id')
        if not producto_id:
            return Response(
                {'error': 'Debe especificar producto_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.db.models import Q

        # Referencias donde el producto es origen
        referencias_origen = self.get_queryset().filter(
            producto_origen_id=producto_id,
            activa=True
        )

        # Referencias bidireccionales donde el producto es destino
        referencias_destino = self.get_queryset().filter(
            producto_destino_id=producto_id,
            bidireccional=True,
            activa=True
        )

        # Combinar resultados
        todas = list(referencias_origen) + list(referencias_destino)

        # Serializar (mostrar el producto relacionado, no el propio)
        resultado = []
        for ref in referencias_origen:
            resultado.append({
                'id': ref.id,
                'producto_relacionado_id': ref.producto_destino_id,
                'producto_relacionado_codigo': ref.producto_destino.codigo_sku,
                'producto_relacionado_nombre': ref.producto_destino.nombre,
                'tipo': ref.tipo,
                'tipo_display': ref.get_tipo_display(),
                'direccion': 'saliente'
            })

        for ref in referencias_destino:
            resultado.append({
                'id': ref.id,
                'producto_relacionado_id': ref.producto_origen_id,
                'producto_relacionado_codigo': ref.producto_origen.codigo_sku,
                'producto_relacionado_nombre': ref.producto_origen.nombre,
                'tipo': ref.tipo,
                'tipo_display': ref.get_tipo_display(),
                'direccion': 'entrante'
            })

        return Response(resultado)

    @action(detail=False, methods=['get'])
    def sustitutos(self, request):
        """Retorna productos sustitutos de un producto específico"""
        producto_id = request.query_params.get('producto_id')
        if not producto_id:
            return Response(
                {'error': 'Debe especificar producto_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        referencias = self.get_queryset().filter(
            producto_origen_id=producto_id,
            tipo='SUSTITUTO',
            activa=True
        )

        productos_sustitutos = [
            {
                'id': ref.producto_destino.id,
                'codigo_sku': ref.producto_destino.codigo_sku,
                'nombre': ref.producto_destino.nombre,
                'precio_venta_base': str(ref.producto_destino.precio_venta_base)
            }
            for ref in referencias
        ]

        return Response(productos_sustitutos)

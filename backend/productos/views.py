"""
ViewSets para el módulo Productos

Este módulo contiene los ViewSets para gestión de productos, categorías,
imágenes y referencias cruzadas.

Incluye soporte para multi-tenancy con filtrado y asignación automática de empresa.
"""
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas
from .serializers import (
    CategoriaSerializer,
    CategoriaListSerializer,
    ProductoSerializer,
    ProductoListSerializer,
    ImagenProductoSerializer,
    ImagenProductoListSerializer,
    ReferenciasCruzadasSerializer,
    ReferenciasCruzadasListSerializer
)
from .permissions import (
    CanGestionarCategoria,
    CanGestionarProducto,
    CanCargarCatalogo,
    CanGestionarImagenes,
    CanGestionarReferencias
)
from .constants import (
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MAX,
    FORMATOS_ARCHIVO_SOPORTADOS,
    COLUMNAS_REQUERIDAS_CATALOGO,
    ERROR_ARCHIVO_NO_PROPORCIONADO,
    ERROR_FORMATO_NO_SOPORTADO,
    ERROR_COLUMNAS_FALTANTES
)
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin
from usuarios.permissions import ActionBasedPermission


logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN
# =============================================================================

class ProductosPagination(PageNumberPagination):
    """Paginación personalizada para el módulo Productos"""
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# VIEWSETS
# =============================================================================

class CategoriaViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de productos.

    Endpoints:
    - GET /categorias/ - Lista todas las categorías (filtrado por empresa)
    - POST /categorias/ - Crea una nueva categoría (asigna empresa del usuario)
    - GET /categorias/{id}/ - Obtiene una categoría
    - PUT /categorias/{id}/ - Actualiza una categoría
    - DELETE /categorias/{id}/ - Elimina una categoría
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    pagination_class = ProductosPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activa']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarCategoria()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return CategoriaListSerializer
        return CategoriaSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con prefetch_related.
        """
        qs = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            qs = qs.prefetch_related('productos')
        return qs

    def perform_create(self, serializer):
        """
        Guarda la categoría con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(f"Categoría creada: {instance.nombre} (id={instance.id}) empresa={instance.empresa_id} por usuario {self.request.user.username}")

    def perform_update(self, serializer):
        """
        Actualiza la categoría y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(f"Categoría actualizada: {instance.nombre} (id={instance.id}) por usuario {self.request.user.username}")

    def perform_destroy(self, instance):
        """
        Elimina la categoría y registra la acción.
        """
        nombre = instance.nombre
        instance_id = instance.id
        super().perform_destroy(instance)
        logger.info(f"Categoría eliminada: {nombre} (id={instance_id}) por usuario {self.request.user.username}")


class ProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos.

    Endpoints:
    - GET /productos/ - Lista todos los productos (filtrado por empresa)
    - POST /productos/ - Crea un nuevo producto (asigna empresa del usuario)
    - GET /productos/{id}/ - Obtiene un producto
    - PUT /productos/{id}/ - Actualiza un producto
    - DELETE /productos/{id}/ - Elimina un producto
    - POST /productos/upload-catalog/ - Carga masiva de productos
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    pagination_class = ProductosPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'tipo_producto', 'es_exento', 'controlar_stock', 'tiene_garantia', 'categorias']
    search_fields = ['nombre', 'codigo_sku', 'descripcion']
    ordering_fields = ['nombre', 'codigo_sku', 'precio_venta_base', 'fecha_creacion']
    ordering = ['nombre']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action == 'upload_catalog':
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanCargarCatalogo()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarProducto()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return ProductoListSerializer
        return ProductoSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con prefetch_related.
        """
        qs = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            qs = qs.prefetch_related('categorias', 'imagenes')
        return qs

    def perform_create(self, serializer):
        """
        Guarda el producto con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(f"Producto creado: {instance.codigo_sku} - {instance.nombre} (id={instance.id}) empresa={instance.empresa_id} por usuario {self.request.user.username}")

    def perform_update(self, serializer):
        """
        Actualiza el producto y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(f"Producto actualizado: {instance.codigo_sku} - {instance.nombre} (id={instance.id}) por usuario {self.request.user.username}")

    def perform_destroy(self, instance):
        """
        Elimina el producto y registra la acción.
        """
        codigo_sku = instance.codigo_sku
        nombre = instance.nombre
        instance_id = instance.id
        super().perform_destroy(instance)
        logger.info(f"Producto eliminado: {codigo_sku} - {nombre} (id={instance_id}) por usuario {self.request.user.username}")

    @action(detail=False, methods=['post'], url_path='upload-catalog')
    def upload_catalog(self, request):
        """
        Carga masiva de productos desde archivo Excel (.xlsx) o CSV.
        Todos los productos se asignan a la empresa del usuario.

        Columnas esperadas:
        - codigo_sku (requerido)
        - nombre (requerido)
        - precio_venta_base (requerido)
        - impuesto_itbis
        - categoria (múltiples separadas por coma)
        - es_servicio
        - descripcion
        - porcentaje_descuento_promocional
        - porcentaje_descuento_maximo
        """
        import pandas as pd

        # Verificar que el usuario tenga empresa asignada
        user = request.user
        if not hasattr(user, 'empresa') or not user.empresa:
            logger.warning(f"Usuario {user.username} sin empresa intentó cargar catálogo")
            return Response(
                {'error': 'Usuario no tiene empresa asignada'},
                status=status.HTTP_403_FORBIDDEN
            )

        empresa = user.empresa

        file = request.FILES.get('file')
        if not file:
            logger.warning(f"Intento de carga de catálogo sin archivo por usuario {request.user.username}")
            return Response({'error': ERROR_ARCHIVO_NO_PROPORCIONADO}, status=status.HTTP_400_BAD_REQUEST)

        # Validar formato de archivo
        file_ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
        if file_ext not in FORMATOS_ARCHIVO_SOPORTADOS:
            logger.warning(f"Formato de archivo no soportado: {file.name} por usuario {request.user.username}")
            return Response({'error': ERROR_FORMATO_NO_SOPORTADO}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Leer archivo con pandas
            if file_ext == '.csv':
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Normalizar columnas a minúsculas
            df.columns = df.columns.str.lower().str.strip()

            # Validar columnas requeridas
            missing = [col for col in COLUMNAS_REQUERIDAS_CATALOGO if col not in df.columns]
            if missing:
                logger.warning(f"Columnas faltantes en catálogo: {missing} por usuario {request.user.username}")
                return Response(
                    {'error': ERROR_COLUMNAS_FALTANTES.format(columnas=', '.join(missing))},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
                            'usuario_modificacion': request.user,
                        }

                        # Mapear campos booleanos y opciones
                        es_servicio = str(row.get('es_servicio', '')).lower() in ['si', 'true', 'yes', '1']
                        if es_servicio:
                            defaults['tipo_producto'] = 'SERVICIO'
                            defaults['controlar_stock'] = False

                        # Actualizar o Crear (filtrar por empresa y SKU)
                        producto, created = Producto.objects.update_or_create(
                            empresa=empresa,
                            codigo_sku=sku,
                            defaults=defaults
                        )

                        if created:
                            producto.usuario_creacion = request.user
                            producto.save(update_fields=['usuario_creacion'])

                        # Manejo de Categorías (Múltiples separadas por coma)
                        categoria_raw = row.get('categoria')
                        if categoria_raw and str(categoria_raw).lower() != 'nan':
                            categorias_nombres = [c.strip() for c in str(categoria_raw).split(',') if c.strip()]

                            for cat_nombre in categorias_nombres:
                                categoria_obj, _ = Categoria.objects.get_or_create(
                                    empresa=empresa,
                                    nombre=cat_nombre,
                                    defaults={
                                        'usuario_creacion': request.user,
                                        'usuario_modificacion': request.user
                                    }
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

            logger.info(f"Catálogo cargado: {created_count} creados, {updated_count} actualizados para empresa {empresa.id} por usuario {request.user.username}")

            return Response({
                'message': 'Catálogo procesado correctamente',
                'created': created_count,
                'updated': updated_count
            })

        except Exception as e:
            logger.error(f"Error en carga de catálogo: {str(e)} por usuario {request.user.username}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImagenProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar imágenes de productos.

    Endpoints:
    - GET /imagenes-producto/ - Lista todas las imágenes (filtrado por empresa)
    - POST /imagenes-producto/ - Crea una nueva imagen
    - GET /imagenes-producto/{id}/ - Obtiene una imagen
    - PUT /imagenes-producto/{id}/ - Actualiza una imagen
    - DELETE /imagenes-producto/{id}/ - Elimina una imagen
    - GET /imagenes-producto/por_producto/ - Imágenes de un producto
    - POST /imagenes-producto/{id}/marcar_principal/ - Marca como principal
    - POST /imagenes-producto/reordenar/ - Reordena imágenes
    """
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer
    pagination_class = ProductosPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['producto', 'es_principal', 'activa']
    search_fields = ['titulo', 'descripcion', 'producto__codigo_sku', 'producto__nombre']
    ordering_fields = ['orden', 'fecha_creacion']
    ordering = ['producto', 'orden']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'marcar_principal', 'reordenar']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarImagenes()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return ImagenProductoListSerializer
        return ImagenProductoSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con select_related.
        """
        return super().get_queryset().select_related('producto', 'empresa')

    def perform_create(self, serializer):
        """
        Guarda la imagen con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(f"Imagen creada para producto {instance.producto.codigo_sku} (id={instance.id}) por usuario {self.request.user.username}")

    def perform_update(self, serializer):
        """
        Actualiza la imagen y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(f"Imagen actualizada (id={instance.id}) por usuario {self.request.user.username}")

    def perform_destroy(self, instance):
        """
        Elimina la imagen y registra la acción.
        """
        instance_id = instance.id
        producto_sku = instance.producto.codigo_sku
        super().perform_destroy(instance)
        logger.info(f"Imagen eliminada (id={instance_id}) del producto {producto_sku} por usuario {self.request.user.username}")

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
        imagen.usuario_modificacion = request.user
        imagen.save()

        logger.info(f"Imagen {imagen.id} marcada como principal para producto {imagen.producto.codigo_sku} por usuario {request.user.username}")

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

        logger.info(f"Imágenes reordenadas: {len(ordenamiento)} elementos por usuario {request.user.username}")

        return Response({'message': 'Imágenes reordenadas correctamente'})


class ReferenciasCruzadasViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar referencias cruzadas entre productos.

    Endpoints:
    - GET /referencias-producto/ - Lista todas las referencias (filtrado por empresa)
    - POST /referencias-producto/ - Crea una nueva referencia
    - GET /referencias-producto/{id}/ - Obtiene una referencia
    - PUT /referencias-producto/{id}/ - Actualiza una referencia
    - DELETE /referencias-producto/{id}/ - Elimina una referencia
    - GET /referencias-producto/por_producto/ - Referencias de un producto
    - GET /referencias-producto/sustitutos/ - Sustitutos de un producto
    """
    queryset = ReferenciasCruzadas.objects.all()
    serializer_class = ReferenciasCruzadasSerializer
    pagination_class = ProductosPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['producto_origen', 'producto_destino', 'tipo', 'activa', 'bidireccional']
    search_fields = [
        'producto_origen__codigo_sku', 'producto_origen__nombre',
        'producto_destino__codigo_sku', 'producto_destino__nombre'
    ]
    ordering_fields = ['tipo', 'fecha_creacion']
    ordering = ['producto_origen', 'tipo']

    def get_permissions(self):
        """
        Retorna los permisos requeridos según la acción.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), ActionBasedPermission(), CanGestionarReferencias()]
        return [permissions.IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """
        Retorna el serializer según la acción.
        """
        if self.action == 'list':
            return ReferenciasCruzadasListSerializer
        return ReferenciasCruzadasSerializer

    def get_queryset(self):
        """
        Filtra por empresa y optimiza con select_related.
        """
        return super().get_queryset().select_related('producto_origen', 'producto_destino', 'empresa')

    def perform_create(self, serializer):
        """
        Guarda la referencia con empresa y usuario de creación.
        """
        super().perform_create(serializer)
        instance = serializer.instance
        logger.info(
            f"Referencia creada: {instance.producto_origen.codigo_sku} -> {instance.producto_destino.codigo_sku} "
            f"({instance.get_tipo_display()}) por usuario {self.request.user.username}"
        )

    def perform_update(self, serializer):
        """
        Actualiza la referencia y registra el usuario de modificación.
        """
        super().perform_update(serializer)
        instance = serializer.instance
        logger.info(f"Referencia actualizada (id={instance.id}) por usuario {self.request.user.username}")

    def perform_destroy(self, instance):
        """
        Elimina la referencia y registra la acción.
        """
        instance_id = instance.id
        origen_sku = instance.producto_origen.codigo_sku
        destino_sku = instance.producto_destino.codigo_sku
        super().perform_destroy(instance)
        logger.info(f"Referencia eliminada (id={instance_id}): {origen_sku} -> {destino_sku} por usuario {self.request.user.username}")

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

"""
ViewSets para el módulo de Clientes

Este módulo implementa los ViewSets para Cliente y CategoriaCliente,
siguiendo los estándares de la Guía Inicial.
"""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Cliente, CategoriaCliente
from .serializers import (
    ClienteSerializer, ClienteListSerializer,
    CategoriaClienteSerializer, CategoriaClienteListSerializer
)
from .services import ClienteService, CategoriaClienteService
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin


# ============================================================
# PAGINACIÓN
# ============================================================

class ClientesPagination(PageNumberPagination):
    """Paginación personalizada para Cliente"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoriasClientePagination(PageNumberPagination):
    """Paginación personalizada para CategoriaCliente"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================
# VIEWSETS
# ============================================================

class CategoriaClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Categorías de Clientes.

    Endpoints:
        GET /categorias-clientes/ - Listar categorías
        POST /categorias-clientes/ - Crear categoría
        GET /categorias-clientes/{id}/ - Detalle de categoría
        PUT/PATCH /categorias-clientes/{id}/ - Actualizar categoría
        DELETE /categorias-clientes/{id}/ - Eliminar categoría
        POST /categorias-clientes/{id}/activar/ - Activar categoría
        POST /categorias-clientes/{id}/desactivar/ - Desactivar categoría
        GET /categorias-clientes/{id}/estadisticas/ - Estadísticas de categoría

    Filtros disponibles:
        - activa: Filtrar por estado activo (true/false)
        - search: Buscar por nombre o descripción
        - ordering: Ordenar por nombre, descuento_porcentaje, fecha_creacion

    Ejemplo Request (POST /categorias-clientes/):
        {
            "nombre": "VIP",
            "descripcion": "Clientes VIP con descuento especial",
            "descuento_porcentaje": "15.00"
        }

    Ejemplo Response:
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "nombre": "VIP",
            "descripcion": "Clientes VIP con descuento especial",
            "descuento_porcentaje": "15.00",
            "activa": true,
            "fecha_creacion": "2025-01-27T10:30:00Z"
        }
    """
    queryset = CategoriaCliente.objects.select_related(
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    pagination_class = CategoriasClientePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activa']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'descuento_porcentaje', 'fecha_creacion']
    ordering = ['nombre']

    def get_serializer_class(self):
        """Retorna serializer según la acción"""
        if self.action == 'list':
            return CategoriaClienteListSerializer
        return CategoriaClienteSerializer

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa una categoría de clientes.

        POST /categorias-clientes/{id}/activar/
        """
        categoria = self.get_object()
        exito, error = CategoriaClienteService.activar_categoria(
            categoria=categoria,
            ejecutado_por=request.user
        )
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Categoría "{categoria.nombre}" activada correctamente'})

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Desactiva una categoría de clientes.

        POST /categorias-clientes/{id}/desactivar/
        """
        categoria = self.get_object()
        exito, error = CategoriaClienteService.desactivar_categoria(
            categoria=categoria,
            ejecutado_por=request.user
        )
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Categoría "{categoria.nombre}" desactivada correctamente'})

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtiene estadísticas de una categoría de clientes.

        GET /categorias-clientes/{id}/estadisticas/
        """
        categoria = self.get_object()
        estadisticas, error = CategoriaClienteService.obtener_estadisticas(categoria)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(estadisticas)


class ClienteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Clientes.

    Endpoints:
        GET /clientes/ - Listar clientes
        POST /clientes/ - Crear cliente
        GET /clientes/{id}/ - Detalle de cliente
        PUT/PATCH /clientes/{id}/ - Actualizar cliente
        DELETE /clientes/{id}/ - Eliminar cliente
        POST /clientes/{id}/activar/ - Activar cliente
        POST /clientes/{id}/desactivar/ - Desactivar cliente
        GET /clientes/{id}/historial_compras/ - Historial de compras
        GET /clientes/{id}/historial_pagos/ - Historial de pagos
        GET /clientes/{id}/resumen/ - Resumen completo con estadísticas
        POST /clientes/{id}/actualizar_limite_credito/ - Actualizar límite de crédito

    Filtros disponibles:
        - activo: Filtrar por estado activo (true/false)
        - categoria: Filtrar por ID de categoría
        - vendedor: Filtrar por ID de vendedor asignado
        - tipo_identificacion: Filtrar por tipo (RNC, CEDULA, PASAPORTE, OTRO)
        - search: Buscar por nombre, número identificación, teléfono, email
        - ordering: Ordenar por nombre, fecha_creacion, limite_credito

    Ejemplo Request (POST /clientes/):
        {
            "nombre": "Empresa ABC S.A.",
            "tipo_identificacion": "RNC",
            "numero_identificacion": "123456789",
            "telefono": "809-555-1234",
            "correo_electronico": "contacto@empresaabc.com",
            "direccion": "Calle Principal #123",
            "limite_credito": "50000.00",
            "categoria": 1
        }

    Ejemplo Response:
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "nombre": "Empresa ABC S.A.",
            "tipo_identificacion": "RNC",
            "numero_identificacion": "123456789",
            "telefono": "809-555-1234",
            "correo_electronico": "contacto@empresaabc.com",
            "direccion": "Calle Principal #123",
            "limite_credito": "50000.00",
            "categoria": 1,
            "categoria_nombre": "VIP",
            "activo": true,
            "fecha_creacion": "2025-01-27T10:30:00Z"
        }
    """
    queryset = Cliente.objects.select_related(
        'empresa',
        'categoria',
        'vendedor_asignado',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    pagination_class = ClientesPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'categoria', 'vendedor_asignado', 'tipo_identificacion']
    search_fields = ['nombre', 'numero_identificacion', 'telefono', 'correo_electronico']
    ordering_fields = ['nombre', 'fecha_creacion', 'limite_credito']
    ordering = ['nombre']

    def get_serializer_class(self):
        """Retorna serializer según la acción"""
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa un cliente.

        POST /clientes/{id}/activar/
        """
        cliente = self.get_object()
        exito, error = ClienteService.activar_cliente(
            cliente=cliente,
            ejecutado_por=request.user
        )
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Cliente "{cliente.nombre}" activado correctamente'})

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Desactiva un cliente.

        POST /clientes/{id}/desactivar/
        """
        cliente = self.get_object()
        exito, error = ClienteService.desactivar_cliente(
            cliente=cliente,
            ejecutado_por=request.user
        )
        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'mensaje': f'Cliente "{cliente.nombre}" desactivado correctamente'})

    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """
        Obtener historial de facturas del cliente.

        GET /clientes/{id}/historial_compras/

        Query params:
            - limit: Límite de facturas a retornar (opcional)
        """
        cliente = self.get_object()
        limit = request.query_params.get('limit')
        limit = int(limit) if limit and limit.isdigit() else None

        historial, error = ClienteService.obtener_historial_compras(cliente, limit)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(historial)

    @action(detail=True, methods=['get'])
    def historial_pagos(self, request, pk=None):
        """
        Obtener historial de pagos del cliente.

        GET /clientes/{id}/historial_pagos/

        Query params:
            - limit: Límite de pagos a retornar (opcional)
        """
        cliente = self.get_object()
        limit = request.query_params.get('limit')
        limit = int(limit) if limit and limit.isdigit() else None

        historial, error = ClienteService.obtener_historial_pagos(cliente, limit)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(historial)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Resumen completo del cliente con estadísticas.

        GET /clientes/{id}/resumen/

        Response incluye:
            - Datos del cliente
            - Total de facturas
            - Total de ventas
            - Total pendiente
            - Total pagado
            - Crédito disponible
        """
        cliente = self.get_object()
        resumen, error = ClienteService.obtener_resumen(cliente)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Agregar datos del cliente al resumen
        resumen['cliente'] = ClienteSerializer(cliente).data
        return Response(resumen)

    @action(detail=True, methods=['post'])
    def actualizar_limite_credito(self, request, pk=None):
        """
        Actualiza el límite de crédito del cliente.

        POST /clientes/{id}/actualizar_limite_credito/

        Body:
            {
                "limite_credito": "75000.00"
            }
        """
        cliente = self.get_object()
        nuevo_limite = request.data.get('limite_credito')

        if nuevo_limite is None:
            return Response(
                {'error': 'Debe proporcionar el nuevo límite de crédito'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal
            nuevo_limite = Decimal(str(nuevo_limite))
        except (ValueError, TypeError):
            return Response(
                {'error': 'El límite de crédito debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        exito, error = ClienteService.actualizar_limite_credito(
            cliente=cliente,
            nuevo_limite=nuevo_limite,
            ejecutado_por=request.user
        )

        if not exito:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        cliente.refresh_from_db()
        return Response({
            'mensaje': f'Límite de crédito actualizado a {nuevo_limite}',
            'cliente': ClienteSerializer(cliente).data
        })

    @action(detail=True, methods=['get'])
    def verificar_credito(self, request, pk=None):
        """
        Verifica si el cliente puede realizar una compra a crédito.

        GET /clientes/{id}/verificar_credito/?monto=1000

        Query params:
            - monto: Monto a verificar (requerido)

        Response:
            {
                "puede_comprar": true/false,
                "credito_disponible": "50000.00",
                "monto_solicitado": "1000.00",
                "mensaje": "..."
            }
        """
        cliente = self.get_object()
        monto = request.query_params.get('monto')

        if not monto:
            return Response(
                {'error': 'Debe proporcionar el monto a verificar'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal
            monto = Decimal(str(monto))
        except (ValueError, TypeError):
            return Response(
                {'error': 'El monto debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        puede, error = ClienteService.verificar_limite_credito(cliente, monto)
        credito_disponible = ClienteService.calcular_credito_disponible(cliente)

        return Response({
            'puede_comprar': puede,
            'credito_disponible': str(credito_disponible),
            'monto_solicitado': str(monto),
            'limite_credito': str(cliente.limite_credito),
            'mensaje': error if error else 'El cliente puede realizar la compra a crédito'
        })

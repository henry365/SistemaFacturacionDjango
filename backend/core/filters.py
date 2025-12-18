"""
Mixins de filtrado para ViewSets del Sistema de Facturación.

Este módulo implementa el principio DRY (Don't Repeat Yourself) proporcionando
mixins reutilizables para filtrado común en ViewSets.

Uso:
    class MiViewSet(StandardFilterMixin, EmpresaFilterMixin, viewsets.ModelViewSet):
        fecha_field = 'fecha_creacion'  # Campo de fecha para filtrar
        # get_queryset() automáticamente aplicará los filtros

Los filtros disponibles via query params:
    - ?estado=PENDIENTE
    - ?fecha_desde=2024-01-01
    - ?fecha_hasta=2024-12-31
    - ?cliente=1
    - ?proveedor=2
    - ?producto=3
    - ?almacen=4
"""


class EstadoFilterMixin:
    """
    Mixin para filtrado por campo 'estado' en get_queryset().

    Query param: ?estado=VALOR

    Ejemplo:
        GET /api/v1/facturas/?estado=PENDIENTE_PAGO
    """

    def filter_by_estado(self, queryset):
        """Filtra por estado si se proporciona en query params."""
        estado = self.request.query_params.get('estado')
        if estado:
            return queryset.filter(estado=estado)
        return queryset


class FechaRangeFilterMixin:
    """
    Mixin para filtrado por rango de fechas.

    Atributos de clase:
        fecha_field: Nombre del campo de fecha a filtrar (default: 'fecha')

    Query params:
        ?fecha_desde=YYYY-MM-DD
        ?fecha_hasta=YYYY-MM-DD

    Ejemplo:
        class FacturaViewSet(FechaRangeFilterMixin, ...):
            fecha_field = 'fecha'

        GET /api/v1/facturas/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31
    """

    fecha_field = 'fecha'  # Override en subclases

    def filter_by_fecha_range(self, queryset):
        """Filtra por rango de fechas si se proporcionan en query params."""
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if fecha_desde:
            queryset = queryset.filter(**{f'{self.fecha_field}__gte': fecha_desde})
        if fecha_hasta:
            queryset = queryset.filter(**{f'{self.fecha_field}__lte': fecha_hasta})

        return queryset


class RelatedFilterMixin:
    """
    Mixin para filtrado por ForeignKeys comunes.

    Filtra automáticamente por: cliente, proveedor, producto, almacen, vendedor

    Query params:
        ?cliente=ID
        ?proveedor=ID
        ?producto=ID
        ?almacen=ID
        ?vendedor=ID

    Ejemplo:
        GET /api/v1/facturas/?cliente=5
    """

    # Campos FK a filtrar (pueden ser override en subclases)
    related_filter_fields = ['cliente', 'proveedor', 'producto', 'almacen', 'vendedor']

    def filter_by_related(self, queryset):
        """Filtra por FKs relacionados si se proporcionan en query params."""
        for field in self.related_filter_fields:
            value = self.request.query_params.get(field)
            if value:
                # Verificar que el campo existe en el modelo
                model = queryset.model
                if hasattr(model, field):
                    queryset = queryset.filter(**{f'{field}_id': value})

        return queryset


class BooleanFilterMixin:
    """
    Mixin para filtrado por campos booleanos.

    Atributos de clase:
        boolean_filter_fields: Lista de campos booleanos a filtrar

    Query params acepta: true, false, 1, 0, yes, no

    Ejemplo:
        class ProductoViewSet(BooleanFilterMixin, ...):
            boolean_filter_fields = ['activo', 'es_servicio']

        GET /api/v1/productos/?activo=true&es_servicio=false
    """

    boolean_filter_fields = ['activo']

    def filter_by_boolean(self, queryset):
        """Filtra por campos booleanos si se proporcionan en query params."""
        true_values = {'true', '1', 'yes', 'si'}
        false_values = {'false', '0', 'no'}

        for field in self.boolean_filter_fields:
            value = self.request.query_params.get(field, '').lower()
            if value:
                model = queryset.model
                if hasattr(model, field):
                    if value in true_values:
                        queryset = queryset.filter(**{field: True})
                    elif value in false_values:
                        queryset = queryset.filter(**{field: False})

        return queryset


class SearchFilterMixin:
    """
    Mixin para búsqueda por texto en múltiples campos.

    Atributos de clase:
        search_fields: Lista de campos donde buscar (soporta lookups)

    Query param: ?search=texto

    Ejemplo:
        class ClienteViewSet(SearchFilterMixin, ...):
            search_fields = ['nombre__icontains', 'numero_identificacion__icontains']

        GET /api/v1/clientes/?search=juan
    """

    search_fields = []

    def filter_by_search(self, queryset):
        """Filtra por texto de búsqueda si se proporciona en query params."""
        from django.db.models import Q

        search = self.request.query_params.get('search', '').strip()
        if not search or not self.search_fields:
            return queryset

        query = Q()
        for field in self.search_fields:
            # Si el campo no incluye un lookup, agregar __icontains por defecto
            if '__' not in field:
                field = f'{field}__icontains'
            query |= Q(**{field: search})

        return queryset.filter(query)


class OrderingFilterMixin:
    """
    Mixin para ordenamiento dinámico.

    Atributos de clase:
        ordering_fields: Lista de campos permitidos para ordenar
        default_ordering: Ordenamiento por defecto

    Query param: ?ordering=campo (prefijo - para descendente)

    Ejemplo:
        class FacturaViewSet(OrderingFilterMixin, ...):
            ordering_fields = ['fecha', 'total', 'numero_factura']
            default_ordering = '-fecha'

        GET /api/v1/facturas/?ordering=-total
    """

    ordering_fields = []
    default_ordering = '-fecha_creacion'

    def filter_by_ordering(self, queryset):
        """Aplica ordenamiento si se proporciona en query params."""
        ordering = self.request.query_params.get('ordering', '').strip()

        if ordering:
            # Quitar prefijo - para validar el campo
            field = ordering.lstrip('-')
            if field in self.ordering_fields:
                return queryset.order_by(ordering)

        # Aplicar ordenamiento por defecto
        if self.default_ordering:
            return queryset.order_by(self.default_ordering)

        return queryset


class StandardFilterMixin(
    EstadoFilterMixin,
    FechaRangeFilterMixin,
    RelatedFilterMixin,
    BooleanFilterMixin,
    SearchFilterMixin,
    OrderingFilterMixin
):
    """
    Mixin que combina todos los filtros estándar.

    Incluye:
    - Filtrado por estado
    - Filtrado por rango de fechas
    - Filtrado por FKs relacionados (cliente, proveedor, etc.)
    - Filtrado por campos booleanos
    - Búsqueda por texto
    - Ordenamiento dinámico

    Uso:
        class FacturaViewSet(StandardFilterMixin, EmpresaFilterMixin, viewsets.ModelViewSet):
            queryset = Factura.objects.all()
            fecha_field = 'fecha'
            search_fields = ['numero_factura', 'cliente__nombre']
            ordering_fields = ['fecha', 'total']
            default_ordering = '-fecha'
    """

    def get_queryset(self):
        """
        Aplica todos los filtros estándar al queryset.

        Este método DEBE ser llamado por super() si se sobrescribe en la subclase.
        """
        queryset = super().get_queryset()

        # Aplicar todos los filtros en orden
        queryset = self.filter_by_estado(queryset)
        queryset = self.filter_by_fecha_range(queryset)
        queryset = self.filter_by_related(queryset)
        queryset = self.filter_by_boolean(queryset)
        queryset = self.filter_by_search(queryset)
        queryset = self.filter_by_ordering(queryset)

        return queryset


class DocumentoFilterMixin(StandardFilterMixin):
    """
    Mixin especializado para documentos transaccionales.

    Extiende StandardFilterMixin con filtros adicionales para documentos:
    - Filtrado por número de documento
    - Filtrado por tipo de venta/compra
    - Filtrado por usuario creador

    Query params adicionales:
        ?numero=FAC-001
        ?tipo_venta=CREDITO
        ?usuario=5
    """

    def filter_by_documento(self, queryset):
        """Filtros adicionales para documentos."""
        # Filtrar por número de documento
        numero = self.request.query_params.get('numero')
        if numero:
            # Buscar en campos comunes de número
            from django.db.models import Q
            query = Q()
            for field in ['numero_factura', 'numero', 'codigo']:
                if hasattr(queryset.model, field):
                    query |= Q(**{f'{field}__icontains': numero})
            if query:
                queryset = queryset.filter(query)

        # Filtrar por tipo de venta
        tipo_venta = self.request.query_params.get('tipo_venta')
        if tipo_venta and hasattr(queryset.model, 'tipo_venta'):
            queryset = queryset.filter(tipo_venta=tipo_venta)

        # Filtrar por usuario creador
        usuario = self.request.query_params.get('usuario')
        if usuario:
            for field in ['usuario', 'usuario_creacion']:
                if hasattr(queryset.model, field):
                    queryset = queryset.filter(**{f'{field}_id': usuario})
                    break

        return queryset

    def get_queryset(self):
        """Aplica filtros de documento además de los estándar."""
        queryset = super().get_queryset()
        queryset = self.filter_by_documento(queryset)
        return queryset

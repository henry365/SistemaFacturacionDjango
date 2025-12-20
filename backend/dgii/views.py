"""
Views para DGII (Comprobantes Fiscales)

Incluye gestión de tipos de comprobante, secuencias NCF,
y generación de reportes fiscales (606, 607, 608).
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.http import HttpResponse
from datetime import date
from decimal import Decimal
import csv
import io

from core.mixins import EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin
from usuarios.permissions import ActionBasedPermission
from .models import TipoComprobante, SecuenciaNCF
from .serializers import (
    TipoComprobanteSerializer, TipoComprobanteListSerializer,
    SecuenciaNCFSerializer, SecuenciaNCFListSerializer,
    GenerarNCFSerializer
)
from .permissions import (
    CanGenerarNCF, CanGenerarReporte606, CanGenerarReporte607,
    CanGenerarReporte608, CanGestionarTipoComprobante, CanGestionarSecuencia
)
from .constants import (
    PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX, PAGE_SIZE_REPORTES,
    TIPO_IDENTIFICACION_RNC, TIPO_IDENTIFICACION_CEDULA,
    TIPO_IDENTIFICACION_OTRO, LONGITUD_RNC, LONGITUD_CEDULA,
    ERROR_SECUENCIA_NO_ACTIVA, ERROR_SECUENCIA_AGOTADA_ACCION,
    ERROR_SECUENCIA_VENCIDA, ERROR_NO_SECUENCIA_DISPONIBLE,
    ERROR_MES_ANIO_REQUERIDOS, ERROR_MES_ANIO_NUMEROS
)

logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN
# =============================================================================

class TipoComprobantePagination(PageNumberPagination):
    """Paginación para TipoComprobante"""
    page_size = PAGE_SIZE_REPORTES
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


class SecuenciaNCFPagination(PageNumberPagination):
    """Paginación para SecuenciaNCF"""
    page_size = PAGE_SIZE_REPORTES
    page_size_query_param = 'page_size'
    max_page_size = PAGE_SIZE_MAX


# =============================================================================
# HELPERS
# =============================================================================

def get_tipo_identificacion(numero):
    """
    Determina el tipo de identificación según el formato.

    Args:
        numero: Número de identificación

    Returns:
        str: '1' para RNC, '2' para Cédula, '3' para Otro
    """
    if not numero:
        return TIPO_IDENTIFICACION_OTRO
    numero = numero.replace('-', '').replace(' ', '')
    if len(numero) == LONGITUD_RNC:
        return TIPO_IDENTIFICACION_RNC
    elif len(numero) == LONGITUD_CEDULA:
        return TIPO_IDENTIFICACION_CEDULA
    return TIPO_IDENTIFICACION_OTRO


# =============================================================================
# VIEWSETS
# =============================================================================

class TipoComprobanteViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar tipos de comprobantes fiscales.

    Endpoints:
        GET/POST /api/v1/dgii/tipos-comprobante/
        GET/PUT/PATCH/DELETE /api/v1/dgii/tipos-comprobante/{id}/

    Permisos:
        - IsAuthenticated para lectura
        - CanGestionarTipoComprobante para crear/editar/eliminar
    """
    queryset = TipoComprobante.objects.select_related(
        'empresa', 'usuario_creacion', 'usuario_modificacion'
    ).all()
    serializer_class = TipoComprobanteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TipoComprobantePagination
    filterset_fields = ['activo', 'codigo', 'prefijo']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['codigo', 'nombre', 'fecha_creacion']
    ordering = ['codigo']

    def get_permissions(self):
        """Aplica permisos según la acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGestionarTipoComprobante()]
        return [IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usa serializer optimizado para listados"""
        if self.action == 'list':
            return TipoComprobanteListSerializer
        return TipoComprobanteSerializer

    def perform_create(self, serializer):
        """Asigna empresa y usuario al crear con logging"""
        super().perform_create(serializer)
        logger.info(
            f"TipoComprobante creado: {serializer.instance.codigo} "
            f"(id={serializer.instance.id}, usuario={self.request.user.id})"
        )

    def perform_update(self, serializer):
        """Asigna usuario de modificación con logging"""
        super().perform_update(serializer)
        logger.info(
            f"TipoComprobante actualizado: {serializer.instance.codigo} "
            f"(id={serializer.instance.id}, usuario={self.request.user.id})"
        )

    def perform_destroy(self, instance):
        """Elimina tipo de comprobante con logging"""
        logger.warning(
            f"TipoComprobante eliminado: {instance.codigo} "
            f"(id={instance.id}, usuario={self.request.user.id})"
        )
        instance.delete()


class SecuenciaNCFViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar secuencias de NCF.

    Endpoints:
        GET/POST /api/v1/dgii/secuencias/
        GET/PUT/PATCH/DELETE /api/v1/dgii/secuencias/{id}/
        GET /api/v1/dgii/secuencias/activas/
        GET /api/v1/dgii/secuencias/por_vencer/
        POST /api/v1/dgii/secuencias/{id}/generar_ncf/
        POST /api/v1/dgii/secuencias/generar_por_tipo/

    Permisos:
        - IsAuthenticated para lectura
        - CanGestionarSecuencia para crear/editar/eliminar
        - CanGenerarNCF para generar_ncf y generar_por_tipo
    """
    queryset = SecuenciaNCF.objects.select_related(
        'tipo_comprobante', 'tipo_comprobante__empresa',
        'empresa', 'usuario_creacion', 'usuario_modificacion'
    ).all()
    serializer_class = SecuenciaNCFSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SecuenciaNCFPagination
    filterset_fields = ['tipo_comprobante', 'activo']
    search_fields = ['descripcion', 'tipo_comprobante__nombre']
    ordering_fields = ['fecha_vencimiento', 'secuencia_actual', 'fecha_creacion']
    ordering = ['-fecha_creacion']

    def get_permissions(self):
        """Aplica permisos según la acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGestionarSecuencia()]
        if self.action in ['generar_ncf', 'generar_por_tipo']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGenerarNCF()]
        return [IsAuthenticated(), ActionBasedPermission()]

    def get_serializer_class(self):
        """Usa serializer optimizado para listados"""
        if self.action == 'list':
            return SecuenciaNCFListSerializer
        return SecuenciaNCFSerializer

    def perform_create(self, serializer):
        """Asigna empresa y usuario al crear con logging"""
        super().perform_create(serializer)
        logger.info(
            f"SecuenciaNCF creada: tipo={serializer.instance.tipo_comprobante} "
            f"(id={serializer.instance.id}, usuario={self.request.user.id})"
        )

    def perform_update(self, serializer):
        """Asigna usuario de modificación con logging"""
        super().perform_update(serializer)
        logger.info(
            f"SecuenciaNCF actualizada: id={serializer.instance.id} "
            f"(usuario={self.request.user.id})"
        )

    def perform_destroy(self, instance):
        """Elimina secuencia NCF con logging"""
        logger.warning(
            f"SecuenciaNCF eliminada: id={instance.id}, tipo={instance.tipo_comprobante} "
            f"(usuario={self.request.user.id})"
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Retorna solo las secuencias activas y no agotadas.

        Endpoint: GET /api/v1/dgii/secuencias/activas/
        """
        secuencias = self.get_queryset().filter(
            activo=True,
            fecha_vencimiento__gte=date.today()
        )
        # Filtrar las agotadas en Python (property)
        secuencias_disponibles = [s for s in secuencias if not s.agotada]
        serializer = self.get_serializer(secuencias_disponibles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_vencer(self, request):
        """
        Retorna secuencias próximas a vencer o con pocos NCF disponibles.

        Endpoint: GET /api/v1/dgii/secuencias/por_vencer/
        """
        from datetime import timedelta
        fecha_alerta = date.today() + timedelta(days=30)

        secuencias = self.get_queryset().filter(activo=True)

        alertas = []
        for secuencia in secuencias:
            disponibles = secuencia.disponibles
            if secuencia.fecha_vencimiento <= fecha_alerta or disponibles <= secuencia.alerta_cantidad:
                alertas.append({
                    'secuencia': SecuenciaNCFSerializer(secuencia).data,
                    'alerta_vencimiento': secuencia.fecha_vencimiento <= fecha_alerta,
                    'alerta_cantidad': disponibles <= secuencia.alerta_cantidad,
                    'dias_para_vencer': (secuencia.fecha_vencimiento - date.today()).days,
                    'ncf_disponibles': disponibles
                })

        logger.info(
            f"Consulta de secuencias por vencer: {len(alertas)} alertas "
            f"(empresa_id={request.user.empresa_id})"
        )
        return Response(alertas)

    @action(detail=True, methods=['post'])
    def generar_ncf(self, request, pk=None):
        """
        Genera el siguiente NCF de una secuencia.

        IDEMPOTENTE: Cada llamada genera un nuevo NCF (esto es intencional).

        Endpoint: POST /api/v1/dgii/secuencias/{id}/generar_ncf/

        Returns:
            NCF generado, secuencia actual y disponibles.
        """
        secuencia = self.get_object()

        if not secuencia.activo:
            logger.warning(
                f"Intento de generar NCF en secuencia inactiva {pk} "
                f"por usuario {request.user.id}"
            )
            return Response(
                {'error': ERROR_SECUENCIA_NO_ACTIVA},
                status=status.HTTP_400_BAD_REQUEST
            )

        if secuencia.agotada:
            logger.warning(
                f"Intento de generar NCF en secuencia agotada {pk} "
                f"por usuario {request.user.id}"
            )
            return Response(
                {'error': ERROR_SECUENCIA_AGOTADA_ACCION},
                status=status.HTTP_400_BAD_REQUEST
            )

        if secuencia.fecha_vencimiento < date.today():
            logger.warning(
                f"Intento de generar NCF en secuencia vencida {pk} "
                f"por usuario {request.user.id}"
            )
            return Response(
                {'error': ERROR_SECUENCIA_VENCIDA},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Bloquear el registro para evitar concurrencia
            secuencia = SecuenciaNCF.objects.select_for_update().get(pk=secuencia.pk)
            ncf = secuencia.siguiente_numero()
            secuencia.secuencia_actual += 1
            secuencia.usuario_modificacion = request.user
            secuencia.save(update_fields=['secuencia_actual', 'usuario_modificacion', 'fecha_actualizacion'])

        logger.info(
            f"NCF generado: {ncf} (secuencia={pk}, usuario={request.user.id})"
        )

        return Response({
            'ncf': ncf,
            'secuencia_actual': secuencia.secuencia_actual,
            'disponibles': secuencia.disponibles
        })

    @action(detail=False, methods=['post'])
    def generar_por_tipo(self, request):
        """
        Genera NCF dado un tipo de comprobante.
        Busca automáticamente la secuencia activa correspondiente.

        Endpoint: POST /api/v1/dgii/secuencias/generar_por_tipo/

        Request Body:
            tipo_comprobante_id: ID del tipo de comprobante

        Returns:
            NCF generado, tipo de comprobante, secuencia_id y disponibles.
        """
        serializer = GenerarNCFSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        tipo_id = serializer.validated_data['tipo_comprobante_id']

        with transaction.atomic():
            secuencia = SecuenciaNCF.objects.select_for_update().filter(
                empresa=request.user.empresa,
                tipo_comprobante_id=tipo_id,
                activo=True,
                fecha_vencimiento__gte=date.today()
            ).first()

            if not secuencia or secuencia.agotada:
                logger.warning(
                    f"No hay secuencia disponible para tipo {tipo_id} "
                    f"(empresa_id={request.user.empresa_id})"
                )
                return Response(
                    {'error': ERROR_NO_SECUENCIA_DISPONIBLE},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ncf = secuencia.siguiente_numero()
            secuencia.secuencia_actual += 1
            secuencia.usuario_modificacion = request.user
            secuencia.save(update_fields=['secuencia_actual', 'usuario_modificacion', 'fecha_actualizacion'])

        logger.info(
            f"NCF generado por tipo: {ncf} (tipo={tipo_id}, secuencia={secuencia.id}, "
            f"usuario={request.user.id})"
        )

        return Response({
            'ncf': ncf,
            'tipo_comprobante': str(secuencia.tipo_comprobante),
            'secuencia_id': secuencia.id,
            'disponibles': secuencia.disponibles
        })


class ReportesDGIIViewSet(viewsets.ViewSet):
    """
    ViewSet para generar reportes fiscales DGII (606, 607, 608).

    Incluye endpoints síncronos (para compatibilidad) y asíncronos (Django 6.0 Tasks).
    Los endpoints *_async inician la generación en segundo plano y retornan un task_id.

    Django 6.0: Paginación agregada para formato JSON.
    - Use ?page=N y ?page_size=N para paginar resultados JSON
    - El formato TXT siempre exporta todos los registros (requerido por DGII)

    Permisos:
        - CanGenerarReporte606 para formato_606 y formato_606_async
        - CanGenerarReporte607 para formato_607 y formato_607_async
        - CanGenerarReporte608 para formato_608 y formato_608_async
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Aplica permisos según la acción"""
        if self.action in ['formato_606', 'formato_606_async']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGenerarReporte606()]
        if self.action in ['formato_607', 'formato_607_async']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGenerarReporte607()]
        if self.action in ['formato_608', 'formato_608_async']:
            return [IsAuthenticated(), ActionBasedPermission(), CanGenerarReporte608()]
        return [IsAuthenticated(), ActionBasedPermission()]

    def _paginate_registros(self, request, registros):
        """
        Aplica paginación a una lista de registros.

        Returns:
            dict con 'results', 'count', 'page', 'page_size', 'total_pages'
        """
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size', PAGE_SIZE_DEFAULT)

        try:
            page_size = min(int(page_size), PAGE_SIZE_MAX)
        except (ValueError, TypeError):
            page_size = PAGE_SIZE_DEFAULT

        total_count = len(registros)
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

        if page is None:
            # Sin paginación - retornar todos
            return {
                'count': total_count,
                'registros': registros
            }

        try:
            page = int(page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        return {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
            'registros': registros[start:end]
        }

    # ==================== ENDPOINTS ASYNC (Django 6.0 Tasks) ====================

    @action(detail=False, methods=['post'])
    def formato_606_async(self, request):
        """
        Inicia la generación del reporte 606 en segundo plano.

        Body params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)

        Returns:
            task_id para consultar el estado posteriormente
        """
        from .tasks import generar_reporte_606

        empresa = request.user.empresa
        mes = request.data.get('mes')
        anio = request.data.get('anio')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Iniciando generación async reporte 606 {anio}-{mes:02d} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        # Encolar tarea en segundo plano
        task_result = generar_reporte_606.enqueue(
            empresa_id=empresa.id,
            anio=anio,
            mes=mes
        )

        return Response({
            'task_id': str(task_result.id),
            'status': 'processing',
            'mensaje': f'Generando reporte 606 para {anio}-{mes:02d}'
        })

    @action(detail=False, methods=['post'])
    def formato_607_async(self, request):
        """
        Inicia la generación del reporte 607 en segundo plano.

        Body params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)

        Returns:
            task_id para consultar el estado posteriormente
        """
        from .tasks import generar_reporte_607

        empresa = request.user.empresa
        mes = request.data.get('mes')
        anio = request.data.get('anio')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Iniciando generación async reporte 607 {anio}-{mes:02d} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        task_result = generar_reporte_607.enqueue(
            empresa_id=empresa.id,
            anio=anio,
            mes=mes
        )

        return Response({
            'task_id': str(task_result.id),
            'status': 'processing',
            'mensaje': f'Generando reporte 607 para {anio}-{mes:02d}'
        })

    @action(detail=False, methods=['post'])
    def formato_608_async(self, request):
        """
        Inicia la generación del reporte 608 en segundo plano.

        Body params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)

        Returns:
            task_id para consultar el estado posteriormente
        """
        from .tasks import generar_reporte_608

        empresa = request.user.empresa
        mes = request.data.get('mes')
        anio = request.data.get('anio')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Iniciando generación async reporte 608 {anio}-{mes:02d} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        task_result = generar_reporte_608.enqueue(
            empresa_id=empresa.id,
            anio=anio,
            mes=mes
        )

        return Response({
            'task_id': str(task_result.id),
            'status': 'processing',
            'mensaje': f'Generando reporte 608 para {anio}-{mes:02d}'
        })

    # ==================== ENDPOINTS SÍNCRONOS (compatibilidad) ====================

    @action(detail=False, methods=['get'])
    def formato_606(self, request):
        """
        Genera el reporte 606 de compras de bienes y servicios.

        Query params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)
        - formato: 'json' (default) o 'txt'
        """
        from compras.models import Compra

        empresa = request.user.empresa
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        formato = request.query_params.get('formato', 'json')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Generando reporte 606 {anio}-{mes:02d} formato={formato} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        # Filtrar compras del período
        compras = Compra.objects.filter(
            empresa=empresa,
            fecha_compra__year=anio,
            fecha_compra__month=mes,
            estado__in=['REGISTRADA', 'CXP', 'PAGADA']
        ).select_related('proveedor').order_by('fecha_compra')

        registros = []
        for compra in compras:
            proveedor = compra.proveedor
            rnc = proveedor.numero_identificacion.replace('-', '').replace(' ', '') if proveedor.numero_identificacion else ''

            registro = {
                'rnc_cedula': rnc,
                'tipo_identificacion': get_tipo_identificacion(rnc),
                'tipo_bienes_servicios': compra.tipo_gasto,
                'ncf': compra.numero_ncf or '',
                'ncf_modificado': compra.ncf_modificado or '',
                'fecha_comprobante': compra.fecha_compra.strftime('%Y%m%d'),
                'fecha_pago': compra.fecha_compra.strftime('%Y%m%d'),
                'monto_facturado': str(compra.total),
                'itbis_facturado': str(compra.impuestos),
                'itbis_retenido': '0',
                'itbis_sujeto_proporcionalidad': '0',
                'itbis_llevado_costo': '0',
                'itbis_por_adelantar': '0',
                'itbis_percibido_compras': '0',
                'tipo_retencion_isr': '',
                'monto_retencion_renta': '0',
                'isr_percibido_compras': '0',
                'impuesto_selectivo_consumo': '0',
                'otros_impuestos_tasas': '0',
                'monto_propina_legal': '0',
                'forma_pago': '01',
            }
            registros.append(registro)

        if formato == 'txt':
            # Generar archivo TXT para DGII
            output = io.StringIO()
            writer = csv.writer(output, delimiter='|')

            for reg in registros:
                writer.writerow([
                    reg['rnc_cedula'],
                    reg['tipo_identificacion'],
                    reg['tipo_bienes_servicios'],
                    reg['ncf'],
                    reg['ncf_modificado'],
                    reg['fecha_comprobante'],
                    reg['fecha_pago'],
                    reg['monto_facturado'],
                    reg['itbis_facturado'],
                    reg['itbis_retenido'],
                    reg['itbis_sujeto_proporcionalidad'],
                    reg['itbis_llevado_costo'],
                    reg['itbis_por_adelantar'],
                    reg['itbis_percibido_compras'],
                    reg['tipo_retencion_isr'],
                    reg['monto_retencion_renta'],
                    reg['isr_percibido_compras'],
                    reg['impuesto_selectivo_consumo'],
                    reg['otros_impuestos_tasas'],
                    reg['monto_propina_legal'],
                    reg['forma_pago'],
                ])

            response = HttpResponse(output.getvalue(), content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="606_{empresa.rnc}_{anio}{mes:02d}.txt"'
            return response

        # Respuesta JSON con paginación opcional
        paginacion = self._paginate_registros(request, registros)
        return Response({
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': paginacion['count'],
            'page': paginacion.get('page'),
            'page_size': paginacion.get('page_size'),
            'total_pages': paginacion.get('total_pages'),
            'has_next': paginacion.get('has_next'),
            'has_previous': paginacion.get('has_previous'),
            'registros': paginacion['registros'],
            'totales': {
                'monto_facturado': str(sum(Decimal(r['monto_facturado']) for r in registros)),
                'itbis_facturado': str(sum(Decimal(r['itbis_facturado']) for r in registros)),
            }
        })

    @action(detail=False, methods=['get'])
    def formato_607(self, request):
        """
        Genera el reporte 607 de ventas de bienes y servicios.

        Query params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)
        - formato: 'json' (default) o 'txt'
        """
        from ventas.models import Factura

        empresa = request.user.empresa
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        formato = request.query_params.get('formato', 'json')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Generando reporte 607 {anio}-{mes:02d} formato={formato} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        # Filtrar facturas del período (solo con NCF)
        facturas = Factura.objects.filter(
            empresa=empresa,
            fecha__year=anio,
            fecha__month=mes,
            estado__in=['PENDIENTE_PAGO', 'PAGADA_PARCIAL', 'PAGADA'],
            venta_sin_comprobante=False
        ).select_related('cliente').order_by('fecha')

        registros = []
        for factura in facturas:
            cliente = factura.cliente
            rnc = cliente.numero_identificacion.replace('-', '').replace(' ', '') if cliente.numero_identificacion else ''

            # Determinar tipo de ingreso basado en NCF
            tipo_ingreso = '01'  # Ingresos por operaciones (no financieros)

            registro = {
                'rnc_cedula': rnc,
                'tipo_identificacion': get_tipo_identificacion(rnc),
                'ncf': factura.ncf or '',
                'ncf_modificado': '',
                'tipo_ingreso': tipo_ingreso,
                'fecha_comprobante': factura.fecha.strftime('%Y%m%d'),
                'fecha_retencion': '',
                'monto_facturado': str(factura.total),
                'itbis_facturado': str(factura.itbis),
                'itbis_retenido_terceros': '0',
                'itbis_percibido': '0',
                'retencion_renta_terceros': '0',
                'isr_percibido': '0',
                'impuesto_selectivo_consumo': '0',
                'otros_impuestos_tasas': '0',
                'monto_propina_legal': '0',
                'efectivo': str(factura.total) if factura.tipo_venta == 'CONTADO' else '0',
                'cheque_transferencia_deposito': '0',
                'tarjeta_debito_credito': '0',
                'venta_credito': str(factura.total) if factura.tipo_venta == 'CREDITO' else '0',
                'bonos_certificados_regalo': '0',
                'permuta': '0',
                'otras_formas_venta': '0',
            }
            registros.append(registro)

        if formato == 'txt':
            # Generar archivo TXT para DGII
            output = io.StringIO()
            writer = csv.writer(output, delimiter='|')

            for reg in registros:
                writer.writerow([
                    reg['rnc_cedula'],
                    reg['tipo_identificacion'],
                    reg['ncf'],
                    reg['ncf_modificado'],
                    reg['tipo_ingreso'],
                    reg['fecha_comprobante'],
                    reg['fecha_retencion'],
                    reg['monto_facturado'],
                    reg['itbis_facturado'],
                    reg['itbis_retenido_terceros'],
                    reg['itbis_percibido'],
                    reg['retencion_renta_terceros'],
                    reg['isr_percibido'],
                    reg['impuesto_selectivo_consumo'],
                    reg['otros_impuestos_tasas'],
                    reg['monto_propina_legal'],
                    reg['efectivo'],
                    reg['cheque_transferencia_deposito'],
                    reg['tarjeta_debito_credito'],
                    reg['venta_credito'],
                    reg['bonos_certificados_regalo'],
                    reg['permuta'],
                    reg['otras_formas_venta'],
                ])

            response = HttpResponse(output.getvalue(), content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="607_{empresa.rnc}_{anio}{mes:02d}.txt"'
            return response

        # Respuesta JSON con paginación opcional
        paginacion = self._paginate_registros(request, registros)
        return Response({
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': paginacion['count'],
            'page': paginacion.get('page'),
            'page_size': paginacion.get('page_size'),
            'total_pages': paginacion.get('total_pages'),
            'has_next': paginacion.get('has_next'),
            'has_previous': paginacion.get('has_previous'),
            'registros': paginacion['registros'],
            'totales': {
                'monto_facturado': str(sum(Decimal(r['monto_facturado']) for r in registros)),
                'itbis_facturado': str(sum(Decimal(r['itbis_facturado']) for r in registros)),
            }
        })

    @action(detail=False, methods=['get'])
    def formato_608(self, request):
        """
        Genera el reporte 608 de comprobantes anulados.

        Query params:
        - mes: Mes del reporte (1-12)
        - anio: Año del reporte (YYYY)
        - formato: 'json' (default) o 'txt'
        """
        from ventas.models import Factura

        empresa = request.user.empresa
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        formato = request.query_params.get('formato', 'json')

        if not mes or not anio:
            return Response(
                {'error': ERROR_MES_ANIO_REQUERIDOS},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': ERROR_MES_ANIO_NUMEROS},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Generando reporte 608 {anio}-{mes:02d} formato={formato} "
            f"(empresa_id={empresa.id}, usuario={request.user.id})"
        )

        # Facturas canceladas con NCF
        facturas_anuladas = Factura.objects.filter(
            empresa=empresa,
            fecha__year=anio,
            fecha__month=mes,
            estado='CANCELADA',
            ncf__isnull=False
        ).exclude(ncf='').order_by('fecha')

        registros = []
        for factura in facturas_anuladas:
            registro = {
                'ncf': factura.ncf,
                'tipo_anulacion': '02',
                'fecha_comprobante': factura.fecha.strftime('%Y%m%d'),
            }
            registros.append(registro)

        if formato == 'txt':
            # Generar archivo TXT para DGII
            output = io.StringIO()
            writer = csv.writer(output, delimiter='|')

            for reg in registros:
                writer.writerow([
                    reg['ncf'],
                    reg['tipo_anulacion'],
                    reg['fecha_comprobante'],
                ])

            response = HttpResponse(output.getvalue(), content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="608_{empresa.rnc}_{anio}{mes:02d}.txt"'
            return response

        # Respuesta JSON con paginación opcional
        paginacion = self._paginate_registros(request, registros)
        return Response({
            'periodo': f'{anio}-{mes:02d}',
            'rnc_empresa': empresa.rnc,
            'cantidad_registros': paginacion['count'],
            'page': paginacion.get('page'),
            'page_size': paginacion.get('page_size'),
            'total_pages': paginacion.get('total_pages'),
            'has_next': paginacion.get('has_next'),
            'has_previous': paginacion.get('has_previous'),
            'registros': paginacion['registros']
        })

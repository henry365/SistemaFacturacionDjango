"""
Views para DGII (Comprobantes Fiscales)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from datetime import date, datetime
from decimal import Decimal
import csv
import io

from core.mixins import EmpresaFilterMixin
from .models import TipoComprobante, SecuenciaNCF
from .serializers import (
    TipoComprobanteSerializer,
    SecuenciaNCFSerializer,
    GenerarNCFSerializer
)


class TipoComprobanteViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar tipos de comprobantes fiscales.
    """
    queryset = TipoComprobante.objects.all()
    serializer_class = TipoComprobanteSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['activo', 'codigo', 'prefijo']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['codigo', 'nombre']
    ordering = ['codigo']

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class SecuenciaNCFViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar secuencias de NCF.
    """
    queryset = SecuenciaNCF.objects.select_related('tipo_comprobante').all()
    serializer_class = SecuenciaNCFSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo_comprobante', 'activo']
    search_fields = ['descripcion']
    ordering_fields = ['fecha_vencimiento', 'secuencia_actual']
    ordering = ['-fecha_creacion']

    def perform_create(self, serializer):
        serializer.save(
            empresa=self.request.user.empresa,
            usuario_creacion=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(usuario_modificacion=self.request.user)

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Retorna solo las secuencias activas y no agotadas"""
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
        """Retorna secuencias proximas a vencer o con pocos NCF disponibles"""
        from datetime import timedelta
        fecha_alerta = date.today() + timedelta(days=30)

        secuencias = self.get_queryset().filter(
            activo=True
        )

        alertas = []
        for secuencia in secuencias:
            disponibles = secuencia.secuencia_final - secuencia.secuencia_actual
            if secuencia.fecha_vencimiento <= fecha_alerta or disponibles <= secuencia.alerta_cantidad:
                alertas.append({
                    'secuencia': SecuenciaNCFSerializer(secuencia).data,
                    'alerta_vencimiento': secuencia.fecha_vencimiento <= fecha_alerta,
                    'alerta_cantidad': disponibles <= secuencia.alerta_cantidad,
                    'dias_para_vencer': (secuencia.fecha_vencimiento - date.today()).days,
                    'ncf_disponibles': disponibles
                })

        return Response(alertas)

    @action(detail=True, methods=['post'])
    def generar_ncf(self, request, pk=None):
        """
        Genera el siguiente NCF de una secuencia.
        Debe usarse dentro de una transaccion.
        """
        secuencia = self.get_object()

        if not secuencia.activo:
            return Response(
                {'error': 'Esta secuencia no esta activa.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if secuencia.agotada:
            return Response(
                {'error': 'Esta secuencia esta agotada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if secuencia.fecha_vencimiento < date.today():
            return Response(
                {'error': 'Esta secuencia ha vencido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Bloquear el registro para evitar concurrencia
            secuencia = SecuenciaNCF.objects.select_for_update().get(pk=secuencia.pk)
            ncf = secuencia.siguiente_numero()
            secuencia.secuencia_actual += 1
            secuencia.save()

        return Response({
            'ncf': ncf,
            'secuencia_actual': secuencia.secuencia_actual,
            'disponibles': secuencia.secuencia_final - secuencia.secuencia_actual
        })

    @action(detail=False, methods=['post'])
    def generar_por_tipo(self, request):
        """
        Genera NCF dado un tipo de comprobante.
        Busca automaticamente la secuencia activa correspondiente.
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
                return Response(
                    {'error': 'No hay secuencia disponible para este tipo de comprobante.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ncf = secuencia.siguiente_numero()
            secuencia.secuencia_actual += 1
            secuencia.save()

        return Response({
            'ncf': ncf,
            'tipo_comprobante': str(secuencia.tipo_comprobante),
            'secuencia_id': secuencia.id,
            'disponibles': secuencia.secuencia_final - secuencia.secuencia_actual
        })


class ReportesDGIIViewSet(viewsets.ViewSet):
    """
    ViewSet para generar reportes fiscales DGII (606, 607, 608).

    Incluye endpoints síncronos (para compatibilidad) y asíncronos (Django 6.0 Tasks).
    Los endpoints *_async inician la generación en segundo plano y retornan un task_id.

    Django 6.0: Paginación agregada para formato JSON.
    - Use ?page=N y ?page_size=N para paginar resultados JSON
    - El formato TXT siempre exporta todos los registros (requerido por DGII)
    """
    permission_classes = [IsAuthenticated]
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 500

    def _paginate_registros(self, request, registros):
        """
        Aplica paginación a una lista de registros.

        Returns:
            dict con 'results', 'count', 'page', 'page_size', 'total_pages'
        """
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size', self.DEFAULT_PAGE_SIZE)

        try:
            page_size = min(int(page_size), self.MAX_PAGE_SIZE)
        except (ValueError, TypeError):
            page_size = self.DEFAULT_PAGE_SIZE

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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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

    def _get_tipo_identificacion(self, numero):
        """Determina el tipo de identificación según el formato"""
        if not numero:
            return '3'  # Sin identificación
        numero = numero.replace('-', '').replace(' ', '')
        if len(numero) == 9:
            return '1'  # RNC
        elif len(numero) == 11:
            return '2'  # Cédula
        return '3'  # Otro

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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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
                'tipo_identificacion': self._get_tipo_identificacion(rnc),
                'tipo_bienes_servicios': compra.tipo_gasto,
                'ncf': compra.numero_ncf or '',
                'ncf_modificado': compra.ncf_modificado or '',
                'fecha_comprobante': compra.fecha_compra.strftime('%Y%m%d'),
                'fecha_pago': compra.fecha_compra.strftime('%Y%m%d'),  # TODO: Usar fecha real de pago
                'monto_facturado': str(compra.total),
                'itbis_facturado': str(compra.impuestos),
                'itbis_retenido': '0',  # TODO: Implementar retenciones
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
                'forma_pago': '01',  # TODO: Mapear forma de pago real
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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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
                'tipo_identificacion': self._get_tipo_identificacion(rnc),
                'ncf': factura.ncf or '',
                'ncf_modificado': '',  # TODO: Obtener de notas de crédito/débito
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
                {'error': 'Debe especificar mes y anio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mes = int(mes)
            anio = int(anio)
        except ValueError:
            return Response(
                {'error': 'mes y anio deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
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
                'tipo_anulacion': '02',  # 01=Deterioro, 02=Error de impresión, 03=Impresión defectuosa, 04=Duplicidad, 05=Corrección información, 06=Cambio de productos, 07=Devolución productos, 08=Omisión de productos, 09=Errores en secuencia NCF
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

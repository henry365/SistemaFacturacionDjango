"""
Dashboard API - Endpoints optimizados para métricas y KPIs del sistema.

Este módulo provee endpoints eficientes que agregan datos de múltiples
modelos usando consultas optimizadas con Django ORM.

Endpoints:
    GET /api/v1/dashboard/resumen/ - Resumen completo del dashboard
    GET /api/v1/dashboard/ventas_periodo/?dias=30 - Ventas por período
    GET /api/v1/dashboard/ventas_por_mes/?meses=12 - Ventas por mes
    GET /api/v1/dashboard/top_productos/?limite=10&dias=30 - Top productos
    GET /api/v1/dashboard/productos_stock_bajo/?limite=20 - Productos con stock bajo
    GET /api/v1/dashboard/top_clientes/?limite=10&dias=90 - Top clientes
    GET /api/v1/dashboard/cuentas_por_cobrar/ - Detalle CxC
    GET /api/v1/dashboard/cuentas_por_pagar/ - Detalle CxP
    GET /api/v1/dashboard/actividad_reciente/?limite=20 - Actividad reciente
    GET /api/v1/dashboard/indicadores_financieros/ - Indicadores financieros
"""
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from .services import DashboardService
from .constants import (
    DIAS_MAXIMO_DASHBOARD, MESES_MAXIMO_DASHBOARD,
    LIMITE_MAXIMO_PRODUCTOS, LIMITE_MAXIMO_CLIENTES, LIMITE_MAXIMO_ACTIVIDADES,
    DIAS_DEFAULT_VENTAS, MESES_DEFAULT_VENTAS,
    LIMITE_DEFAULT_PRODUCTOS, LIMITE_DEFAULT_CLIENTES,
    LIMITE_DEFAULT_ACTIVIDADES, LIMITE_DEFAULT_STOCK_BAJO,
    ERROR_EMPRESA_NO_ASIGNADA, ERROR_DIAS_INVALIDO, ERROR_MESES_INVALIDO,
    ERROR_LIMITE_INVALIDO, ERROR_RESUMEN_DASHBOARD, ERROR_VENTAS_PERIODO,
    ERROR_TOP_PRODUCTOS, ERROR_STOCK_BAJO, ERROR_TOP_CLIENTES,
    ERROR_CUENTAS_COBRAR, ERROR_CUENTAS_PAGAR, ERROR_ACTIVIDAD_RECIENTE,
    ERROR_INDICADORES
)

logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para métricas del Dashboard.

    Todos los endpoints filtran automáticamente por la empresa del usuario
    autenticado para garantizar aislamiento multi-tenant.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_empresa(self, request):
        """
        Obtiene la empresa del usuario autenticado.

        Raises:
            ValidationError: Si el usuario no tiene empresa asignada
        """
        empresa = request.user.empresa
        if not empresa:
            raise ValidationError(ERROR_EMPRESA_NO_ASIGNADA)
        return empresa

    def _validar_dias(self, dias):
        """
        Valida que días esté en rango válido.

        Args:
            dias: Número de días

        Returns:
            int: Días validado

        Raises:
            ValidationError: Si días está fuera de rango
        """
        if dias < 1 or dias > DIAS_MAXIMO_DASHBOARD:
            raise ValidationError(
                ERROR_DIAS_INVALIDO.format(max=DIAS_MAXIMO_DASHBOARD)
            )
        return dias

    def _validar_meses(self, meses):
        """
        Valida que meses esté en rango válido.

        Args:
            meses: Número de meses

        Returns:
            int: Meses validado

        Raises:
            ValidationError: Si meses está fuera de rango
        """
        if meses < 1 or meses > MESES_MAXIMO_DASHBOARD:
            raise ValidationError(
                ERROR_MESES_INVALIDO.format(max=MESES_MAXIMO_DASHBOARD)
            )
        return meses

    def _validar_limite(self, limite, maximo):
        """
        Valida que límite esté en rango válido.

        Args:
            limite: Límite a validar
            maximo: Valor máximo permitido

        Returns:
            int: Límite validado

        Raises:
            ValidationError: Si límite está fuera de rango
        """
        if limite < 1 or limite > maximo:
            raise ValidationError(ERROR_LIMITE_INVALIDO.format(max=maximo))
        return limite

    def _parse_int(self, value, default):
        """
        Parsea un valor a entero con valor por defecto.

        Args:
            value: Valor a parsear
            default: Valor por defecto

        Returns:
            int: Valor parseado
        """
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default

    # ==================== ENDPOINT PRINCIPAL ====================

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        Endpoint principal que retorna todas las métricas del dashboard
        en una sola llamada optimizada.

        Returns:
            dict: {
                'fecha': str (ISO format),
                'ventas': {'hoy': {...}, 'mes': {...}},
                'cuentas_por_cobrar': {...},
                'cuentas_por_pagar': {...},
                'inventario': {...},
                'caja_actual': {...}
            }

        Status Codes:
            - 200: OK
            - 400: Usuario sin empresa asignada
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            logger.info(f"Dashboard resumen solicitado por usuario {request.user.id}")

            resumen = DashboardService.obtener_resumen(empresa)

            logger.debug(f"Resumen generado para empresa {empresa.id}")
            return Response(resumen)

        except ValidationError as e:
            logger.warning(f"Error de validación en resumen: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en resumen dashboard: {e}", exc_info=True)
            return Response(
                {'error': ERROR_RESUMEN_DASHBOARD},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== VENTAS ====================

    @action(detail=False, methods=['get'])
    def ventas_periodo(self, request):
        """
        Retorna ventas agrupadas por día para gráficos.

        Query params:
            - dias: Número de días hacia atrás (default: 30, max: 365)

        Returns:
            dict: {'periodo_dias': int, 'fecha_inicio': str, 'datos': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            dias = self._parse_int(
                request.query_params.get('dias'),
                DIAS_DEFAULT_VENTAS
            )
            dias = self._validar_dias(dias)

            logger.info(f"Ventas período ({dias} días) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_ventas_periodo(empresa, dias)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en ventas_periodo: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en ventas_periodo: {e}", exc_info=True)
            return Response(
                {'error': ERROR_VENTAS_PERIODO},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def ventas_por_mes(self, request):
        """
        Retorna ventas agrupadas por mes para gráficos anuales.

        Query params:
            - meses: Número de meses hacia atrás (default: 12, max: 36)

        Returns:
            dict: {'periodo_meses': int, 'datos': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            meses = self._parse_int(
                request.query_params.get('meses'),
                MESES_DEFAULT_VENTAS
            )
            meses = self._validar_meses(meses)

            logger.info(f"Ventas por mes ({meses} meses) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_ventas_por_mes(empresa, meses)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en ventas_por_mes: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en ventas_por_mes: {e}", exc_info=True)
            return Response(
                {'error': ERROR_VENTAS_PERIODO},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== PRODUCTOS ====================

    @action(detail=False, methods=['get'])
    def top_productos(self, request):
        """
        Retorna los productos más vendidos.

        Query params:
            - limite: Cantidad de productos (default: 10, max: 100)
            - dias: Período en días (default: 30, max: 365)

        Returns:
            dict: {'periodo_dias': int, 'productos': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            limite = self._parse_int(
                request.query_params.get('limite'),
                LIMITE_DEFAULT_PRODUCTOS
            )
            dias = self._parse_int(
                request.query_params.get('dias'),
                DIAS_DEFAULT_VENTAS
            )
            limite = self._validar_limite(limite, LIMITE_MAXIMO_PRODUCTOS)
            dias = self._validar_dias(dias)

            logger.info(f"Top productos ({limite}, {dias} días) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_top_productos(empresa, limite, dias)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en top_productos: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en top_productos: {e}", exc_info=True)
            return Response(
                {'error': ERROR_TOP_PRODUCTOS},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def productos_stock_bajo(self, request):
        """
        Retorna productos con stock por debajo del mínimo.

        Query params:
            - limite: Cantidad de productos (default: 20, max: 100)

        Returns:
            dict: {'total': int, 'productos': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            limite = self._parse_int(
                request.query_params.get('limite'),
                LIMITE_DEFAULT_STOCK_BAJO
            )
            limite = self._validar_limite(limite, LIMITE_MAXIMO_PRODUCTOS)

            logger.info(f"Stock bajo ({limite}) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_productos_stock_bajo(empresa, limite)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en productos_stock_bajo: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en productos_stock_bajo: {e}", exc_info=True)
            return Response(
                {'error': ERROR_STOCK_BAJO},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CLIENTES ====================

    @action(detail=False, methods=['get'])
    def top_clientes(self, request):
        """
        Retorna los clientes con mayor volumen de compras.

        Query params:
            - limite: Cantidad de clientes (default: 10, max: 100)
            - dias: Período en días (default: 90, max: 365)

        Returns:
            dict: {'periodo_dias': int, 'clientes': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            limite = self._parse_int(
                request.query_params.get('limite'),
                LIMITE_DEFAULT_CLIENTES
            )
            dias = self._parse_int(
                request.query_params.get('dias'),
                90  # Default específico para clientes
            )
            limite = self._validar_limite(limite, LIMITE_MAXIMO_CLIENTES)
            dias = self._validar_dias(dias)

            logger.info(f"Top clientes ({limite}, {dias} días) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_top_clientes(empresa, limite, dias)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en top_clientes: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en top_clientes: {e}", exc_info=True)
            return Response(
                {'error': ERROR_TOP_CLIENTES},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUENTAS ====================

    @action(detail=False, methods=['get'])
    def cuentas_por_cobrar(self, request):
        """
        Resumen detallado de cuentas por cobrar.

        Returns:
            dict: {
                'resumen_por_estado': {...},
                'por_vencer': {...},
                'vencidas_por_antiguedad': {...}
            }

        Status Codes:
            - 200: OK
            - 400: Sin empresa asignada
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            logger.info(f"CxC detalle solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_detalle_cxc(empresa)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en cuentas_por_cobrar: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en cuentas_por_cobrar: {e}", exc_info=True)
            return Response(
                {'error': ERROR_CUENTAS_COBRAR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def cuentas_por_pagar(self, request):
        """
        Resumen detallado de cuentas por pagar.

        Returns:
            dict: {
                'resumen_por_estado': {...},
                'por_vencer': {...}
            }

        Status Codes:
            - 200: OK
            - 400: Sin empresa asignada
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            logger.info(f"CxP detalle solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_detalle_cxp(empresa)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en cuentas_por_pagar: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en cuentas_por_pagar: {e}", exc_info=True)
            return Response(
                {'error': ERROR_CUENTAS_PAGAR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== ACTIVIDAD RECIENTE ====================

    @action(detail=False, methods=['get'])
    def actividad_reciente(self, request):
        """
        Retorna las últimas actividades del sistema.

        Query params:
            - limite: Cantidad de actividades (default: 20, max: 100)

        Returns:
            dict: {'total': int, 'actividades': [...]}

        Status Codes:
            - 200: OK
            - 400: Parámetros inválidos o sin empresa
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            limite = self._parse_int(
                request.query_params.get('limite'),
                LIMITE_DEFAULT_ACTIVIDADES
            )
            limite = self._validar_limite(limite, LIMITE_MAXIMO_ACTIVIDADES)

            logger.info(f"Actividad reciente ({limite}) solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_actividad_reciente(empresa, limite)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en actividad_reciente: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en actividad_reciente: {e}", exc_info=True)
            return Response(
                {'error': ERROR_ACTIVIDAD_RECIENTE},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== INDICADORES FINANCIEROS ====================

    @action(detail=False, methods=['get'])
    def indicadores_financieros(self, request):
        """
        Retorna indicadores financieros clave.

        Returns:
            dict: {
                'periodo': {...},
                'ventas': {...},
                'compras': {...},
                'cuentas': {...},
                'inventario': {...},
                'margen_bruto_mes': str
            }

        Status Codes:
            - 200: OK
            - 400: Sin empresa asignada
            - 401: No autenticado
            - 500: Error del servidor
        """
        try:
            empresa = self.get_empresa(request)
            logger.info(f"Indicadores financieros solicitado por usuario {request.user.id}")

            resultado = DashboardService.obtener_indicadores_financieros(empresa)
            return Response(resultado)

        except ValidationError as e:
            logger.warning(f"Error de validación en indicadores_financieros: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error en indicadores_financieros: {e}", exc_info=True)
            return Response(
                {'error': ERROR_INDICADORES},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

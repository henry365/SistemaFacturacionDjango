from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import (
    SolicitudCotizacionProveedor,
    OrdenCompra,
    Compra,
    Gasto,
    RecepcionCompra,
    DetalleRecepcion,
    DevolucionProveedor,
    DetalleDevolucionProveedor,
    LiquidacionImportacion,
    GastoImportacion,
    TipoRetencion,
    RetencionCompra
)
from .serializers import (
    SolicitudCotizacionProveedorSerializer,
    OrdenCompraSerializer,
    CompraSerializer,
    GastoSerializer,
    RecepcionCompraSerializer,
    RecepcionCompraListSerializer,
    DetalleRecepcionSerializer,
    DevolucionProveedorSerializer,
    DevolucionProveedorListSerializer,
    DetalleDevolucionProveedorSerializer,
    LiquidacionImportacionSerializer,
    LiquidacionImportacionListSerializer,
    GastoImportacionSerializer,
    TipoRetencionSerializer,
    RetencionCompraSerializer,
    AplicarRetencionSerializer
)
from .services import ServicioCompras
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin


class SolicitudCotizacionProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = SolicitudCotizacionProveedor.objects.all()
    serializer_class = SolicitudCotizacionProveedorSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['proveedor__nombre', 'detalles']
    ordering_fields = ['fecha_solicitud', 'estado']
    ordering = ['-fecha_solicitud']
    
    def get_queryset(self):
        """Filtrar solicitudes según empresa del usuario"""
        queryset = super().get_queryset()
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)
        
        return queryset


class OrdenCompraViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = OrdenCompra.objects.all()
    serializer_class = OrdenCompraSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['proveedor__nombre', 'observaciones']
    ordering_fields = ['fecha_emision', 'estado', 'total']
    ordering = ['-fecha_emision']
    
    def get_queryset(self):
        """Filtrar órdenes según empresa del usuario"""
        queryset = super().get_queryset()
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba una orden de compra"""
        orden = self.get_object()
        if orden.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden aprobar órdenes en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orden.estado = 'APROBADA'
        orden.usuario_aprobacion = request.user
        orden.usuario_modificacion = request.user
        orden.save()
        
        serializer = self.get_serializer(orden)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Marca la orden como enviada al proveedor"""
        orden = self.get_object()
        if orden.estado not in ['APROBADA', 'BORRADOR']:
            return Response(
                {'error': 'Solo se pueden enviar órdenes en estado BORRADOR o APROBADA'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orden.estado = 'ENVIADA'
        orden.usuario_modificacion = request.user
        orden.save()
        
        serializer = self.get_serializer(orden)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def recibir(self, request, pk=None):
        """Recibe una orden de compra con las cantidades recibidas"""
        orden = self.get_object()
        if orden.estado not in ['APROBADA', 'ENVIADA', 'RECIBIDA_PARCIAL']:
            return Response(
                {'error': 'Solo se pueden recibir órdenes en estado APROBADA, ENVIADA o RECIBIDA_PARCIAL'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        detalles_recibidos = request.data.get('detalles_recibidos', {})
        if not detalles_recibidos:
            return Response(
                {'error': 'Debe proporcionar las cantidades recibidas en el campo detalles_recibidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            orden = ServicioCompras.recibir_orden_compra(
                orden_compra=orden,
                detalles_recibidos=detalles_recibidos,
                usuario=request.user
            )
            serializer = self.get_serializer(orden)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una orden de compra"""
        orden = self.get_object()
        if orden.estado in ['RECIBIDA_TOTAL', 'CANCELADA']:
            return Response(
                {'error': 'No se puede cancelar una orden que ya está recibida totalmente o cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orden.estado = 'CANCELADA'
        orden.usuario_modificacion = request.user
        orden.save()
        
        serializer = self.get_serializer(orden)
        return Response(serializer.data)


class CompraViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['proveedor__nombre', 'numero_factura_proveedor', 'numero_ncf']
    ordering_fields = ['fecha_compra', 'fecha_registro', 'total', 'estado']
    ordering = ['-fecha_registro']
    
    def get_queryset(self):
        """Filtrar compras según empresa del usuario"""
        queryset = super().get_queryset()
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)
        
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_compra__gte=fecha_desde)
        
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_compra__lte=fecha_hasta)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """Procesa una compra registrando movimientos de inventario"""
        compra = self.get_object()
        almacen_id = request.data.get('almacen_id')
        
        almacen = None
        if almacen_id:
            from inventario.models import Almacen
            try:
                almacen = Almacen.objects.get(pk=almacen_id, empresa=compra.empresa)
            except Almacen.DoesNotExist:
                return Response(
                    {'error': 'El almacén especificado no existe o no pertenece a la empresa'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            movimientos = ServicioCompras.procesar_compra(
                compra=compra,
                usuario=request.user,
                almacen=almacen
            )
            serializer = self.get_serializer(compra)
            return Response({
                'compra': serializer.data,
                'movimientos_registrados': len(movimientos),
                'mensaje': 'Compra procesada exitosamente. Movimientos de inventario registrados.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        """Anula una compra y revierte movimientos de inventario"""
        compra = self.get_object()
        
        try:
            ServicioCompras.anular_compra(
                compra=compra,
                usuario=request.user
            )
            serializer = self.get_serializer(compra)
            return Response({
                'compra': serializer.data,
                'mensaje': 'Compra anulada exitosamente. Movimientos de inventario revertidos.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GastoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descripcion', 'categoria', 'numero_factura', 'proveedor__nombre']
    ordering_fields = ['fecha_gasto', 'fecha_creacion', 'total', 'estado']
    ordering = ['-fecha_gasto']
    
    def get_queryset(self):
        """Filtrar gastos según empresa del usuario"""
        queryset = super().get_queryset()
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        
        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)
        
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_gasto__gte=fecha_desde)
        
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_gasto__lte=fecha_hasta)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def marcar_pagado(self, request, pk=None):
        """Marca un gasto como pagado"""
        gasto = self.get_object()
        gasto.estado = 'PAGADO'
        gasto.usuario_modificacion = request.user
        gasto.save()

        serializer = self.get_serializer(gasto)
        return Response(serializer.data)


class RecepcionCompraViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de recepciones de compra"""
    queryset = RecepcionCompra.objects.all()
    serializer_class = RecepcionCompraSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_recepcion', 'orden_compra__proveedor__nombre', 'observaciones']
    ordering_fields = ['fecha_recepcion', 'estado']
    ordering = ['-fecha_recepcion']

    def get_queryset(self):
        queryset = super().get_queryset()

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        orden_compra = self.request.query_params.get('orden_compra')
        if orden_compra:
            queryset = queryset.filter(orden_compra_id=orden_compra)

        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_recepcion__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_recepcion__lte=fecha_hasta)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return RecepcionCompraListSerializer
        return RecepcionCompraSerializer

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirma una recepción y actualiza inventario"""
        recepcion = self.get_object()

        if recepcion.estado not in ['PENDIENTE', 'PARCIAL']:
            return Response(
                {'error': 'Solo se pueden confirmar recepciones en estado PENDIENTE o PARCIAL'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Actualizar inventario por cada detalle
                from inventario.models import MovimientoInventario, InventarioProducto

                for detalle in recepcion.detalles.all():
                    if detalle.cantidad_recibida > 0:
                        # Crear movimiento de inventario
                        MovimientoInventario.objects.create(
                            empresa=recepcion.empresa,
                            almacen=recepcion.almacen,
                            producto=detalle.producto,
                            tipo='ENTRADA_COMPRA',
                            cantidad=detalle.cantidad_recibida,
                            referencia=f"Recepción {recepcion.numero_recepcion}",
                            usuario_creacion=request.user
                        )

                        # Actualizar o crear inventario
                        inventario, created = InventarioProducto.objects.get_or_create(
                            empresa=recepcion.empresa,
                            almacen=recepcion.almacen,
                            producto=detalle.producto,
                            defaults={'cantidad': 0, 'costo_promedio': detalle.detalle_orden.costo_unitario}
                        )
                        inventario.cantidad += detalle.cantidad_recibida
                        inventario.save()

                        # Actualizar cantidad recibida en la orden de compra
                        detalle.detalle_orden.cantidad_recibida += detalle.cantidad_recibida
                        detalle.detalle_orden.save()

                # Verificar si la orden está completamente recibida
                orden = recepcion.orden_compra
                total_ordenado = sum(d.cantidad for d in orden.detalles.all())
                total_recibido = sum(d.cantidad_recibida for d in orden.detalles.all())

                if total_recibido >= total_ordenado:
                    orden.estado = 'RECIBIDA_TOTAL'
                    recepcion.estado = 'COMPLETA'
                else:
                    orden.estado = 'RECIBIDA_PARCIAL'
                    recepcion.estado = 'PARCIAL'

                orden.usuario_modificacion = request.user
                orden.save()
                recepcion.usuario_modificacion = request.user
                recepcion.save()

            serializer = self.get_serializer(recepcion)
            return Response({
                'recepcion': serializer.data,
                'mensaje': 'Recepción confirmada exitosamente. Inventario actualizado.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una recepción"""
        recepcion = self.get_object()

        if recepcion.estado not in ['PENDIENTE']:
            return Response(
                {'error': 'Solo se pueden cancelar recepciones en estado PENDIENTE'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recepcion.estado = 'CANCELADA'
        recepcion.usuario_modificacion = request.user
        recepcion.save()

        serializer = self.get_serializer(recepcion)
        return Response(serializer.data)


class DevolucionProveedorViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de devoluciones a proveedores"""
    queryset = DevolucionProveedor.objects.all()
    serializer_class = DevolucionProveedorSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_devolucion', 'proveedor__nombre', 'descripcion_motivo']
    ordering_fields = ['fecha', 'estado', 'total']
    ordering = ['-fecha']

    def get_queryset(self):
        queryset = super().get_queryset()

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_id=proveedor)

        motivo = self.request.query_params.get('motivo')
        if motivo:
            queryset = queryset.filter(motivo=motivo)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return DevolucionProveedorListSerializer
        return DevolucionProveedorSerializer

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirma una devolución y registra salida de inventario"""
        devolucion = self.get_object()

        if devolucion.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden confirmar devoluciones en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                from inventario.models import MovimientoInventario, InventarioProducto

                for detalle in devolucion.detalles.all():
                    # Verificar stock disponible
                    inventario = InventarioProducto.objects.filter(
                        empresa=devolucion.empresa,
                        almacen=detalle.almacen,
                        producto=detalle.producto
                    ).first()

                    if not inventario or inventario.cantidad < detalle.cantidad:
                        return Response(
                            {'error': f'Stock insuficiente para {detalle.producto.nombre} en almacén {detalle.almacen.nombre}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Crear movimiento de inventario (salida)
                    MovimientoInventario.objects.create(
                        empresa=devolucion.empresa,
                        almacen=detalle.almacen,
                        producto=detalle.producto,
                        tipo='DEVOLUCION_PROVEEDOR',
                        cantidad=-detalle.cantidad,  # Negativo para salida
                        referencia=f"Devolución {devolucion.numero_devolucion}",
                        usuario_creacion=request.user
                    )

                    # Actualizar inventario
                    inventario.cantidad -= detalle.cantidad
                    inventario.save()

                # Actualizar totales y estado
                devolucion.calcular_totales()
                devolucion.estado = 'CONFIRMADA'
                devolucion.usuario_modificacion = request.user
                devolucion.save()

                # Si genera nota de crédito, ajustar CxP
                if devolucion.genera_nota_credito and devolucion.compra:
                    from cuentas_pagar.models import CuentaPorPagar
                    cxp = CuentaPorPagar.objects.filter(compra=devolucion.compra).first()
                    if cxp:
                        cxp.monto_pendiente -= devolucion.total
                        if cxp.monto_pendiente <= 0:
                            cxp.monto_pendiente = 0
                            cxp.estado = 'PAGADA'
                        cxp.save()

            serializer = self.get_serializer(devolucion)
            return Response({
                'devolucion': serializer.data,
                'mensaje': 'Devolución confirmada exitosamente.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una devolución"""
        devolucion = self.get_object()

        if devolucion.estado not in ['BORRADOR']:
            return Response(
                {'error': 'Solo se pueden cancelar devoluciones en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        devolucion.estado = 'CANCELADA'
        devolucion.usuario_modificacion = request.user
        devolucion.save()

        serializer = self.get_serializer(devolucion)
        return Response(serializer.data)


class LiquidacionImportacionViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de liquidaciones de importación"""
    queryset = LiquidacionImportacion.objects.all()
    serializer_class = LiquidacionImportacionSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_liquidacion', 'compra__numero_factura_proveedor', 'compra__proveedor__nombre']
    ordering_fields = ['fecha', 'estado', 'total_cif']
    ordering = ['-fecha']

    def get_queryset(self):
        queryset = super().get_queryset()

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        compra = self.request.query_params.get('compra')
        if compra:
            queryset = queryset.filter(compra_id=compra)

        incoterm = self.request.query_params.get('incoterm')
        if incoterm:
            queryset = queryset.filter(incoterm=incoterm)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return LiquidacionImportacionListSerializer
        return LiquidacionImportacionSerializer

    @action(detail=True, methods=['post'])
    def liquidar(self, request, pk=None):
        """Liquida la importación y actualiza costos en inventario"""
        liquidacion = self.get_object()

        if liquidacion.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden liquidar importaciones en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Calcular totales
                liquidacion.calcular_totales()

                # Prorratear gastos entre productos de la compra
                detalles_compra = liquidacion.compra.detalles.all()
                total_valor_fob = sum(d.cantidad * d.costo_unitario for d in detalles_compra)

                if total_valor_fob <= 0:
                    return Response(
                        {'error': 'El valor FOB total debe ser mayor a cero'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Actualizar costo en inventario por cada producto
                from inventario.models import InventarioProducto

                for detalle in detalles_compra:
                    valor_fob_linea = detalle.cantidad * detalle.costo_unitario
                    proporcion = valor_fob_linea / total_valor_fob
                    gasto_prorrateado = liquidacion.total_gastos * proporcion
                    costo_total_linea = valor_fob_linea + gasto_prorrateado
                    costo_unitario_nacionalizado = costo_total_linea / detalle.cantidad if detalle.cantidad > 0 else 0

                    # Actualizar costo promedio en inventario
                    inventarios = InventarioProducto.objects.filter(
                        empresa=liquidacion.empresa,
                        producto=detalle.producto
                    )
                    for inv in inventarios:
                        # Cálculo de costo promedio ponderado
                        if inv.cantidad > 0:
                            costo_actual_total = inv.cantidad * inv.costo_promedio
                            costo_nuevo_total = detalle.cantidad * costo_unitario_nacionalizado
                            inv.costo_promedio = (costo_actual_total + costo_nuevo_total) / (inv.cantidad + detalle.cantidad)
                            inv.save()

                liquidacion.estado = 'LIQUIDADA'
                liquidacion.usuario_modificacion = request.user
                liquidacion.save()

            serializer = self.get_serializer(liquidacion)
            return Response({
                'liquidacion': serializer.data,
                'mensaje': 'Liquidación completada. Costos actualizados en inventario.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una liquidación"""
        liquidacion = self.get_object()

        if liquidacion.estado not in ['BORRADOR']:
            return Response(
                {'error': 'Solo se pueden cancelar liquidaciones en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        liquidacion.estado = 'CANCELADA'
        liquidacion.usuario_modificacion = request.user
        liquidacion.save()

        serializer = self.get_serializer(liquidacion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def agregar_gasto(self, request, pk=None):
        """Agrega un gasto a la liquidación"""
        liquidacion = self.get_object()

        if liquidacion.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden agregar gastos a liquidaciones en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = GastoImportacionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(liquidacion=liquidacion)
            liquidacion.calcular_totales()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# RETENCIONES FISCALES
# =============================================================================

class TipoRetencionViewSet(EmpresaFilterMixin, EmpresaAuditMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar tipos de retención fiscal"""
    queryset = TipoRetencion.objects.all()
    serializer_class = TipoRetencionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['categoria', 'activo', 'aplica_a_persona_fisica', 'aplica_a_persona_juridica']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['codigo', 'nombre', 'porcentaje']
    ordering = ['categoria', 'codigo']

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class RetencionCompraViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """ViewSet para gestionar retenciones aplicadas a compras"""
    queryset = RetencionCompra.objects.select_related(
        'compra', 'tipo_retencion', 'usuario_creacion'
    ).all()
    serializer_class = RetencionCompraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['compra', 'tipo_retencion', 'tipo_retencion__categoria']
    search_fields = ['compra__numero_factura_proveedor', 'tipo_retencion__nombre']
    ordering_fields = ['fecha_aplicacion', 'monto_retenido']
    ordering = ['-fecha_creacion']

    def perform_create(self, serializer):
        tipo_retencion = serializer.validated_data.get('tipo_retencion')
        serializer.save(
            empresa=self.request.user.empresa,
            usuario_creacion=self.request.user,
            porcentaje=tipo_retencion.porcentaje if not serializer.validated_data.get('porcentaje') else serializer.validated_data['porcentaje']
        )

    @action(detail=False, methods=['get'])
    def por_compra(self, request):
        """Retorna retenciones de una compra específica"""
        compra_id = request.query_params.get('compra_id')
        if not compra_id:
            return Response(
                {'error': 'Debe especificar compra_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        retenciones = self.get_queryset().filter(compra_id=compra_id)
        serializer = self.get_serializer(retenciones, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen_periodo(self, request):
        """Resumen de retenciones por período (mes/año)"""
        from django.db.models import Sum
        from decimal import Decimal

        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')

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

        empresa = request.user.empresa
        retenciones = RetencionCompra.objects.filter(
            empresa=empresa,
            fecha_aplicacion__year=anio,
            fecha_aplicacion__month=mes
        )

        isr_total = retenciones.filter(
            tipo_retencion__categoria='ISR'
        ).aggregate(total=Sum('monto_retenido'))['total'] or Decimal('0')

        itbis_total = retenciones.filter(
            tipo_retencion__categoria='ITBIS'
        ).aggregate(total=Sum('monto_retenido'))['total'] or Decimal('0')

        return Response({
            'periodo': f'{anio}-{mes:02d}',
            'isr_retenido': str(isr_total),
            'itbis_retenido': str(itbis_total),
            'total_retenciones': str(isr_total + itbis_total),
            'cantidad_retenciones': retenciones.count()
        })


class CompraRetencionMixin:
    """Mixin para agregar acción de aplicar retención a CompraViewSet"""

    @action(detail=True, methods=['post'])
    def aplicar_retencion(self, request, pk=None):
        """Aplica una retención a la compra"""
        compra = self.get_object()

        serializer = AplicarRetencionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tipo_retencion_id = serializer.validated_data['tipo_retencion_id']
        base_imponible = serializer.validated_data.get('base_imponible', compra.subtotal)
        observaciones = serializer.validated_data.get('observaciones', '')

        try:
            tipo_retencion = TipoRetencion.objects.get(
                id=tipo_retencion_id,
                empresa=request.user.empresa,
                activo=True
            )
        except TipoRetencion.DoesNotExist:
            return Response(
                {'error': 'Tipo de retención no encontrado o inactivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular monto
        from decimal import Decimal
        monto = (base_imponible * tipo_retencion.porcentaje) / Decimal('100')

        # Crear la retención
        retencion = RetencionCompra.objects.create(
            empresa=request.user.empresa,
            compra=compra,
            tipo_retencion=tipo_retencion,
            base_imponible=base_imponible,
            porcentaje=tipo_retencion.porcentaje,
            monto_retenido=monto,
            observaciones=observaciones,
            usuario_creacion=request.user
        )

        return Response(
            RetencionCompraSerializer(retencion).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def retenciones(self, request, pk=None):
        """Lista las retenciones aplicadas a una compra"""
        compra = self.get_object()
        retenciones = RetencionCompra.objects.filter(compra=compra)
        serializer = RetencionCompraSerializer(retenciones, many=True)
        return Response(serializer.data)

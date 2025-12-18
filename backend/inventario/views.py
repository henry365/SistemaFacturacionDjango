from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from django.db import transaction
from .models import (
    Almacen, InventarioProducto, MovimientoInventario,
    ReservaStock, Lote, AlertaInventario,
    TransferenciaInventario, DetalleTransferencia,
    AjusteInventario, DetalleAjusteInventario,
    ConteoFisico, DetalleConteoFisico
)
from .serializers import (
    AlmacenSerializer, InventarioProductoSerializer, MovimientoInventarioSerializer,
    ReservaStockSerializer, LoteSerializer, AlertaInventarioSerializer,
    TransferenciaInventarioSerializer, DetalleTransferenciaSerializer,
    AjusteInventarioSerializer, DetalleAjusteInventarioSerializer,
    ConteoFisicoSerializer, DetalleConteoFisicoSerializer
)
from .services import ServicioInventario, ServicioAlertasInventario
from usuarios.permissions import ActionBasedPermission
from core.mixins import IdempotencyMixin, EmpresaFilterMixin, EmpresaAuditMixin, EmpresaFilterMixin, EmpresaAuditMixin

class AlmacenViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Almacen.objects.all()
    serializer_class = AlmacenSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'direccion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_queryset(self):
        """Filtrar almacenes según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear almacén"""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)

class InventarioProductoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    # InventarioProducto generalmente no se crea directamente via API, sino por movimientos
    queryset = InventarioProducto.objects.all()
    serializer_class = InventarioProductoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['producto__nombre', 'cantidad_disponible', 'fecha_creacion']
    ordering = ['producto__nombre']
    
    def get_queryset(self):
        """Filtrar inventarios según empresa del usuario"""
        queryset = super().get_queryset()
        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)
        
        producto = self.request.query_params.get('producto')
        if producto:
            queryset = queryset.filter(producto_id=producto)
        
        bajo_minimo = self.request.query_params.get('bajo_minimo')
        if bajo_minimo == 'true':
            queryset = queryset.filter(cantidad_disponible__lte=F('stock_minimo'))
        
        return queryset

class MovimientoInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['producto__nombre', 'producto__codigo_sku', 'referencia']
    ordering_fields = ['fecha', 'tipo_movimiento']
    ordering = ['-fecha']
    
    def get_queryset(self):
        """Filtrar movimientos según empresa del usuario"""
        queryset = super().get_queryset()
        producto = self.request.query_params.get('producto')
        if producto:
            queryset = queryset.filter(producto_id=producto)
        
        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)
        
        tipo_movimiento = self.request.query_params.get('tipo_movimiento')
        if tipo_movimiento:
            queryset = queryset.filter(tipo_movimiento=tipo_movimiento)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear movimiento"""
        user = self.request.user
        kwargs = {
            'usuario': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    @action(detail=False, methods=['get'], url_path='kardex')
    def kardex(self, request):
        """
        Endpoint de Kardex según especificaciones.
        Devuelve el historial de movimientos por producto y almacén, con saldo acumulado.
        
        Parámetros de consulta:
        - producto_id: ID del producto (requerido)
        - almacen_id: ID del almacén (requerido)
        - fecha_desde: Fecha inicial (opcional, formato YYYY-MM-DD)
        - fecha_hasta: Fecha final (opcional, formato YYYY-MM-DD)
        """
        producto_id = request.query_params.get('producto_id')
        almacen_id = request.query_params.get('almacen_id')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if not producto_id or not almacen_id:
            return Response(
                {'error': 'Los parámetros producto_id y almacen_id son requeridos'},
                status=400
            )
        
        # Filtrar movimientos por empresa también
        user = request.user
        queryset = MovimientoInventario.objects.filter(
            producto_id=producto_id,
            almacen_id=almacen_id
        )
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        queryset = queryset.select_related('producto', 'almacen', 'usuario', 'lote').order_by('fecha')
        
        # Filtros opcionales de fecha
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        # Calcular saldo inicial
        # Si hay fecha_desde, calcular saldo hasta esa fecha
        if fecha_desde:
            movimientos_anteriores = MovimientoInventario.objects.filter(
                producto_id=producto_id,
                almacen_id=almacen_id,
                fecha__lt=fecha_desde
            )
            if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
                movimientos_anteriores = movimientos_anteriores.filter(empresa=user.empresa)
            
            # Calcular saldo inicial sumando entradas y restando salidas
            entradas = movimientos_anteriores.filter(
                tipo_movimiento__in=[
                    'ENTRADA_COMPRA', 'ENTRADA_AJUSTE', 'TRANSFERENCIA_ENTRADA',
                    'DEVOLUCION_CLIENTE'
                ]
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            salidas = movimientos_anteriores.filter(
                tipo_movimiento__in=[
                    'SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA',
                    'DEVOLUCION_PROVEEDOR'
                ]
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            saldo_inicial = entradas - salidas
        else:
            # Si no hay fecha_desde, el saldo inicial es 0 (asumiendo que empezó desde cero)
            # O podríamos usar el inventario actual menos los movimientos del período
            saldo_inicial = 0
        
        saldo_acumulado = saldo_inicial
        
        # Construir respuesta con saldo acumulado
        movimientos = []
        for movimiento in queryset:
            # Calcular saldo acumulado
            if movimiento.tipo_movimiento in [
                'ENTRADA_COMPRA', 'ENTRADA_AJUSTE', 'TRANSFERENCIA_ENTRADA',
                'DEVOLUCION_CLIENTE'
            ]:
                saldo_acumulado += movimiento.cantidad
            elif movimiento.tipo_movimiento in [
                'SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA',
                'DEVOLUCION_PROVEEDOR'
            ]:
                saldo_acumulado -= movimiento.cantidad
            
            movimientos.append({
                'id': movimiento.id,
                'fecha': movimiento.fecha,
                'tipo_movimiento': movimiento.tipo_movimiento,
                'tipo_movimiento_display': movimiento.get_tipo_movimiento_display(),
                'cantidad': float(movimiento.cantidad),
                'costo_unitario': float(movimiento.costo_unitario),
                'valor_total': float(movimiento.cantidad * movimiento.costo_unitario),
                'saldo_acumulado': float(saldo_acumulado),
                'referencia': movimiento.referencia,
                'numero_serie': movimiento.numero_serie,
                'numero_lote_proveedor': movimiento.numero_lote_proveedor,
                'lote_codigo': movimiento.lote.codigo_lote if movimiento.lote else None,
                'usuario': movimiento.usuario.username,
                'notas': movimiento.notas,
                'producto': {
                    'id': movimiento.producto.id,
                    'nombre': movimiento.producto.nombre,
                    'codigo_sku': movimiento.producto.codigo_sku,
                },
                'almacen': {
                    'id': movimiento.almacen.id,
                    'nombre': movimiento.almacen.nombre,
                },
            })
        
        # Información del producto y almacén
        producto = queryset.first().producto if queryset.exists() else None
        almacen = queryset.first().almacen if queryset.exists() else None
        
        return Response({
            'producto': {
                'id': producto.id if producto else producto_id,
                'nombre': producto.nombre if producto else None,
                'codigo_sku': producto.codigo_sku if producto else None,
            },
            'almacen': {
                'id': almacen.id if almacen else almacen_id,
                'nombre': almacen.nombre if almacen else None,
            },
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'saldo_inicial': float(saldo_inicial),
            'saldo_final': float(saldo_acumulado),
            'total_movimientos': len(movimientos),
            'movimientos': movimientos,
        })


# ========== VIEWSETS DE RESERVAS ==========

class ReservaStockViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = ReservaStock.objects.all()
    serializer_class = ReservaStockSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['referencia', 'inventario__producto__nombre']
    ordering_fields = ['fecha_reserva', 'estado']
    
    def get_queryset(self):
        """Filtrar reservas según empresa del usuario"""
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear reserva"""
        user = self.request.user
        kwargs = {
            'usuario': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirma una reserva de stock"""
        reserva = self.get_object()
        try:
            ServicioInventario.confirmar_reserva(reserva)
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela una reserva de stock"""
        reserva = self.get_object()
        try:
            ServicioInventario.cancelar_reserva(reserva)
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ========== VIEWSETS DE LOTES ==========

class LoteViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo_lote', 'numero_lote', 'producto__nombre', 'producto__codigo_sku']
    ordering_fields = ['fecha_ingreso', 'fecha_vencimiento', 'estado']
    
    def get_queryset(self):
        """Filtrar lotes según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        vencidos = self.request.query_params.get('vencidos')
        if vencidos == 'true':
            queryset = queryset.filter(fecha_vencimiento__lt=timezone.now().date())
        
        producto = self.request.query_params.get('producto')
        if producto:
            queryset = queryset.filter(producto_id=producto)
        
        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear lote"""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)


# ========== VIEWSETS DE ALERTAS ==========

class AlertaInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = AlertaInventario.objects.all()
    serializer_class = AlertaInventarioSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['mensaje', 'inventario__producto__nombre', 'lote__codigo_lote']
    ordering_fields = ['fecha_alerta', 'prioridad', 'tipo']
    ordering = ['-fecha_alerta']
    
    def get_queryset(self):
        """Filtrar alertas según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        # Filtrar solo alertas no resueltas por defecto
        resueltas = self.request.query_params.get('resueltas')
        if resueltas != 'true':
            queryset = queryset.filter(resuelta=False)
        
        # Filtros adicionales
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        prioridad = self.request.query_params.get('prioridad')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear alerta"""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Marca una alerta como resuelta"""
        alerta = self.get_object()
        alerta.resuelta = True
        alerta.usuario_resolucion = request.user
        alerta.fecha_resuelta = timezone.now()
        alerta.save()
        serializer = self.get_serializer(alerta)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generar_alertas(self, request):
        """Genera todas las alertas de inventario"""
        try:
            resultado = ServicioAlertasInventario.generar_todas_las_alertas()
            return Response({
                'mensaje': 'Alertas generadas exitosamente',
                'resultado': resultado
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ========== VIEWSETS DE TRANSFERENCIAS ==========

class DetalleTransferenciaViewSet(viewsets.ModelViewSet):
    queryset = DetalleTransferencia.objects.all()
    serializer_class = DetalleTransferenciaSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]


class TransferenciaInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = TransferenciaInventario.objects.all()
    serializer_class = TransferenciaInventarioSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_transferencia', 'almacen_origen__nombre', 'almacen_destino__nombre']
    ordering_fields = ['fecha_solicitud', 'estado']
    ordering = ['-fecha_solicitud']
    
    def get_queryset(self):
        """Filtrar transferencias según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        almacen_origen = self.request.query_params.get('almacen_origen')
        if almacen_origen:
            queryset = queryset.filter(almacen_origen_id=almacen_origen)
        
        almacen_destino = self.request.query_params.get('almacen_destino')
        if almacen_destino:
            queryset = queryset.filter(almacen_destino_id=almacen_destino)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear transferencia"""
        user = self.request.user
        kwargs = {
            'usuario_solicitante': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)
    
    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Marca la transferencia como enviada"""
        transferencia = self.get_object()
        if transferencia.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden enviar transferencias pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transferencia.estado = 'EN_TRANSITO'
        transferencia.fecha_envio = timezone.now()
        transferencia.save()
        
        # Registrar movimientos de salida para cada detalle
        detalles = transferencia.detalles.all()
        for detalle in detalles:
            if detalle.cantidad_enviada > 0:
                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=transferencia.almacen_origen,
                    tipo_movimiento='TRANSFERENCIA_SALIDA',
                    cantidad=detalle.cantidad_enviada,
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=transferencia.empresa,
                    referencia=f"TRF-{transferencia.numero_transferencia}",
                    lote=detalle.lote
                )
        
        serializer = self.get_serializer(transferencia)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def recibir(self, request, pk=None):
        """Marca la transferencia como recibida"""
        transferencia = self.get_object()
        if transferencia.estado not in ['EN_TRANSITO', 'RECIBIDA_PARCIAL']:
            return Response(
                {'error': 'Solo se pueden recibir transferencias en tránsito'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transferencia.estado = 'RECIBIDA'
        transferencia.fecha_recepcion = timezone.now()
        transferencia.usuario_receptor = request.user
        transferencia.save()
        
        # Registrar movimientos de entrada para cada detalle recibido
        detalles = transferencia.detalles.all()
        for detalle in detalles:
            if detalle.cantidad_recibida > 0:
                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=transferencia.almacen_destino,
                    tipo_movimiento='TRANSFERENCIA_ENTRADA',
                    cantidad=detalle.cantidad_recibida,
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=transferencia.empresa,
                    referencia=f"TRF-{transferencia.numero_transferencia}",
                    lote=detalle.lote
                )
        
        serializer = self.get_serializer(transferencia)
        return Response(serializer.data)


# ========== VIEWSETS DE AJUSTES ==========

class DetalleAjusteInventarioViewSet(viewsets.ModelViewSet):
    queryset = DetalleAjusteInventario.objects.all()
    serializer_class = DetalleAjusteInventarioSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]


class AjusteInventarioViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = AjusteInventario.objects.all()
    serializer_class = AjusteInventarioSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['motivo', 'almacen__nombre']
    ordering_fields = ['fecha_ajuste', 'estado']
    ordering = ['-fecha_ajuste']
    
    def get_queryset(self):
        """Filtrar ajustes según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        tipo_ajuste = self.request.query_params.get('tipo_ajuste')
        if tipo_ajuste:
            queryset = queryset.filter(tipo_ajuste=tipo_ajuste)
        
        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear ajuste"""
        user = self.request.user
        kwargs = {
            'usuario_solicitante': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un ajuste de inventario"""
        ajuste = self.get_object()
        if ajuste.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden aprobar ajustes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ajuste.estado = 'APROBADO'
        ajuste.usuario_aprobador = request.user
        ajuste.fecha_aprobacion = timezone.now()
        ajuste.observaciones_aprobacion = request.data.get('observaciones', '')
        ajuste.save()
        
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechaza un ajuste de inventario"""
        ajuste = self.get_object()
        if ajuste.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden rechazar ajustes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ajuste.estado = 'RECHAZADO'
        ajuste.usuario_aprobador = request.user
        ajuste.fecha_aprobacion = timezone.now()
        ajuste.observaciones_aprobacion = request.data.get('observaciones', '')
        ajuste.save()
        
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def procesar(self, request, pk=None):
        """Procesa un ajuste aprobado (aplica los cambios al inventario)"""
        ajuste = self.get_object()
        if ajuste.estado != 'APROBADO':
            return Response(
                {'error': 'Solo se pueden procesar ajustes aprobados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aplicar cada detalle del ajuste
        for detalle in ajuste.detalles.all():
            if detalle.diferencia != 0:
                tipo_movimiento = 'ENTRADA_AJUSTE' if detalle.diferencia > 0 else 'SALIDA_AJUSTE'
                
                ServicioInventario.registrar_movimiento(
                    producto=detalle.producto,
                    almacen=ajuste.almacen,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=abs(detalle.diferencia),
                    costo_unitario=detalle.costo_unitario,
                    usuario=request.user,
                    empresa=ajuste.empresa,
                    referencia=f"AJUSTE-{ajuste.id}",
                    lote=detalle.lote,
                    notas=f"Ajuste: {ajuste.motivo}"
                )
        
        ajuste.estado = 'PROCESADO'
        ajuste.save()
        
        serializer = self.get_serializer(ajuste)
        return Response(serializer.data)


# ========== VIEWSETS DE CONTEO FÍSICO ==========

class DetalleConteoFisicoViewSet(viewsets.ModelViewSet):
    queryset = DetalleConteoFisico.objects.all()
    serializer_class = DetalleConteoFisicoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]


class ConteoFisicoViewSet(EmpresaFilterMixin, EmpresaAuditMixin, IdempotencyMixin, viewsets.ModelViewSet):
    queryset = ConteoFisico.objects.all()
    serializer_class = ConteoFisicoSerializer
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_conteo', 'almacen__nombre']
    ordering_fields = ['fecha_conteo', 'estado']
    ordering = ['-fecha_conteo']
    
    def get_queryset(self):
        """Filtrar conteos según empresa del usuario"""
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        tipo_conteo = self.request.query_params.get('tipo_conteo')
        if tipo_conteo:
            queryset = queryset.filter(tipo_conteo=tipo_conteo)
        
        almacen = self.request.query_params.get('almacen')
        if almacen:
            queryset = queryset.filter(almacen_id=almacen)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear conteo"""
        user = self.request.user
        kwargs = {
            'usuario_responsable': user,
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Inicia un conteo físico"""
        conteo = self.get_object()
        if conteo.estado != 'PLANIFICADO':
            return Response(
                {'error': 'Solo se pueden iniciar conteos planificados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conteo.estado = 'EN_PROCESO'
        conteo.fecha_inicio = timezone.now()
        conteo.save()
        
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finaliza un conteo físico"""
        conteo = self.get_object()
        if conteo.estado != 'EN_PROCESO':
            return Response(
                {'error': 'Solo se pueden finalizar conteos en proceso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conteo.estado = 'FINALIZADO'
        conteo.fecha_fin = timezone.now()
        conteo.save()
        
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def ajustar(self, request, pk=None):
        """Ajusta el inventario basado en las diferencias del conteo"""
        conteo = self.get_object()
        if conteo.estado != 'FINALIZADO':
            return Response(
                {'error': 'Solo se pueden ajustar conteos finalizados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear ajuste automático basado en las diferencias
        ajuste = AjusteInventario.objects.create(
            empresa=conteo.empresa,
            almacen=conteo.almacen,
            tipo_ajuste='AJUSTE_DIFERENCIA',
            motivo=f'Ajuste por conteo físico {conteo.numero_conteo}',
            fecha_ajuste=conteo.fecha_conteo,
            estado='APROBADO',  # Auto-aprobado porque viene de conteo
            usuario_solicitante=conteo.usuario_responsable,
            usuario_aprobador=conteo.usuario_responsable,
            fecha_aprobacion=timezone.now()
        )
        
        # Crear detalles del ajuste
        for detalle_conteo in conteo.detalles.all():
            if detalle_conteo.diferencia != 0:
                DetalleAjusteInventario.objects.create(
                    ajuste=ajuste,
                    producto=detalle_conteo.producto,
                    lote=detalle_conteo.lote,
                    cantidad_anterior=detalle_conteo.cantidad_sistema,
                    cantidad_nueva=detalle_conteo.cantidad_fisica,
                    costo_unitario=detalle_conteo.producto.precio_venta_base  # Usar precio base como referencia
                )
        
        # Procesar el ajuste automáticamente
        for detalle_conteo in conteo.detalles.all():
            if detalle_conteo.diferencia != 0:
                tipo_movimiento = 'ENTRADA_AJUSTE' if detalle_conteo.diferencia > 0 else 'SALIDA_AJUSTE'
                
                ServicioInventario.registrar_movimiento(
                    producto=detalle_conteo.producto,
                    almacen=conteo.almacen,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=abs(detalle_conteo.diferencia),
                    costo_unitario=detalle_conteo.producto.precio_venta_base,
                    usuario=request.user,
                    empresa=conteo.empresa,
                    referencia=f"CONTEO-{conteo.numero_conteo}",
                    lote=detalle_conteo.lote,
                    notas=f"Ajuste por conteo físico {conteo.numero_conteo}"
                )
        
        conteo.estado = 'AJUSTADO'
        conteo.save()
        
        serializer = self.get_serializer(conteo)
        return Response(serializer.data)

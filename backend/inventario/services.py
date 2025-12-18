"""
Servicios para manejar la lógica de negocio del inventario
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import (
    InventarioProducto, MovimientoInventario, ReservaStock,
    AlertaInventario, Lote
)


class ServicioInventario:
    """Servicio principal para operaciones de inventario"""
    
    @staticmethod
    def puede_realizar_movimiento(producto, tipo_movimiento, cantidad, almacen):
        """
        Valida si se puede realizar un movimiento según reglas de negocio.
        Retorna (puede_realizar, mensaje_error)
        """
        # Servicios no tienen inventario
        if producto.tipo_producto == 'SERVICIO':
            return False, "Los servicios no tienen inventario"
        
        # Productos que no controlan stock
        if not producto.controlar_stock:
            return True, None
        
        # Validar stock para salidas
        if tipo_movimiento in ['SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA']:
            try:
                # Usar select_for_update para evitar condiciones de carrera
                inventario = InventarioProducto.objects.select_for_update().get(
                    producto=producto,
                    almacen=almacen
                )
                
                if not inventario.tiene_stock_suficiente(cantidad):
                    return False, (
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Disponible: {inventario.stock_disponible_real}, "
                        f"Solicitado: {cantidad}"
                    )
            except InventarioProducto.DoesNotExist:
                return False, f"No existe inventario para {producto.nombre} en {almacen.nombre}"
        
        return True, None
    
    @staticmethod
    @transaction.atomic
    def registrar_movimiento(
        producto, almacen, tipo_movimiento, cantidad, costo_unitario,
        usuario, empresa, referencia=None, lote=None, notas=None
    ):
        """
        Registra un movimiento de inventario y actualiza el stock.
        """
        # Validar movimiento
        puede, mensaje = ServicioInventario.puede_realizar_movimiento(
            producto, tipo_movimiento, cantidad, almacen
        )
        if not puede:
            raise ValidationError(mensaje)
        
        # Obtener o crear inventario con bloqueo para evitar condiciones de carrera
        inventario, created = InventarioProducto.objects.select_for_update().get_or_create(
            producto=producto,
            almacen=almacen,
            empresa=empresa,
            defaults={'costo_promedio': costo_unitario}
        )
        
        # Crear movimiento
        movimiento = MovimientoInventario.objects.create(
            empresa=empresa,
            producto=producto,
            almacen=almacen,
            tipo_movimiento=tipo_movimiento,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            referencia=referencia,
            lote=lote,
            usuario=usuario,
            notas=notas,
            tipo_documento_origen='AJUSTE' if 'AJUSTE' in tipo_movimiento else None,
            usuario_creacion=usuario,
            usuario_modificacion=usuario
        )
        
        # Actualizar inventario según tipo de movimiento
        if tipo_movimiento in ['ENTRADA_COMPRA', 'ENTRADA_AJUSTE', 'TRANSFERENCIA_ENTRADA', 'DEVOLUCION_CLIENTE']:
            # Entrada: aumentar stock y actualizar costo promedio
            inventario.cantidad_disponible += cantidad
            if tipo_movimiento == 'ENTRADA_COMPRA':
                inventario.actualizar_costo_promedio(cantidad, costo_unitario)
            else:
                # Para otros tipos, mantener el costo promedio actual
                pass
        
        elif tipo_movimiento in ['SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA', 'DEVOLUCION_PROVEEDOR']:
            # Salida: disminuir stock
            inventario.cantidad_disponible -= cantidad
        
        inventario.save()
        
        # Actualizar lote si existe
        if lote:
            if tipo_movimiento in ['ENTRADA_COMPRA', 'ENTRADA_AJUSTE']:
                lote.cantidad_disponible += cantidad
            elif tipo_movimiento in ['SALIDA_VENTA', 'SALIDA_AJUSTE']:
                lote.cantidad_disponible -= cantidad
            
            # Actualizar estado del lote
            if lote.cantidad_disponible == 0:
                lote.estado = 'AGOTADO'
            elif lote.cantidad_disponible > 0 and lote.estado == 'AGOTADO':
                lote.estado = 'DISPONIBLE'
            
            lote.save()
        
        return movimiento
    
    @staticmethod
    @transaction.atomic
    def crear_reserva(inventario, cantidad, referencia, usuario, empresa=None, fecha_vencimiento=None):
        """Crea una reserva de stock"""
        # Bloquear inventario para evitar condiciones de carrera
        inventario = InventarioProducto.objects.select_for_update().get(pk=inventario.pk)
        
        if not inventario.tiene_stock_suficiente(cantidad):
            raise ValidationError(
                f"Stock insuficiente. Disponible: {inventario.stock_disponible_real}, "
                f"Solicitado: {cantidad}"
            )
        
        # Usar empresa del inventario si no se proporciona
        if not empresa and inventario.empresa:
            empresa = inventario.empresa
        
        reserva = ReservaStock.objects.create(
            inventario=inventario,
            cantidad_reservada=cantidad,
            referencia=referencia,
            usuario=usuario,
            empresa=empresa,
            usuario_creacion=usuario,
            usuario_modificacion=usuario,
            fecha_vencimiento=fecha_vencimiento
        )
        
        return reserva
    
    @staticmethod
    @transaction.atomic
    def confirmar_reserva(reserva):
        """Confirma una reserva y la marca como confirmada"""
        reserva.estado = 'CONFIRMADA'
        reserva.save()
        return reserva
    
    @staticmethod
    @transaction.atomic
    def cancelar_reserva(reserva):
        """Cancela una reserva"""
        reserva.estado = 'CANCELADA'
        reserva.save()
        return reserva


class ServicioAlertasInventario:
    """Servicio para generar y gestionar alertas de inventario"""
    
    @staticmethod
    def verificar_stock_bajo():
        """Genera alertas para productos bajo mínimo"""
        inventarios = InventarioProducto.objects.filter(
            cantidad_disponible__lte=F('stock_minimo'),
            producto__activo=True
        ).select_related('producto', 'almacen', 'empresa')
        
        alertas_creadas = 0
        for inventario in inventarios:
            if inventario.cantidad_disponible == 0:
                tipo = 'STOCK_AGOTADO'
                prioridad = 'CRITICA'
            else:
                tipo = 'STOCK_BAJO'
                prioridad = 'ALTA' if inventario.cantidad_disponible < inventario.punto_reorden else 'MEDIA'
            
            # Verificar si ya existe una alerta activa
            existe_alerta = AlertaInventario.objects.filter(
                inventario=inventario,
                tipo=tipo,
                resuelta=False
            ).exists()
            
            if not existe_alerta:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                # Usar el primer usuario del sistema o None si no hay usuarios
                usuario_creacion = User.objects.filter(is_active=True).first()
                AlertaInventario.objects.create(
                    empresa=inventario.empresa,
                    inventario=inventario,
                    tipo=tipo,
                    prioridad=prioridad,
                    mensaje=(
                        f"Stock bajo mínimo para {inventario.producto.nombre} en {inventario.almacen.nombre}. "
                        f"Disponible: {inventario.cantidad_disponible}, "
                        f"Mínimo: {inventario.stock_minimo}"
                    ),
                    usuario_creacion=usuario_creacion,
                    usuario_modificacion=usuario_creacion
                )
                alertas_creadas += 1
        
        return alertas_creadas
    
    @staticmethod
    def verificar_vencimientos(dias_antes=30):
        """Genera alertas para lotes próximos a vencer"""
        fecha_limite = timezone.now().date() + timedelta(days=dias_antes)
        fecha_hoy = timezone.now().date()
        
        # Lotes próximos a vencer
        lotes = Lote.objects.filter(
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gte=fecha_hoy,
            estado='DISPONIBLE',
            cantidad_disponible__gt=0
        ).select_related('producto', 'almacen', 'empresa')
        
        alertas_creadas = 0
        for lote in lotes:
            dias_restantes = (lote.fecha_vencimiento - fecha_hoy).days
            tipo = 'VENCIMIENTO_PROXIMO'
            
            if dias_restantes <= 7:
                prioridad = 'CRITICA'
            elif dias_restantes <= 15:
                prioridad = 'ALTA'
            else:
                prioridad = 'MEDIA'
            
            # Verificar si ya existe una alerta activa
            existe_alerta = AlertaInventario.objects.filter(
                lote=lote,
                tipo=tipo,
                resuelta=False
            ).exists()
            
            if not existe_alerta:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                usuario_creacion = User.objects.filter(is_active=True).first()
                AlertaInventario.objects.create(
                    empresa=lote.empresa,
                    lote=lote,
                    tipo=tipo,
                    prioridad=prioridad,
                    mensaje=(
                        f"Lote {lote.codigo_lote} de {lote.producto.nombre} vence en {dias_restantes} días "
                        f"({lote.fecha_vencimiento.strftime('%d/%m/%Y')})"
                    ),
                    usuario_creacion=usuario_creacion,
                    usuario_modificacion=usuario_creacion
                )
                alertas_creadas += 1
        
        # Lotes vencidos
        lotes_vencidos = Lote.objects.filter(
            fecha_vencimiento__lt=fecha_hoy,
            estado='DISPONIBLE',
            cantidad_disponible__gt=0
        ).select_related('producto', 'almacen', 'empresa')
        
        for lote in lotes_vencidos:
            tipo = 'VENCIMIENTO_VENCIDO'
            prioridad = 'CRITICA'
            
            existe_alerta = AlertaInventario.objects.filter(
                lote=lote,
                tipo=tipo,
                resuelta=False
            ).exists()
            
            if not existe_alerta:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                usuario_creacion = User.objects.filter(is_active=True).first()
                dias_vencido = (fecha_hoy - lote.fecha_vencimiento).days
                AlertaInventario.objects.create(
                    empresa=lote.empresa,
                    lote=lote,
                    tipo=tipo,
                    prioridad=prioridad,
                    mensaje=(
                        f"Lote {lote.codigo_lote} de {lote.producto.nombre} está vencido "
                        f"desde hace {dias_vencido} días ({lote.fecha_vencimiento.strftime('%d/%m/%Y')})"
                    ),
                    usuario_creacion=usuario_creacion,
                    usuario_modificacion=usuario_creacion
                )
                alertas_creadas += 1
        
        return alertas_creadas
    
    @staticmethod
    def verificar_stock_excesivo():
        """Genera alertas para productos con stock excesivo"""
        inventarios = InventarioProducto.objects.filter(
            cantidad_disponible__gte=F('stock_maximo'),
            stock_maximo__gt=0,
            producto__activo=True
        ).select_related('producto', 'almacen', 'empresa')
        
        alertas_creadas = 0
        for inventario in inventarios:
            tipo = 'STOCK_EXCESIVO'
            prioridad = 'MEDIA'
            
            existe_alerta = AlertaInventario.objects.filter(
                inventario=inventario,
                tipo=tipo,
                resuelta=False
            ).exists()
            
            if not existe_alerta:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                usuario_creacion = User.objects.filter(is_active=True).first()
                AlertaInventario.objects.create(
                    empresa=inventario.empresa,
                    inventario=inventario,
                    tipo=tipo,
                    prioridad=prioridad,
                    mensaje=(
                        f"Stock excesivo para {inventario.producto.nombre} en {inventario.almacen.nombre}. "
                        f"Disponible: {inventario.cantidad_disponible}, "
                        f"Máximo: {inventario.stock_maximo}"
                    ),
                    usuario_creacion=usuario_creacion,
                    usuario_modificacion=usuario_creacion
                )
                alertas_creadas += 1
        
        return alertas_creadas
    
    @staticmethod
    def generar_todas_las_alertas():
        """Genera todas las alertas de inventario"""
        stock_bajo = ServicioAlertasInventario.verificar_stock_bajo()
        vencimientos = ServicioAlertasInventario.verificar_vencimientos()
        stock_excesivo = ServicioAlertasInventario.verificar_stock_excesivo()
        
        return {
            'stock_bajo': stock_bajo,
            'vencimientos': vencimientos,
            'stock_excesivo': stock_excesivo,
            'total': stock_bajo + vencimientos + stock_excesivo
        }


class ServicioKardex:
    """
    Servicio para cálculo de Kardex con saldos acumulados.

    El Kardex es un registro detallado de movimientos de inventario
    que muestra el saldo acumulado después de cada operación.
    """

    @staticmethod
    def obtener_kardex(producto_id, almacen_id=None, fecha_desde=None, fecha_hasta=None, empresa=None):
        """
        Genera el Kardex de un producto.

        Args:
            producto_id: ID del producto
            almacen_id: ID del almacén (opcional)
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
            empresa: Empresa para filtrar (opcional)

        Returns:
            dict con:
            - saldo_inicial: Cantidad y valor al inicio del período
            - movimientos: Lista de movimientos con saldo acumulado
            - saldo_final: Cantidad y valor al final del período
        """
        from django.db.models import Sum, Q
        from decimal import Decimal

        # Construir filtros base
        filtros = Q(producto_id=producto_id)
        if almacen_id:
            filtros &= Q(almacen_id=almacen_id)
        if empresa:
            filtros &= Q(empresa=empresa)

        # Calcular saldo inicial (movimientos antes de fecha_desde)
        saldo_inicial = {'cantidad': Decimal('0'), 'valor': Decimal('0')}
        if fecha_desde:
            movimientos_anteriores = MovimientoInventario.objects.filter(
                filtros,
                fecha__lt=fecha_desde
            ).aggregate(
                total_entradas=Sum('cantidad', filter=Q(cantidad__gt=0)),
                total_salidas=Sum('cantidad', filter=Q(cantidad__lt=0))
            )
            entradas = movimientos_anteriores['total_entradas'] or Decimal('0')
            salidas = abs(movimientos_anteriores['total_salidas'] or Decimal('0'))
            saldo_inicial['cantidad'] = entradas - salidas

        # Obtener movimientos del período
        filtros_periodo = filtros
        if fecha_desde:
            filtros_periodo &= Q(fecha__gte=fecha_desde)
        if fecha_hasta:
            filtros_periodo &= Q(fecha__lte=fecha_hasta)

        movimientos = MovimientoInventario.objects.filter(
            filtros_periodo
        ).select_related(
            'producto', 'almacen', 'usuario_creacion'
        ).order_by('fecha', 'id')

        # Calcular saldo acumulado para cada movimiento
        saldo_acumulado = saldo_inicial['cantidad']
        resultado_movimientos = []

        for mov in movimientos:
            if mov.cantidad > 0:
                entrada = mov.cantidad
                salida = Decimal('0')
            else:
                entrada = Decimal('0')
                salida = abs(mov.cantidad)

            saldo_acumulado += mov.cantidad

            resultado_movimientos.append({
                'id': mov.id,
                'fecha': mov.fecha,
                'tipo': mov.tipo_movimiento,
                'referencia': mov.referencia,
                'entrada': entrada,
                'salida': salida,
                'costo_unitario': mov.costo_unitario,
                'saldo': saldo_acumulado,
                'valor_movimiento': abs(mov.cantidad) * (mov.costo_unitario or Decimal('0')),
                'usuario': mov.usuario_creacion.username if mov.usuario_creacion else None,
                'notas': mov.notas
            })

        return {
            'producto_id': producto_id,
            'almacen_id': almacen_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'saldo_inicial': saldo_inicial,
            'movimientos': resultado_movimientos,
            'saldo_final': {
                'cantidad': saldo_acumulado,
                'total_movimientos': len(resultado_movimientos)
            }
        }

    @staticmethod
    def obtener_resumen_rotacion(producto_id, almacen_id=None, dias=30, empresa=None):
        """
        Calcula la rotación de inventario de un producto.

        Args:
            producto_id: ID del producto
            almacen_id: ID del almacén (opcional)
            dias: Período en días para calcular
            empresa: Empresa para filtrar

        Returns:
            dict con índice de rotación y días de inventario
        """
        from django.db.models import Sum, Q, Avg
        from datetime import timedelta

        fecha_desde = timezone.now().date() - timedelta(days=dias)

        # Filtros
        filtros = Q(producto_id=producto_id, fecha__gte=fecha_desde)
        if almacen_id:
            filtros &= Q(almacen_id=almacen_id)
        if empresa:
            filtros &= Q(empresa=empresa)

        # Ventas/salidas del período
        salidas = MovimientoInventario.objects.filter(
            filtros,
            tipo_movimiento__in=['SALIDA_VENTA', 'SALIDA_AJUSTE']
        ).aggregate(
            total=Sum('cantidad')
        )
        total_salidas = abs(salidas['total'] or 0)

        # Inventario promedio
        inventario_actual = InventarioProducto.objects.filter(
            producto_id=producto_id
        )
        if almacen_id:
            inventario_actual = inventario_actual.filter(almacen_id=almacen_id)
        if empresa:
            inventario_actual = inventario_actual.filter(empresa=empresa)

        inv_promedio = inventario_actual.aggregate(
            promedio=Avg('cantidad_disponible')
        )['promedio'] or 1

        # Calcular rotación
        rotacion = float(total_salidas) / float(inv_promedio) if inv_promedio > 0 else 0
        dias_inventario = dias / rotacion if rotacion > 0 else 0

        return {
            'producto_id': producto_id,
            'periodo_dias': dias,
            'total_salidas': total_salidas,
            'inventario_promedio': float(inv_promedio),
            'indice_rotacion': round(rotacion, 2),
            'dias_inventario': round(dias_inventario, 1)
        }


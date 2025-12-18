from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    Almacen, InventarioProducto, MovimientoInventario,
    ReservaStock, Lote, AlertaInventario,
    TransferenciaInventario, DetalleTransferencia,
    AjusteInventario, DetalleAjusteInventario,
    ConteoFisico, DetalleConteoFisico
)

# ========== SERIALIZERS BÁSICOS ==========

class AlmacenSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = Almacen
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate(self, data):
        """Validar nombre único por empresa"""
        nombre = data.get('nombre')
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        
        if nombre and empresa:
            queryset = Almacen.objects.filter(empresa=empresa, nombre=nombre)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    "nombre": f"Ya existe un almacén con este nombre en la empresa {empresa.nombre}."
                })
        return data

class InventarioProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    # Propiedades calculadas
    esta_bajo_minimo = serializers.ReadOnlyField()
    necesita_reorden = serializers.ReadOnlyField()
    stock_reservado = serializers.ReadOnlyField()
    stock_disponible_real = serializers.ReadOnlyField()
    valor_inventario = serializers.ReadOnlyField()
    
    class Meta:
        model = InventarioProducto
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate(self, data):
        """Validar que producto y almacen pertenezcan a la misma empresa"""
        producto = data.get('producto') or (self.instance.producto if self.instance else None)
        almacen = data.get('almacen') or (self.instance.almacen if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        
        if producto and almacen and empresa:
            # Verificar que el producto pertenezca a la empresa
            if hasattr(producto, 'empresa') and producto.empresa != empresa:
                raise serializers.ValidationError({
                    "producto": "El producto no pertenece a la empresa especificada."
                })
            
            # Verificar que el almacén pertenezca a la empresa
            if almacen.empresa != empresa:
                raise serializers.ValidationError({
                    "almacen": "El almacén no pertenece a la empresa especificada."
                })
        
        return data

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')

    class Meta:
        model = MovimientoInventario
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha', 'fecha_actualizacion', 'usuario', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate_cantidad(self, value):
        """Validar que la cantidad sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
        return value
    
    def validate(self, data):
        """Validar stock suficiente para salidas"""
        tipo_movimiento = data.get('tipo_movimiento') or (self.instance.tipo_movimiento if self.instance else None)
        cantidad = data.get('cantidad')
        producto = data.get('producto') or (self.instance.producto if self.instance else None)
        almacen = data.get('almacen') or (self.instance.almacen if self.instance else None)
        
        if tipo_movimiento in ['SALIDA_VENTA', 'SALIDA_AJUSTE', 'TRANSFERENCIA_SALIDA'] and cantidad and producto and almacen:
            try:
                inventario = InventarioProducto.objects.get(producto=producto, almacen=almacen)
                if not inventario.tiene_stock_suficiente(cantidad):
                    raise serializers.ValidationError({
                        "cantidad": f"Stock insuficiente. Disponible: {inventario.stock_disponible_real}, Solicitado: {cantidad}"
                    })
            except InventarioProducto.DoesNotExist:
                raise serializers.ValidationError({
                    "producto": "No existe inventario para este producto en este almacén."
                })
        
        return data

# ========== SERIALIZERS DE RESERVAS ==========

class ReservaStockSerializer(serializers.ModelSerializer):
    inventario_producto = serializers.ReadOnlyField(source='inventario.producto.nombre')
    inventario_almacen = serializers.ReadOnlyField(source='inventario.almacen.nombre')
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = ReservaStock
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_reserva', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate_cantidad_reservada(self, value):
        """Validar que la cantidad reservada sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad reservada debe ser mayor a cero.")
        return value
    
    def validate(self, data):
        """Validar stock disponible"""
        inventario = data.get('inventario') or (self.instance.inventario if self.instance else None)
        cantidad_reservada = data.get('cantidad_reservada')
        
        if inventario and cantidad_reservada:
            if not inventario.tiene_stock_suficiente(cantidad_reservada):
                raise serializers.ValidationError({
                    "cantidad_reservada": f"Stock insuficiente. Disponible: {inventario.stock_disponible_real}, Solicitado: {cantidad_reservada}"
                })
        
        return data

# ========== SERIALIZERS DE LOTES ==========

class LoteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre', allow_null=True)
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    esta_vencido = serializers.ReadOnlyField()
    dias_para_vencer = serializers.ReadOnlyField()
    
    class Meta:
        model = Lote
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_ingreso', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate_codigo_lote(self, value):
        """Validar código de lote único por empresa"""
        if value:
            empresa = self.initial_data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = Lote.objects.filter(empresa=empresa, codigo_lote=value)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError(f"Ya existe un lote con este código en la empresa {empresa.nombre}.")
        return value
    
    def validate_cantidad_inicial(self, value):
        """Validar que la cantidad inicial sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad inicial debe ser mayor a cero.")
        return value
    
    def validate(self, data):
        """Validar que cantidad_disponible no exceda cantidad_inicial"""
        cantidad_inicial = data.get('cantidad_inicial') or (self.instance.cantidad_inicial if self.instance else None)
        cantidad_disponible = data.get('cantidad_disponible') or (self.instance.cantidad_disponible if self.instance else None)
        
        if cantidad_inicial and cantidad_disponible:
            if cantidad_disponible > cantidad_inicial:
                raise serializers.ValidationError({
                    "cantidad_disponible": "La cantidad disponible no puede exceder la cantidad inicial."
                })
        
        return data

# ========== SERIALIZERS DE ALERTAS ==========

class AlertaInventarioSerializer(serializers.ModelSerializer):
    inventario_producto = serializers.ReadOnlyField(source='inventario.producto.nombre', allow_null=True)
    inventario_almacen = serializers.ReadOnlyField(source='inventario.almacen.nombre', allow_null=True)
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)
    lote_producto = serializers.ReadOnlyField(source='lote.producto.nombre', allow_null=True)
    usuario_resolucion_nombre = serializers.ReadOnlyField(source='usuario_resolucion.username', allow_null=True)
    tipo_display = serializers.ReadOnlyField(source='get_tipo_display')
    prioridad_display = serializers.ReadOnlyField(source='get_prioridad_display')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = AlertaInventario
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_alerta', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate(self, data):
        """Validar que al menos inventario o lote esté presente"""
        inventario = data.get('inventario') or (self.instance.inventario if self.instance else None)
        lote = data.get('lote') or (self.instance.lote if self.instance else None)
        
        if not inventario and not lote:
            raise serializers.ValidationError({
                "inventario": "Debe especificar al menos un inventario o un lote.",
                "lote": "Debe especificar al menos un inventario o un lote."
            })
        
        return data

# ========== SERIALIZERS DE TRANSFERENCIAS ==========

class DetalleTransferenciaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)
    
    class Meta:
        model = DetalleTransferencia
        fields = '__all__'
        read_only_fields = ('id',)

class TransferenciaInventarioSerializer(serializers.ModelSerializer):
    almacen_origen_nombre = serializers.ReadOnlyField(source='almacen_origen.nombre')
    almacen_destino_nombre = serializers.ReadOnlyField(source='almacen_destino.nombre')
    usuario_solicitante_nombre = serializers.ReadOnlyField(source='usuario_solicitante.username')
    usuario_receptor_nombre = serializers.ReadOnlyField(source='usuario_receptor.username', allow_null=True)
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleTransferenciaSerializer(many=True, read_only=True)
    
    class Meta:
        model = TransferenciaInventario
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_solicitud', 'fecha_creacion', 'fecha_actualizacion', 'usuario_solicitante', 'usuario_receptor', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate_numero_transferencia(self, value):
        """Validar número de transferencia único por empresa"""
        if value:
            empresa = self.initial_data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = TransferenciaInventario.objects.filter(empresa=empresa, numero_transferencia=value)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError(f"Ya existe una transferencia con este número en la empresa {empresa.nombre}.")
        return value
    
    def validate(self, data):
        """Validar que almacenes pertenezcan a la misma empresa"""
        almacen_origen = data.get('almacen_origen') or (self.instance.almacen_origen if self.instance else None)
        almacen_destino = data.get('almacen_destino') or (self.instance.almacen_destino if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        
        if almacen_origen and almacen_destino:
            if almacen_origen == almacen_destino:
                raise serializers.ValidationError({
                    "almacen_destino": "El almacén destino debe ser diferente del almacén origen."
                })
            
            if empresa:
                if almacen_origen.empresa != empresa:
                    raise serializers.ValidationError({
                        "almacen_origen": "El almacén origen no pertenece a la empresa especificada."
                    })
                if almacen_destino.empresa != empresa:
                    raise serializers.ValidationError({
                        "almacen_destino": "El almacén destino no pertenece a la empresa especificada."
                    })
        
        return data

# ========== SERIALIZERS DE AJUSTES ==========

class DetalleAjusteInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)
    
    class Meta:
        model = DetalleAjusteInventario
        fields = '__all__'
        read_only_fields = ('id', 'diferencia')

class AjusteInventarioSerializer(serializers.ModelSerializer):
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    usuario_solicitante_nombre = serializers.ReadOnlyField(source='usuario_solicitante.username')
    usuario_aprobador_nombre = serializers.ReadOnlyField(source='usuario_aprobador.username', allow_null=True)
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    tipo_ajuste_display = serializers.ReadOnlyField(source='get_tipo_ajuste_display')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleAjusteInventarioSerializer(many=True, read_only=True)
    
    class Meta:
        model = AjusteInventario
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_aprobacion', 'fecha_creacion', 'fecha_actualizacion', 'usuario_solicitante', 'usuario_aprobador', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate(self, data):
        """Validaciones de negocio"""
        almacen = data.get('almacen') or (self.instance.almacen if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        
        if almacen and empresa:
            if almacen.empresa != empresa:
                raise serializers.ValidationError({
                    "almacen": "El almacén no pertenece a la empresa especificada."
                })
        
        return data

# ========== SERIALIZERS DE CONTEO FÍSICO ==========

class DetalleConteoFisicoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_codigo_sku = serializers.ReadOnlyField(source='producto.codigo_sku')
    lote_codigo = serializers.ReadOnlyField(source='lote.codigo_lote', allow_null=True)
    contado_por_nombre = serializers.ReadOnlyField(source='contado_por.username', allow_null=True)
    
    class Meta:
        model = DetalleConteoFisico
        fields = '__all__'
        read_only_fields = ('id', 'diferencia')

class ConteoFisicoSerializer(serializers.ModelSerializer):
    almacen_nombre = serializers.ReadOnlyField(source='almacen.nombre')
    usuario_responsable_nombre = serializers.ReadOnlyField(source='usuario_responsable.username')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')
    tipo_conteo_display = serializers.ReadOnlyField(source='get_tipo_conteo_display')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    detalles = DetalleConteoFisicoSerializer(many=True, read_only=True)
    
    class Meta:
        model = ConteoFisico
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_inicio', 'fecha_fin', 'fecha_creacion', 'fecha_actualizacion', 'usuario_responsable', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def validate_numero_conteo(self, value):
        """Validar número de conteo único por empresa"""
        if value:
            empresa = self.initial_data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = ConteoFisico.objects.filter(empresa=empresa, numero_conteo=value)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError(f"Ya existe un conteo con este número en la empresa {empresa.nombre}.")
        return value
    
    def validate(self, data):
        """Validar que almacén pertenezca a la empresa"""
        almacen = data.get('almacen') or (self.instance.almacen if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
        
        if almacen and empresa:
            if almacen.empresa != empresa:
                raise serializers.ValidationError({
                    "almacen": "El almacén no pertenece a la empresa especificada."
                })
        
        return data

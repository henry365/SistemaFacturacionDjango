"""
Constantes para el módulo Inventario

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""

# =============================================================================
# TIPOS DE MOVIMIENTO
# =============================================================================

TIPO_ENTRADA_COMPRA = 'ENTRADA_COMPRA'
TIPO_ENTRADA_AJUSTE = 'ENTRADA_AJUSTE'
TIPO_TRANSFERENCIA_ENTRADA = 'TRANSFERENCIA_ENTRADA'
TIPO_DEVOLUCION_CLIENTE = 'DEVOLUCION_CLIENTE'

TIPO_SALIDA_VENTA = 'SALIDA_VENTA'
TIPO_SALIDA_AJUSTE = 'SALIDA_AJUSTE'
TIPO_TRANSFERENCIA_SALIDA = 'TRANSFERENCIA_SALIDA'
TIPO_DEVOLUCION_PROVEEDOR = 'DEVOLUCION_PROVEEDOR'

TIPOS_MOVIMIENTO_ENTRADA = [
    TIPO_ENTRADA_COMPRA,
    TIPO_ENTRADA_AJUSTE,
    TIPO_TRANSFERENCIA_ENTRADA,
    TIPO_DEVOLUCION_CLIENTE,
]

TIPOS_MOVIMIENTO_SALIDA = [
    TIPO_SALIDA_VENTA,
    TIPO_SALIDA_AJUSTE,
    TIPO_TRANSFERENCIA_SALIDA,
    TIPO_DEVOLUCION_PROVEEDOR,
]

# =============================================================================
# ESTADOS DE RESERVA
# =============================================================================

ESTADO_RESERVA_PENDIENTE = 'PENDIENTE'
ESTADO_RESERVA_CONFIRMADA = 'CONFIRMADA'
ESTADO_RESERVA_CANCELADA = 'CANCELADA'
ESTADO_RESERVA_VENCIDA = 'VENCIDA'

ESTADOS_RESERVA_ACTIVOS = [ESTADO_RESERVA_PENDIENTE, ESTADO_RESERVA_CONFIRMADA]

# =============================================================================
# ESTADOS DE TRANSFERENCIA
# =============================================================================

ESTADO_TRANSFERENCIA_PENDIENTE = 'PENDIENTE'
ESTADO_TRANSFERENCIA_EN_TRANSITO = 'EN_TRANSITO'
ESTADO_TRANSFERENCIA_RECIBIDA = 'RECIBIDA'
ESTADO_TRANSFERENCIA_RECIBIDA_PARCIAL = 'RECIBIDA_PARCIAL'
ESTADO_TRANSFERENCIA_CANCELADA = 'CANCELADA'

# =============================================================================
# ESTADOS DE AJUSTE
# =============================================================================

ESTADO_AJUSTE_PENDIENTE = 'PENDIENTE'
ESTADO_AJUSTE_APROBADO = 'APROBADO'
ESTADO_AJUSTE_RECHAZADO = 'RECHAZADO'
ESTADO_AJUSTE_PROCESADO = 'PROCESADO'

# =============================================================================
# ESTADOS DE CONTEO
# =============================================================================

ESTADO_CONTEO_PLANIFICADO = 'PLANIFICADO'
ESTADO_CONTEO_EN_PROCESO = 'EN_PROCESO'
ESTADO_CONTEO_FINALIZADO = 'FINALIZADO'
ESTADO_CONTEO_AJUSTADO = 'AJUSTADO'
ESTADO_CONTEO_CANCELADO = 'CANCELADO'

# =============================================================================
# ESTADOS DE LOTE
# =============================================================================

ESTADO_LOTE_ACTIVO = 'ACTIVO'
ESTADO_LOTE_AGOTADO = 'AGOTADO'
ESTADO_LOTE_VENCIDO = 'VENCIDO'
ESTADO_LOTE_RETIRADO = 'RETIRADO'

# =============================================================================
# MÉTODOS DE VALORACIÓN
# =============================================================================

METODO_PROMEDIO = 'PROMEDIO'
METODO_PEPS = 'PEPS'
METODO_UEPS = 'UEPS'
METODO_PRECIO_ESPECIFICO = 'PRECIO_ESPECIFICO'

# =============================================================================
# TIPOS DE ALERTA
# =============================================================================

TIPO_ALERTA_STOCK_MINIMO = 'STOCK_MINIMO'
TIPO_ALERTA_STOCK_MAXIMO = 'STOCK_MAXIMO'
TIPO_ALERTA_VENCIMIENTO = 'VENCIMIENTO'
TIPO_ALERTA_REORDEN = 'REORDEN'

# =============================================================================
# PRIORIDADES DE ALERTA
# =============================================================================

PRIORIDAD_BAJA = 'BAJA'
PRIORIDAD_MEDIA = 'MEDIA'
PRIORIDAD_ALTA = 'ALTA'
PRIORIDAD_CRITICA = 'CRITICA'

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# =============================================================================
# CONFIGURACIÓN DE ALERTAS
# =============================================================================

DIAS_ANTES_VENCIMIENTO_ALERTA = 30
DIAS_CRITICO_VENCIMIENTO = 7
DIAS_ALTA_PRIORIDAD_VENCIMIENTO = 15

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío'
ERROR_NOMBRE_REQUERIDO = 'El nombre es requerido'
ERROR_NOMBRE_DUPLICADO_EMPRESA = 'Ya existe un almacén con este nombre en esta empresa'

ERROR_CANTIDAD_NEGATIVA = 'La cantidad no puede ser negativa'
ERROR_CANTIDAD_CERO = 'La cantidad debe ser mayor a cero'
ERROR_COSTO_NEGATIVO = 'El costo no puede ser negativo'

ERROR_STOCK_INSUFICIENTE = 'Stock insuficiente. Disponible: {disponible}, Solicitado: {solicitado}'
ERROR_STOCK_MINIMO_MAYOR_MAXIMO = 'El stock mínimo no puede ser mayor al stock máximo'
ERROR_PUNTO_REORDEN_MENOR_MINIMO = 'El punto de reorden no puede ser menor al stock mínimo'
ERROR_PUNTO_REORDEN_MAYOR_MAXIMO = 'El punto de reorden no puede ser mayor al stock máximo'

ERROR_PRODUCTO_NO_PERTENECE_EMPRESA = 'El producto no pertenece a la empresa especificada'
ERROR_ALMACEN_NO_PERTENECE_EMPRESA = 'El almacén no pertenece a la empresa especificada'
ERROR_LOTE_NO_PERTENECE_EMPRESA = 'El lote no pertenece a la empresa especificada'
ERROR_LOTE_NO_CORRESPONDE_PRODUCTO = 'El lote no corresponde al producto especificado'

ERROR_TRANSFERENCIA_SOLO_PENDIENTES = 'Solo se pueden enviar transferencias pendientes'
ERROR_TRANSFERENCIA_SOLO_EN_TRANSITO = 'Solo se pueden recibir transferencias en tránsito'
ERROR_AJUSTE_SOLO_PENDIENTES = 'Solo se pueden aprobar/rechazar ajustes pendientes'
ERROR_AJUSTE_SOLO_APROBADOS = 'Solo se pueden procesar ajustes aprobados'
ERROR_CONTEO_SOLO_PLANIFICADOS = 'Solo se pueden iniciar conteos planificados'
ERROR_CONTEO_SOLO_EN_PROCESO = 'Solo se pueden finalizar conteos en proceso'
ERROR_CONTEO_SOLO_FINALIZADOS = 'Solo se pueden ajustar conteos finalizados'

ERROR_KARDEX_PARAMETROS_REQUERIDOS = 'Los parámetros producto_id y almacen_id son requeridos'

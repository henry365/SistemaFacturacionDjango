"""
Constantes para el módulo de Despachos

Centraliza estados, transiciones y mensajes de error para mantener consistencia
y cumplir con el principio DRY.
"""

# =============================================================================
# ESTADOS DE DESPACHO
# =============================================================================

ESTADO_PENDIENTE = 'PENDIENTE'
ESTADO_EN_PREPARACION = 'EN_PREPARACION'
ESTADO_PARCIAL = 'PARCIAL'
ESTADO_COMPLETADO = 'COMPLETADO'
ESTADO_CANCELADO = 'CANCELADO'

ESTADO_CHOICES = (
    (ESTADO_PENDIENTE, 'Pendiente'),
    (ESTADO_EN_PREPARACION, 'En Preparación'),
    (ESTADO_PARCIAL, 'Parcial'),
    (ESTADO_COMPLETADO, 'Completado'),
    (ESTADO_CANCELADO, 'Cancelado'),
)

# Estados terminales (no se pueden modificar)
ESTADOS_TERMINALES = [ESTADO_COMPLETADO, ESTADO_CANCELADO]

# Estados que permiten despachar
ESTADOS_DESPACHABLES = [ESTADO_PENDIENTE, ESTADO_EN_PREPARACION, ESTADO_PARCIAL]

# Estados que permiten cancelar
ESTADOS_CANCELABLES = [ESTADO_PENDIENTE, ESTADO_EN_PREPARACION, ESTADO_PARCIAL]

# =============================================================================
# TRANSICIONES DE ESTADO
# =============================================================================

TRANSICIONES_ESTADO = {
    # PENDIENTE puede ir a preparación, parcial, completado (despacho directo) o cancelado
    ESTADO_PENDIENTE: [ESTADO_EN_PREPARACION, ESTADO_PARCIAL, ESTADO_COMPLETADO, ESTADO_CANCELADO],
    ESTADO_EN_PREPARACION: [ESTADO_PARCIAL, ESTADO_COMPLETADO, ESTADO_CANCELADO],
    ESTADO_PARCIAL: [ESTADO_PARCIAL, ESTADO_COMPLETADO, ESTADO_CANCELADO],
    ESTADO_COMPLETADO: [],  # Estado final
    ESTADO_CANCELADO: [],  # Estado final
}

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

# Validaciones de modelo
ERROR_FACTURA_EMPRESA = 'La factura debe pertenecer a la misma empresa'
ERROR_CLIENTE_EMPRESA = 'El cliente debe pertenecer a la misma empresa'
ERROR_ALMACEN_EMPRESA = 'El almacén debe pertenecer a la misma empresa'
ERROR_CLIENTE_FACTURA = 'El cliente debe coincidir con el cliente de la factura'
ERROR_FECHA_DESPACHO_FUTURA = 'La fecha de despacho no puede ser futura'
ERROR_FECHA_DESPACHO_ANTERIOR = 'La fecha de despacho no puede ser anterior a la fecha de creación'
ERROR_TRANSICION_INVALIDA = 'No se puede cambiar de {estado_actual} a {estado_nuevo}'

# Validaciones de detalle
ERROR_CANTIDAD_SOLICITADA_POSITIVA = 'La cantidad solicitada debe ser mayor a cero'
ERROR_CANTIDAD_DESPACHADA_NEGATIVA = 'La cantidad despachada no puede ser negativa'
ERROR_CANTIDAD_EXCEDE_SOLICITADA = 'La cantidad despachada no puede ser mayor a la cantidad solicitada'
ERROR_PRODUCTO_EMPRESA = 'El producto debe pertenecer a la misma empresa del despacho'
ERROR_LOTE_ALMACEN = 'El lote debe pertenecer al almacén del despacho'

# Validaciones de serializer
ERROR_FACTURA_OTRA_EMPRESA = 'La factura debe pertenecer a su empresa'
ERROR_CLIENTE_OTRA_EMPRESA = 'El cliente debe pertenecer a su empresa'
ERROR_ALMACEN_OTRA_EMPRESA = 'El almacén debe pertenecer a su empresa'

# Errores de acciones
ERROR_SOLO_PENDIENTES_PREPARAR = 'Solo se pueden preparar despachos pendientes'
ERROR_ESTADO_NO_PERMITE_DESPACHAR = 'No se puede despachar en este estado'
ERROR_YA_COMPLETADO = 'El despacho ya está completado'
ERROR_NO_COMPLETAR_CANCELADO = 'No se puede completar un despacho cancelado'
ERROR_NO_CANCELAR_COMPLETADO = 'No se puede cancelar un despacho completado'
ERROR_YA_CANCELADO = 'El despacho ya está cancelado'
ERROR_STOCK_INSUFICIENTE = 'Stock insuficiente para producto {producto}'
ERROR_DESPACHO_FALLIDO = 'Error al procesar el despacho'

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DESPACHOS = 20
PAGE_SIZE_MAX = 100

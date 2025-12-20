"""
Constantes del módulo Cuentas por Pagar

Este módulo centraliza todas las constantes utilizadas en el módulo de cuentas por pagar,
siguiendo el principio DRY y facilitando el mantenimiento.
"""

# ============================================================
# ESTADOS DE CUENTA POR PAGAR
# ============================================================

ESTADO_CXP_PENDIENTE = 'PENDIENTE'
ESTADO_CXP_PARCIAL = 'PARCIAL'
ESTADO_CXP_PAGADA = 'PAGADA'
ESTADO_CXP_VENCIDA = 'VENCIDA'
ESTADO_CXP_ANULADA = 'ANULADA'

ESTADO_CXP_CHOICES = (
    (ESTADO_CXP_PENDIENTE, 'Pendiente'),
    (ESTADO_CXP_PARCIAL, 'Pago Parcial'),
    (ESTADO_CXP_PAGADA, 'Pagada'),
    (ESTADO_CXP_VENCIDA, 'Vencida'),
    (ESTADO_CXP_ANULADA, 'Anulada'),
)

# Estados que permiten pagos
ESTADOS_CXP_PAGABLES = [
    ESTADO_CXP_PENDIENTE,
    ESTADO_CXP_PARCIAL,
    ESTADO_CXP_VENCIDA,
]

# Estados terminales (no modificables)
ESTADOS_CXP_TERMINALES = [
    ESTADO_CXP_PAGADA,
    ESTADO_CXP_ANULADA,
]

# Transiciones válidas de estado
TRANSICIONES_ESTADO_CXP = {
    ESTADO_CXP_PENDIENTE: [ESTADO_CXP_PARCIAL, ESTADO_CXP_PAGADA, ESTADO_CXP_VENCIDA, ESTADO_CXP_ANULADA],
    ESTADO_CXP_PARCIAL: [ESTADO_CXP_PAGADA, ESTADO_CXP_VENCIDA, ESTADO_CXP_ANULADA],
    ESTADO_CXP_VENCIDA: [ESTADO_CXP_PARCIAL, ESTADO_CXP_PAGADA, ESTADO_CXP_ANULADA],
    ESTADO_CXP_PAGADA: [],  # Estado terminal
    ESTADO_CXP_ANULADA: [],  # Estado terminal
}


# ============================================================
# METODOS DE PAGO
# ============================================================

METODO_PAGO_EFECTIVO = 'EFECTIVO'
METODO_PAGO_TRANSFERENCIA = 'TRANSFERENCIA'
METODO_PAGO_CHEQUE = 'CHEQUE'
METODO_PAGO_TARJETA = 'TARJETA'
METODO_PAGO_OTRO = 'OTRO'

METODO_PAGO_CHOICES = (
    (METODO_PAGO_EFECTIVO, 'Efectivo'),
    (METODO_PAGO_TRANSFERENCIA, 'Transferencia Bancaria'),
    (METODO_PAGO_CHEQUE, 'Cheque'),
    (METODO_PAGO_TARJETA, 'Tarjeta'),
    (METODO_PAGO_OTRO, 'Otro'),
)

# Métodos que requieren referencia obligatoria
METODOS_REQUIEREN_REFERENCIA = [
    METODO_PAGO_TRANSFERENCIA,
    METODO_PAGO_CHEQUE,
]


# ============================================================
# MENSAJES DE ERROR
# ============================================================

ERROR_PROVEEDOR_EMPRESA = 'El proveedor debe pertenecer a la misma empresa.'
ERROR_COMPRA_EMPRESA = 'La compra debe pertenecer a la misma empresa.'
ERROR_MONTO_NEGATIVO = 'El monto no puede ser negativo.'
ERROR_MONTO_PENDIENTE_NEGATIVO = 'El monto pendiente no puede ser negativo.'
ERROR_MONTO_MAYOR_CERO = 'El monto debe ser mayor a cero.'
ERROR_MONTO_APLICADO_MAYOR_CERO = 'El monto aplicado debe ser mayor a cero.'
ERROR_MONTO_EXCEDE_PENDIENTE = 'El monto aplicado no puede exceder el saldo pendiente.'
ERROR_CXP_NO_PAGABLE = 'La cuenta por pagar no está en estado pagable.'
ERROR_PAGO_EMPRESA = 'El pago debe pertenecer a la misma empresa que la cuenta por pagar.'
ERROR_TOTAL_EXCEDE_PAGO = 'El total aplicado excede el monto del pago.'
ERROR_REFERENCIA_REQUERIDA = 'La referencia es requerida para este método de pago.'
ERROR_FECHA_VENCIMIENTO_PASADA = 'La fecha de vencimiento no puede ser anterior a la fecha del documento.'
ERROR_MONTO_PAGADO_EXCEDE = 'El monto pagado no puede exceder el monto original.'


# ============================================================
# CONFIGURACION DE PAGINACION
# ============================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

"""
Constantes del módulo Cuentas por Cobrar

Este módulo centraliza todas las constantes utilizadas en el módulo de cuentas por cobrar,
siguiendo el principio DRY y facilitando el mantenimiento.
"""

# ============================================================
# ESTADOS DE CUENTA POR COBRAR
# ============================================================

ESTADO_CXC_PENDIENTE = 'PENDIENTE'
ESTADO_CXC_PARCIAL = 'PARCIAL'
ESTADO_CXC_COBRADA = 'COBRADA'
ESTADO_CXC_VENCIDA = 'VENCIDA'
ESTADO_CXC_ANULADA = 'ANULADA'

ESTADO_CXC_CHOICES = (
    (ESTADO_CXC_PENDIENTE, 'Pendiente'),
    (ESTADO_CXC_PARCIAL, 'Cobro Parcial'),
    (ESTADO_CXC_COBRADA, 'Cobrada'),
    (ESTADO_CXC_VENCIDA, 'Vencida'),
    (ESTADO_CXC_ANULADA, 'Anulada'),
)

# Estados que permiten cobros
ESTADOS_CXC_COBRABLES = [
    ESTADO_CXC_PENDIENTE,
    ESTADO_CXC_PARCIAL,
    ESTADO_CXC_VENCIDA,
]

# Estados terminales (no modificables)
ESTADOS_CXC_TERMINALES = [
    ESTADO_CXC_COBRADA,
    ESTADO_CXC_ANULADA,
]

# Transiciones válidas de estado
TRANSICIONES_ESTADO_CXC = {
    ESTADO_CXC_PENDIENTE: [ESTADO_CXC_PARCIAL, ESTADO_CXC_COBRADA, ESTADO_CXC_VENCIDA, ESTADO_CXC_ANULADA],
    ESTADO_CXC_PARCIAL: [ESTADO_CXC_COBRADA, ESTADO_CXC_VENCIDA, ESTADO_CXC_ANULADA],
    ESTADO_CXC_VENCIDA: [ESTADO_CXC_PARCIAL, ESTADO_CXC_COBRADA, ESTADO_CXC_ANULADA],
    ESTADO_CXC_COBRADA: [],  # Estado terminal
    ESTADO_CXC_ANULADA: [],  # Estado terminal
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

ERROR_CLIENTE_EMPRESA = 'El cliente debe pertenecer a la misma empresa.'
ERROR_MONTO_NEGATIVO = 'El monto no puede ser negativo.'
ERROR_MONTO_PENDIENTE_NEGATIVO = 'El monto pendiente no puede ser negativo.'
ERROR_MONTO_MAYOR_CERO = 'El monto debe ser mayor a cero.'
ERROR_MONTO_APLICADO_MAYOR_CERO = 'El monto aplicado debe ser mayor a cero.'
ERROR_MONTO_EXCEDE_PENDIENTE = 'El monto aplicado no puede exceder el saldo pendiente.'
ERROR_CXC_NO_COBRABLE = 'La cuenta por cobrar no está en estado cobrable.'
ERROR_COBRO_EMPRESA = 'El cobro debe pertenecer a la misma empresa que la cuenta por cobrar.'
ERROR_TOTAL_EXCEDE_COBRO = 'El total aplicado excede el monto del cobro.'
ERROR_REFERENCIA_REQUERIDA = 'La referencia es requerida para este método de pago.'
ERROR_FECHA_VENCIMIENTO_PASADA = 'La fecha de vencimiento no puede ser anterior a la fecha del documento.'
ERROR_FACTURA_EMPRESA = 'La factura debe pertenecer a la misma empresa.'
ERROR_MONTO_COBRADO_EXCEDE = 'El monto cobrado no puede exceder el monto original.'
ERROR_FECHA_FUTURA = 'La fecha no puede ser futura.'


# ============================================================
# CONFIGURACION DE PAGINACION
# ============================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

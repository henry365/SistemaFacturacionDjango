"""
Constantes para el módulo Caja

Este módulo centraliza todas las constantes utilizadas en el módulo de caja,
siguiendo el principio DRY (Don't Repeat Yourself).
"""

# ============================================================
# ESTADOS DE SESION DE CAJA
# ============================================================

ESTADO_ABIERTA = 'ABIERTA'
ESTADO_CERRADA = 'CERRADA'
ESTADO_ARQUEADA = 'ARQUEADA'

ESTADO_CHOICES = (
    (ESTADO_ABIERTA, 'Abierta'),
    (ESTADO_CERRADA, 'Cerrada'),
    (ESTADO_ARQUEADA, 'Arqueada'),
)

ESTADO_DEFAULT = ESTADO_ABIERTA

# Transiciones de estado permitidas
TRANSICIONES_ESTADO = {
    ESTADO_ABIERTA: [ESTADO_CERRADA],
    ESTADO_CERRADA: [ESTADO_ARQUEADA],
    ESTADO_ARQUEADA: [],  # Estado final
}

# ============================================================
# TIPOS DE MOVIMIENTO DE CAJA
# ============================================================

TIPO_VENTA = 'VENTA'
TIPO_INGRESO_MANUAL = 'INGRESO_MANUAL'
TIPO_RETIRO_MANUAL = 'RETIRO_MANUAL'
TIPO_GASTO_MENOR = 'GASTO_MENOR'
TIPO_APERTURA = 'APERTURA'
TIPO_CIERRE = 'CIERRE'

TIPO_MOVIMIENTO_CHOICES = (
    (TIPO_VENTA, 'Venta (Cobro)'),
    (TIPO_INGRESO_MANUAL, 'Ingreso Manual'),
    (TIPO_RETIRO_MANUAL, 'Retiro Manual'),
    (TIPO_GASTO_MENOR, 'Gasto Menor'),
    (TIPO_APERTURA, 'Monto Apertura'),
    (TIPO_CIERRE, 'Retiro por Cierre'),
)

# Tipos de movimiento que representan INGRESOS
TIPOS_INGRESO = [TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_APERTURA]

# Tipos de movimiento que representan EGRESOS
TIPOS_EGRESO = [TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR, TIPO_CIERRE]

# Tipos de movimiento que NO se pueden eliminar
TIPOS_NO_ELIMINABLES = [TIPO_APERTURA]

# Tipos de movimiento que NO se pueden editar
TIPOS_NO_EDITABLES = [TIPO_APERTURA, TIPO_CIERRE]

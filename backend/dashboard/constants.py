"""
Constantes para el módulo Dashboard

Centraliza estados, límites y valores por defecto para mantener consistencia
y cumplir con el principio DRY.
"""
from decimal import Decimal

# =============================================================================
# LÍMITES DE QUERY PARAMS
# =============================================================================

DIAS_MAXIMO_DASHBOARD = 365
LIMITE_MAXIMO_PRODUCTOS = 100
LIMITE_MAXIMO_CLIENTES = 100
LIMITE_MAXIMO_ACTIVIDADES = 100
MESES_MAXIMO_DASHBOARD = 36

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

DIAS_DEFAULT_VENTAS = 30
MESES_DEFAULT_VENTAS = 12
LIMITE_DEFAULT_PRODUCTOS = 10
LIMITE_DEFAULT_CLIENTES = 10
LIMITE_DEFAULT_ACTIVIDADES = 20
LIMITE_DEFAULT_STOCK_BAJO = 20

# =============================================================================
# ESTADOS DE FACTURA
# =============================================================================

ESTADOS_FACTURA_VALIDOS = ['PAGADA', 'PAGADA_PARCIAL', 'PENDIENTE_PAGO']
ESTADOS_FACTURA_PAGADAS = ['PAGADA', 'PAGADA_PARCIAL']

# =============================================================================
# ESTADOS DE CUENTAS POR COBRAR
# =============================================================================

ESTADOS_CXC_ACTIVOS = ['PENDIENTE', 'PARCIAL', 'VENCIDA']

# =============================================================================
# ESTADOS DE CUENTAS POR PAGAR
# =============================================================================

ESTADOS_CXP_ACTIVOS = ['PENDIENTE', 'PARCIAL', 'VENCIDA']

# =============================================================================
# ESTADOS DE COMPRA
# =============================================================================

ESTADOS_COMPRA_VALIDOS = ['REGISTRADA', 'CXP', 'PAGADA']

# =============================================================================
# TIPOS DE MOVIMIENTO DE INVENTARIO
# =============================================================================

TIPOS_MOVIMIENTO_RELEVANTES = ['ENTRADA_COMPRA', 'SALIDA_VENTA', 'AJUSTE', 'TRANSFERENCIA']

# =============================================================================
# RANGOS DE VENCIMIENTO
# =============================================================================

RANGOS_VENCIMIENTO = [7, 15, 30]
RANGOS_ANTIGUEDAD = [(1, 30), (31, 60), (61, 90), (91, None)]

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_EMPRESA_NO_ASIGNADA = 'El usuario no tiene empresa asignada'
ERROR_DIAS_INVALIDO = 'dias debe estar entre 1 y {max}'
ERROR_MESES_INVALIDO = 'meses debe estar entre 1 y {max}'
ERROR_LIMITE_INVALIDO = 'limite debe estar entre 1 y {max}'
ERROR_RESUMEN_DASHBOARD = 'Error al obtener resumen del dashboard'
ERROR_VENTAS_PERIODO = 'Error al obtener ventas del período'
ERROR_TOP_PRODUCTOS = 'Error al obtener top productos'
ERROR_STOCK_BAJO = 'Error al obtener productos con stock bajo'
ERROR_TOP_CLIENTES = 'Error al obtener top clientes'
ERROR_CUENTAS_COBRAR = 'Error al obtener cuentas por cobrar'
ERROR_CUENTAS_PAGAR = 'Error al obtener cuentas por pagar'
ERROR_ACTIVIDAD_RECIENTE = 'Error al obtener actividad reciente'
ERROR_INDICADORES = 'Error al obtener indicadores financieros'

# =============================================================================
# VALORES DECIMALES POR DEFECTO
# =============================================================================

DECIMAL_CERO = Decimal('0.00')

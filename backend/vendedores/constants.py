"""
Constantes para el módulo Vendedores

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# =============================================================================
# ESTADOS DE FACTURA (para cálculos de comisiones)
# =============================================================================

ESTADO_FACTURA_PAGADA = 'PAGADA'
ESTADO_FACTURA_PAGADA_PARCIAL = 'PAGADA_PARCIAL'
ESTADO_FACTURA_ANULADA = 'ANULADA'
ESTADO_FACTURA_PENDIENTE = 'PENDIENTE'

ESTADOS_FACTURA_PARA_COMISION = [ESTADO_FACTURA_PAGADA, ESTADO_FACTURA_PAGADA_PARCIAL]

# =============================================================================
# ESTADOS DE COTIZACIÓN
# =============================================================================

ESTADO_COTIZACION_APROBADA = 'APROBADA'
ESTADO_COTIZACION_PENDIENTE = 'PENDIENTE'
ESTADO_COTIZACION_RECHAZADA = 'RECHAZADA'

# =============================================================================
# CONFIGURACIÓN DE COMISIONES
# =============================================================================

COMISION_MIN = 0.00
COMISION_MAX = 100.00
COMISION_DEFAULT = 0.00

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío.'
ERROR_CEDULA_DUPLICADA = 'Ya existe un vendedor con esta cédula en la empresa {empresa}.'
ERROR_COMISION_RANGO = 'La comisión debe estar entre 0 y 100.'
ERROR_TELEFONO_INVALIDO = 'El teléfono contiene caracteres inválidos.'
ERROR_TELEFONO_LONGITUD = 'El teléfono debe tener entre 10 y 15 dígitos.'
ERROR_EMAIL_INVALIDO = 'Formato de correo electrónico inválido.'
ERROR_USUARIO_EMPRESA_DIFERENTE = 'El usuario debe pertenecer a la misma empresa del vendedor.'
ERROR_CEDULA_FORMATO = 'El formato de cédula debe ser XXX-XXXXXXX-X.'

# =============================================================================
# REGEX PARA VALIDACIONES
# =============================================================================

REGEX_CEDULA = r'^[0-9]{3}-[0-9]{7}-[0-9]{1}$'
REGEX_TELEFONO = r'^[\d\s\-\(\)]+$'

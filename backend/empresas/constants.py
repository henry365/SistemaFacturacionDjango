"""
Constantes para el módulo Empresas

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""

# =============================================================================
# LONGITUDES PARA VALIDACIÓN
# =============================================================================

LONGITUD_RNC_MIN = 9
LONGITUD_RNC_MAX = 11
LONGITUD_TELEFONO_MIN = 10
LONGITUD_TELEFONO_MAX = 15

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

ACTIVO_DEFAULT = True
CONFIGURACION_FISCAL_DEFAULT = {}

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío'
ERROR_RNC_VACIO = 'El RNC no puede estar vacío'
ERROR_RNC_FORMATO = 'El RNC solo puede contener números y guiones'
ERROR_RNC_LONGITUD = f'El RNC debe tener entre {LONGITUD_RNC_MIN} y {LONGITUD_RNC_MAX} dígitos'
ERROR_RNC_DUPLICADO = 'Ya existe una empresa con este RNC'
ERROR_TELEFONO_FORMATO = 'El teléfono contiene caracteres inválidos'
ERROR_TELEFONO_LONGITUD = f'El teléfono debe tener entre {LONGITUD_TELEFONO_MIN} y {LONGITUD_TELEFONO_MAX} dígitos'
ERROR_CONFIGURACION_FISCAL_INVALIDA = 'La configuración fiscal debe ser un objeto JSON válido'
ERROR_CONFIGURACION_FISCAL_REQUERIDA = 'Se requiere el campo configuracion_fiscal'

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

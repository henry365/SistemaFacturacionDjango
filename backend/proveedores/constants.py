"""
Constantes para el módulo Proveedores

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""

# =============================================================================
# TIPOS DE IDENTIFICACIÓN
# =============================================================================

TIPO_IDENTIFICACION_RNC = 'RNC'
TIPO_IDENTIFICACION_CEDULA = 'CEDULA'
TIPO_IDENTIFICACION_PASAPORTE = 'PASAPORTE'
TIPO_IDENTIFICACION_OTRO = 'OTRO'

TIPO_IDENTIFICACION_CHOICES = (
    (TIPO_IDENTIFICACION_RNC, 'RNC'),
    (TIPO_IDENTIFICACION_CEDULA, 'Cédula'),
    (TIPO_IDENTIFICACION_PASAPORTE, 'Pasaporte'),
    (TIPO_IDENTIFICACION_OTRO, 'Otro'),
)

# =============================================================================
# TIPOS DE CONTRIBUYENTE
# =============================================================================

TIPO_CONTRIBUYENTE_JURIDICA = 'JURIDICA'
TIPO_CONTRIBUYENTE_FISICA = 'FISICA'
TIPO_CONTRIBUYENTE_INFORMAL = 'INFORMAL'
TIPO_CONTRIBUYENTE_ESTATAL = 'ESTATAL'
TIPO_CONTRIBUYENTE_EXTRANJERO = 'EXTRANJERO'

TIPO_CONTRIBUYENTE_CHOICES = (
    (TIPO_CONTRIBUYENTE_JURIDICA, 'Persona Jurídica'),
    (TIPO_CONTRIBUYENTE_FISICA, 'Persona Física'),
    (TIPO_CONTRIBUYENTE_INFORMAL, 'Proveedor Informal'),
    (TIPO_CONTRIBUYENTE_ESTATAL, 'Gobierno / Estatal'),
    (TIPO_CONTRIBUYENTE_EXTRANJERO, 'Extranjero'),
)

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío.'
ERROR_RNC_REQUERIDO = 'El número de identificación es obligatorio para RNC.'
ERROR_NUMERO_IDENTIFICACION_DUPLICADO = 'Ya existe un proveedor con este número de identificación en esta empresa.'
ERROR_TELEFONO_INVALIDO = 'El teléfono contiene caracteres inválidos.'
ERROR_TELEFONO_LONGITUD = 'El teléfono debe tener entre 10 y 15 dígitos.'
ERROR_EMAIL_INVALIDO = 'Formato de correo electrónico inválido.'
ERROR_RNC_FORMATO = 'El RNC debe tener entre 9 y 11 dígitos numéricos.'
ERROR_CEDULA_FORMATO = 'El formato de cédula debe ser XXX-XXXXXXX-X.'

# =============================================================================
# REGEX PARA VALIDACIONES
# =============================================================================

REGEX_RNC = r'^[0-9]{9,11}$'
REGEX_CEDULA = r'^[0-9]{3}-[0-9]{7}-[0-9]{1}$'
REGEX_TELEFONO = r'^[\d\s\-\(\)]+$'

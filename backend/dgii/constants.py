"""
Constantes para el módulo DGII

Centraliza valores para mantener DRY y facilitar mantenimiento.
"""

# =============================================================================
# PREFIJOS NCF
# =============================================================================

PREFIJO_B = 'B'  # Prefijo estándar
PREFIJO_E = 'E'  # Prefijo para comprobantes electrónicos

PREFIJOS_NCF_VALIDOS = [PREFIJO_B, PREFIJO_E]

# =============================================================================
# TIPOS DE IDENTIFICACIÓN DGII
# =============================================================================

TIPO_IDENTIFICACION_RNC = '1'
TIPO_IDENTIFICACION_CEDULA = '2'
TIPO_IDENTIFICACION_OTRO = '3'

TIPO_IDENTIFICACION_CHOICES = (
    (TIPO_IDENTIFICACION_RNC, 'RNC'),
    (TIPO_IDENTIFICACION_CEDULA, 'Cédula'),
    (TIPO_IDENTIFICACION_OTRO, 'Otro'),
)

# Longitudes para determinar tipo de identificación
LONGITUD_RNC = 9
LONGITUD_CEDULA = 11

# =============================================================================
# CÓDIGOS DE TIPO DE COMPROBANTE
# =============================================================================

LONGITUD_CODIGO_TIPO = 2

# Tipos de comprobante DGII
TIPO_FACTURA_CREDITO_FISCAL = '01'
TIPO_FACTURA_CONSUMIDOR = '02'
TIPO_NOTA_DEBITO = '03'
TIPO_NOTA_CREDITO = '04'
TIPO_REGISTRO_UNICO_INGRESO = '11'
TIPO_REGISTRO_GASTOS_MENORES = '12'
TIPO_COMPROBANTE_COMPRAS = '13'
TIPO_GASTOS_MENORES = '14'
TIPO_GUBERNAMENTAL = '15'
TIPO_REGIMENES_ESPECIALES = '16'
TIPO_EXTERIOR = '17'

# =============================================================================
# TIPOS DE ANULACIÓN (608)
# =============================================================================

TIPO_ANULACION_DETERIORO = '01'
TIPO_ANULACION_ERROR_IMPRESION = '02'
TIPO_ANULACION_IMPRESION_DEFECTUOSA = '03'
TIPO_ANULACION_DUPLICIDAD = '04'
TIPO_ANULACION_CORRECCION = '05'
TIPO_ANULACION_CAMBIO_PRODUCTOS = '06'
TIPO_ANULACION_DEVOLUCION = '07'
TIPO_ANULACION_OMISION_PRODUCTOS = '08'
TIPO_ANULACION_ERROR_SECUENCIA = '09'

TIPO_ANULACION_CHOICES = (
    (TIPO_ANULACION_DETERIORO, 'Deterioro'),
    (TIPO_ANULACION_ERROR_IMPRESION, 'Error de impresión'),
    (TIPO_ANULACION_IMPRESION_DEFECTUOSA, 'Impresión defectuosa'),
    (TIPO_ANULACION_DUPLICIDAD, 'Duplicidad'),
    (TIPO_ANULACION_CORRECCION, 'Corrección de información'),
    (TIPO_ANULACION_CAMBIO_PRODUCTOS, 'Cambio de productos'),
    (TIPO_ANULACION_DEVOLUCION, 'Devolución de productos'),
    (TIPO_ANULACION_OMISION_PRODUCTOS, 'Omisión de productos'),
    (TIPO_ANULACION_ERROR_SECUENCIA, 'Errores en secuencia NCF'),
)

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

ALERTA_CANTIDAD_DEFAULT = 10
PREFIJO_DEFAULT = PREFIJO_B

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 100
PAGE_SIZE_MAX = 500
PAGE_SIZE_REPORTES = 20

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

# Validaciones de TipoComprobante
ERROR_CODIGO_LONGITUD = 'El código debe tener exactamente 2 dígitos'
ERROR_PREFIJO_INVALIDO = f'El prefijo debe ser {PREFIJO_B} o {PREFIJO_E}'

# Validaciones de SecuenciaNCF
ERROR_SECUENCIA_FINAL_MAYOR = 'La secuencia final debe ser mayor que la inicial'
ERROR_SECUENCIA_ACTUAL_NEGATIVA = 'La secuencia actual no puede ser negativa'
ERROR_SECUENCIA_ACTUAL_MENOR_INICIAL = 'La secuencia actual no puede ser menor que la inicial'
ERROR_SECUENCIA_ACTUAL_MAYOR_FINAL = 'La secuencia actual no puede ser mayor que la final'
ERROR_FECHA_VENCIMIENTO_PASADA = 'La fecha de vencimiento no puede ser pasada para nuevas secuencias'
ERROR_TIPO_COMPROBANTE_EMPRESA = 'El tipo de comprobante debe pertenecer a la misma empresa'
ERROR_ALERTA_CANTIDAD_NEGATIVA = 'La alerta de cantidad debe ser positiva'
ERROR_SECUENCIA_AGOTADA = 'Secuencia de comprobantes agotada'

# Validaciones de serializer
ERROR_TIPO_COMPROBANTE_OTRA_EMPRESA = 'El tipo de comprobante debe pertenecer a su empresa'

# Errores de acciones
ERROR_SECUENCIA_NO_ACTIVA = 'Esta secuencia no está activa'
ERROR_SECUENCIA_AGOTADA_ACCION = 'Esta secuencia está agotada'
ERROR_SECUENCIA_VENCIDA = 'Esta secuencia ha vencido'
ERROR_NO_SECUENCIA_DISPONIBLE = 'No hay secuencia disponible para este tipo de comprobante'
ERROR_MES_ANIO_REQUERIDOS = 'Debe especificar mes y año'
ERROR_MES_ANIO_NUMEROS = 'mes y año deben ser números'

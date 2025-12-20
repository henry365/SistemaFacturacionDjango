"""
Constantes para el módulo Productos

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""

# =============================================================================
# TIPOS DE PRODUCTO
# =============================================================================

TIPO_ALMACENABLE = 'ALMACENABLE'
TIPO_SERVICIO = 'SERVICIO'
TIPO_CONSUMIBLE = 'CONSUMIBLE'
TIPO_ACTIVO_FIJO = 'ACTIVO_FIJO'

TIPO_PRODUCTO_CHOICES = (
    (TIPO_ALMACENABLE, 'Producto Almacenable (Inventario)'),
    (TIPO_SERVICIO, 'Servicio (Intangible)'),
    (TIPO_CONSUMIBLE, 'Consumible (Uso Interno)'),
    (TIPO_ACTIVO_FIJO, 'Activo Fijo (Maquinaria/Equipos)'),
)

# Tipos que no controlan stock
TIPOS_PRODUCTO_SIN_STOCK = [TIPO_SERVICIO, TIPO_ACTIVO_FIJO]

# =============================================================================
# TIPOS DE REFERENCIA CRUZADA
# =============================================================================

TIPO_REFERENCIA_RELACIONADO = 'RELACIONADO'
TIPO_REFERENCIA_SUSTITUTO = 'SUSTITUTO'
TIPO_REFERENCIA_COMPLEMENTARIO = 'COMPLEMENTARIO'
TIPO_REFERENCIA_ACCESORIO = 'ACCESORIO'
TIPO_REFERENCIA_REPUESTO = 'REPUESTO'

TIPO_REFERENCIA_CHOICES = (
    (TIPO_REFERENCIA_RELACIONADO, 'Producto Relacionado'),
    (TIPO_REFERENCIA_SUSTITUTO, 'Producto Sustituto'),
    (TIPO_REFERENCIA_COMPLEMENTARIO, 'Producto Complementario'),
    (TIPO_REFERENCIA_ACCESORIO, 'Accesorio'),
    (TIPO_REFERENCIA_REPUESTO, 'Repuesto'),
)

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

ITBIS_DEFAULT = 18.00
ITBIS_MIN = 0.00
ITBIS_MAX = 100.00

DESCUENTO_MIN = 0.00
DESCUENTO_MAX = 100.00

PRECIO_MIN = 0.00

MESES_GARANTIA_MIN = 0

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# =============================================================================
# FORMATOS DE ARCHIVO PARA CARGA MASIVA
# =============================================================================

FORMATOS_ARCHIVO_SOPORTADOS = ['.csv', '.xlsx']
COLUMNAS_REQUERIDAS_CATALOGO = ['codigo_sku', 'nombre', 'precio_venta_base']

# =============================================================================
# REGEX PARA VALIDACIONES
# =============================================================================

SKU_REGEX = r'^[a-zA-Z0-9_-]+$'

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío.'
ERROR_NOMBRE_REQUERIDO = 'El nombre es requerido.'
ERROR_NOMBRE_DUPLICADO = 'Ya existe una categoría con este nombre.'

ERROR_SKU_VACIO = 'El código SKU no puede estar vacío.'
ERROR_SKU_DUPLICADO = 'Ya existe un producto con este código SKU.'
ERROR_SKU_FORMATO = 'El SKU solo puede contener letras, números, guiones (-) y guiones bajos (_).'

ERROR_PRECIO_NEGATIVO = 'El precio de venta no puede ser negativo.'

ERROR_ITBIS_RANGO = 'El porcentaje de ITBIS debe estar entre 0 y 100.'

ERROR_DESCUENTO_PROMOCIONAL_RANGO = 'El descuento promocional debe estar entre 0 y 100.'
ERROR_DESCUENTO_MAXIMO_RANGO = 'El descuento máximo debe estar entre 0 y 100.'
ERROR_DESCUENTO_MAXIMO_MENOR = 'El descuento máximo no puede ser menor al descuento promocional.'

ERROR_MESES_GARANTIA_NEGATIVO = 'Los meses de garantía no pueden ser negativos.'
ERROR_MESES_GARANTIA_REQUERIDO = 'Si el producto tiene garantía, los meses deben ser mayores a cero.'

ERROR_PRODUCTO_ORIGEN_DESTINO_IGUAL = 'El producto destino no puede ser el mismo que el origen.'

ERROR_ARCHIVO_NO_PROPORCIONADO = 'No se proporcionó ningún archivo.'
ERROR_FORMATO_NO_SOPORTADO = 'Formato no soportado. Use .csv o .xlsx'
ERROR_COLUMNAS_FALTANTES = 'Faltan columnas requeridas: {columnas}'

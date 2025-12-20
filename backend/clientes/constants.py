"""
Constantes para el módulo de Clientes

Este módulo centraliza todas las constantes utilizadas en el módulo de clientes,
siguiendo el principio DRY (Don't Repeat Yourself).
"""
from decimal import Decimal


# ============================================================
# TIPOS DE IDENTIFICACIÓN
# ============================================================

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

# Tipos que requieren número de identificación obligatorio
TIPOS_REQUIEREN_NUMERO = [TIPO_IDENTIFICACION_RNC]


# ============================================================
# VALORES POR DEFECTO
# ============================================================

LIMITE_CREDITO_DEFAULT = Decimal('0.00')
DESCUENTO_PORCENTAJE_DEFAULT = Decimal('0.00')


# ============================================================
# LÍMITES Y VALIDACIONES
# ============================================================

DESCUENTO_MIN = Decimal('0.00')
DESCUENTO_MAX = Decimal('100.00')
LIMITE_CREDITO_MIN = Decimal('0.00')


# ============================================================
# MENSAJES DE ERROR
# ============================================================

ERROR_NOMBRE_VACIO = 'El nombre no puede estar vacío.'
ERROR_DESCUENTO_RANGO = 'El descuento debe estar entre 0 y 100.'
ERROR_LIMITE_CREDITO_NEGATIVO = 'El límite de crédito no puede ser negativo.'
ERROR_NUMERO_IDENTIFICACION_REQUERIDO = 'El número de identificación es obligatorio para {tipo}.'
ERROR_CATEGORIA_OTRA_EMPRESA = 'La categoría debe pertenecer a la misma empresa del cliente.'
ERROR_VENDEDOR_OTRA_EMPRESA = 'El vendedor debe pertenecer a la misma empresa del cliente.'
ERROR_CATEGORIA_DUPLICADA = 'Ya existe una categoría con este nombre para esta empresa.'
ERROR_CLIENTE_IDENTIFICACION_DUPLICADA = 'Ya existe un cliente con este número de identificación para esta empresa.'

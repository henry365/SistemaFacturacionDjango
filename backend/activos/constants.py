"""
Constantes para el módulo de Activos Fijos
"""
from decimal import Decimal

# Estados de activos fijos
ESTADO_ACTIVO = 'ACTIVO'
ESTADO_MANTENIMIENTO = 'MANTENIMIENTO'
ESTADO_DEPRECIADO = 'DEPRECIADO'
ESTADO_VENDIDO = 'VENDIDO'
ESTADO_DESINCORPORADO = 'DESINCORPORADO'

ESTADO_CHOICES = (
    (ESTADO_ACTIVO, 'Activo / En Uso'),
    (ESTADO_MANTENIMIENTO, 'En Mantenimiento'),
    (ESTADO_DEPRECIADO, 'Totalmente Depreciado'),
    (ESTADO_VENDIDO, 'Vendido'),
    (ESTADO_DESINCORPORADO, 'Desincorporado / Danado'),
)

ESTADOS_VALIDOS = [e[0] for e in ESTADO_CHOICES]

# Estados que permiten depreciación
ESTADOS_DEPRECIABLES = [ESTADO_ACTIVO, ESTADO_MANTENIMIENTO]

# Validaciones de porcentaje de depreciación
PORCENTAJE_DEPRECIACION_MIN = Decimal('0')
PORCENTAJE_DEPRECIACION_MAX = Decimal('100')

# Vida útil mínima en años
VIDA_UTIL_MIN_ANOS = 1

# Tolerancia para comparación de decimales
TOLERANCIA_DECIMAL = Decimal('0.01')

# Porcentajes de depreciación típicos según DGII RD
TASAS_DGII = {
    'EDIFICIOS': Decimal('5.00'),
    'VEHICULOS': Decimal('25.00'),
    'MOBILIARIO': Decimal('10.00'),
    'EQUIPOS_OFICINA': Decimal('20.00'),
    'EQUIPOS_COMPUTO': Decimal('33.33'),
    'MAQUINARIA': Decimal('10.00'),
}

# Meses en un año (para cálculo de depreciación mensual)
MESES_POR_ANO = 12

# Prefijos para códigos internos de activos
PREFIJO_CODIGO_DEFAULT = 'ACT'

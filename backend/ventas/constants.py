"""
Constantes para el módulo Ventas

Centraliza valores para mantener DRY (Don't Repeat Yourself).
"""
from decimal import Decimal

# =============================================================================
# CONFIGURACIÓN DE PAGINACIÓN
# =============================================================================

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# =============================================================================
# ESTADOS DE COTIZACIÓN
# =============================================================================

ESTADO_COTIZACION_PENDIENTE = 'PENDIENTE'
ESTADO_COTIZACION_APROBADA = 'APROBADA'
ESTADO_COTIZACION_RECHAZADA = 'RECHAZADA'
ESTADO_COTIZACION_EXPIRADA = 'EXPIRADA'

ESTADO_COTIZACION_CHOICES = (
    (ESTADO_COTIZACION_PENDIENTE, 'Pendiente'),
    (ESTADO_COTIZACION_APROBADA, 'Aprobada'),
    (ESTADO_COTIZACION_RECHAZADA, 'Rechazada'),
    (ESTADO_COTIZACION_EXPIRADA, 'Expirada'),
)

# =============================================================================
# ESTADOS DE FACTURA
# =============================================================================

ESTADO_FACTURA_PENDIENTE_PAGO = 'PENDIENTE_PAGO'
ESTADO_FACTURA_PAGADA_PARCIAL = 'PAGADA_PARCIAL'
ESTADO_FACTURA_PAGADA = 'PAGADA'
ESTADO_FACTURA_CANCELADA = 'CANCELADA'

ESTADO_FACTURA_CHOICES = (
    (ESTADO_FACTURA_PENDIENTE_PAGO, 'Pendiente de Pago'),
    (ESTADO_FACTURA_PAGADA_PARCIAL, 'Pagada Parcialmente'),
    (ESTADO_FACTURA_PAGADA, 'Pagada'),
    (ESTADO_FACTURA_CANCELADA, 'Cancelada'),
)

ESTADOS_FACTURA_PARA_COMISION = [ESTADO_FACTURA_PAGADA, ESTADO_FACTURA_PAGADA_PARCIAL]

# =============================================================================
# TIPOS DE VENTA
# =============================================================================

TIPO_VENTA_CONTADO = 'CONTADO'
TIPO_VENTA_CREDITO = 'CREDITO'

TIPO_VENTA_CHOICES = (
    (TIPO_VENTA_CONTADO, 'Contado'),
    (TIPO_VENTA_CREDITO, 'Crédito'),
)

# =============================================================================
# ESTADOS DE LISTA DE ESPERA
# =============================================================================

ESTADO_LISTA_PENDIENTE = 'PENDIENTE'
ESTADO_LISTA_NOTIFICADO = 'NOTIFICADO'
ESTADO_LISTA_COMPLETADO = 'COMPLETADO'
ESTADO_LISTA_CANCELADO = 'CANCELADO'

ESTADO_LISTA_CHOICES = (
    (ESTADO_LISTA_PENDIENTE, 'Pendiente'),
    (ESTADO_LISTA_NOTIFICADO, 'Notificado'),
    (ESTADO_LISTA_COMPLETADO, 'Completado'),
    (ESTADO_LISTA_CANCELADO, 'Cancelado'),
)

# =============================================================================
# PRIORIDADES
# =============================================================================

PRIORIDAD_NORMAL = 'NORMAL'
PRIORIDAD_ALTA = 'ALTA'

PRIORIDAD_CHOICES = (
    (PRIORIDAD_NORMAL, 'Normal'),
    (PRIORIDAD_ALTA, 'Alta'),
)

# =============================================================================
# MÉTODOS DE PAGO
# =============================================================================

METODO_PAGO_EFECTIVO = 'EFECTIVO'
METODO_PAGO_TARJETA = 'TARJETA'
METODO_PAGO_TRANSFERENCIA = 'TRANSFERENCIA'
METODO_PAGO_CHEQUE = 'CHEQUE'
METODO_PAGO_OTRO = 'OTRO'

METODO_PAGO_CHOICES = (
    (METODO_PAGO_EFECTIVO, 'Efectivo'),
    (METODO_PAGO_TARJETA, 'Tarjeta'),
    (METODO_PAGO_TRANSFERENCIA, 'Transferencia'),
    (METODO_PAGO_CHEQUE, 'Cheque'),
    (METODO_PAGO_OTRO, 'Otro'),
)

# =============================================================================
# VALORES POR DEFECTO
# =============================================================================

TASA_CAMBIO_DEFAULT = Decimal('1.0000')
TOTAL_DEFAULT = Decimal('0.00')
MONTO_DEFAULT = Decimal('0.00')

# =============================================================================
# MENSAJES DE ERROR
# =============================================================================

ERROR_CLIENTE_EMPRESA = 'El cliente debe pertenecer a la misma empresa.'
ERROR_VENDEDOR_EMPRESA = 'El vendedor debe pertenecer a la misma empresa.'
ERROR_COTIZACION_EMPRESA = 'La cotización debe pertenecer a la misma empresa.'
ERROR_FACTURA_EMPRESA = 'La factura debe pertenecer a la misma empresa.'
ERROR_PRODUCTO_EMPRESA = 'El producto debe pertenecer a la misma empresa.'
ERROR_TOTAL_NEGATIVO = 'El total no puede ser negativo.'
ERROR_MONTO_NEGATIVO = 'El monto no puede ser negativo.'
ERROR_MONTO_MAYOR_CERO = 'El monto debe ser mayor a cero.'
ERROR_MONTO_PENDIENTE_NEGATIVO = 'El monto pendiente no puede ser negativo.'
ERROR_MONTO_PENDIENTE_MAYOR_TOTAL = 'El monto pendiente no puede ser mayor que el total.'
ERROR_TASA_CAMBIO_INVALIDA = 'La tasa de cambio debe ser mayor a cero.'
ERROR_CANTIDAD_INVALIDA = 'La cantidad debe ser mayor a cero.'
ERROR_PRECIO_NEGATIVO = 'El precio unitario no puede ser negativo.'
ERROR_DESCUENTO_NEGATIVO = 'El descuento no puede ser negativo.'
ERROR_ITBIS_NEGATIVO = 'El ITBIS no puede ser negativo.'
ERROR_IMPUESTO_NEGATIVO = 'El impuesto no puede ser negativo.'
ERROR_LIMITE_CREDITO_EXCEDIDO = 'El total excede el límite de crédito del cliente ({limite}).'
ERROR_VIGENCIA_INVALIDA = 'La fecha de vigencia no puede ser anterior a la fecha de creación.'
ERROR_MOTIVO_VACIO = 'El motivo no puede estar vacío.'

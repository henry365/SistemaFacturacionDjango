"""
Constantes para el módulo Compras

Este módulo centraliza todas las constantes utilizadas en el módulo de compras,
siguiendo los estándares de la Guía Inicial para mantener consistencia y
facilitar el mantenimiento.
"""
from decimal import Decimal

# ============================================================
# ESTADOS DE COMPRA
# ============================================================

ESTADO_COMPRA_REGISTRADA = 'REGISTRADA'
ESTADO_COMPRA_CXP = 'CXP'
ESTADO_COMPRA_PAGADA = 'PAGADA'
ESTADO_COMPRA_ANULADA = 'ANULADA'

ESTADO_COMPRA_CHOICES = (
    (ESTADO_COMPRA_REGISTRADA, 'Registrada'),
    (ESTADO_COMPRA_CXP, 'En Cuentas por Pagar'),
    (ESTADO_COMPRA_PAGADA, 'Pagada'),
    (ESTADO_COMPRA_ANULADA, 'Anulada'),
)

# Transiciones permitidas para Compra
TRANSICIONES_COMPRA = {
    ESTADO_COMPRA_REGISTRADA: [ESTADO_COMPRA_CXP, ESTADO_COMPRA_ANULADA],
    ESTADO_COMPRA_CXP: [ESTADO_COMPRA_PAGADA, ESTADO_COMPRA_ANULADA],
    ESTADO_COMPRA_PAGADA: [],  # Estado final
    ESTADO_COMPRA_ANULADA: [],  # Estado final
}

# ============================================================
# ESTADOS DE ORDEN DE COMPRA
# ============================================================

ESTADO_ORDEN_BORRADOR = 'BORRADOR'
ESTADO_ORDEN_APROBADA = 'APROBADA'
ESTADO_ORDEN_ENVIADA = 'ENVIADA'
ESTADO_ORDEN_RECIBIDA_PARCIAL = 'RECIBIDA_PARCIAL'
ESTADO_ORDEN_RECIBIDA_TOTAL = 'RECIBIDA_TOTAL'
ESTADO_ORDEN_CANCELADA = 'CANCELADA'

ESTADO_ORDEN_CHOICES = (
    (ESTADO_ORDEN_BORRADOR, 'Borrador'),
    (ESTADO_ORDEN_APROBADA, 'Aprobada'),
    (ESTADO_ORDEN_ENVIADA, 'Enviada al Proveedor'),
    (ESTADO_ORDEN_RECIBIDA_PARCIAL, 'Recibida Parcialmente'),
    (ESTADO_ORDEN_RECIBIDA_TOTAL, 'Recibida Totalmente'),
    (ESTADO_ORDEN_CANCELADA, 'Cancelada'),
)

# Transiciones permitidas para OrdenCompra
TRANSICIONES_ORDEN = {
    ESTADO_ORDEN_BORRADOR: [ESTADO_ORDEN_APROBADA, ESTADO_ORDEN_ENVIADA, ESTADO_ORDEN_CANCELADA],
    ESTADO_ORDEN_APROBADA: [ESTADO_ORDEN_ENVIADA, ESTADO_ORDEN_RECIBIDA_PARCIAL, ESTADO_ORDEN_CANCELADA],
    ESTADO_ORDEN_ENVIADA: [ESTADO_ORDEN_RECIBIDA_PARCIAL, ESTADO_ORDEN_RECIBIDA_TOTAL, ESTADO_ORDEN_CANCELADA],
    ESTADO_ORDEN_RECIBIDA_PARCIAL: [ESTADO_ORDEN_RECIBIDA_TOTAL, ESTADO_ORDEN_CANCELADA],
    ESTADO_ORDEN_RECIBIDA_TOTAL: [],  # Estado final
    ESTADO_ORDEN_CANCELADA: [],  # Estado final
}

# Estados de orden que permiten recepción
ESTADOS_ORDEN_PERMITE_RECEPCION = [ESTADO_ORDEN_APROBADA, ESTADO_ORDEN_ENVIADA, ESTADO_ORDEN_RECIBIDA_PARCIAL]

# ============================================================
# ESTADOS DE GASTO
# ============================================================

ESTADO_GASTO_PENDIENTE = 'PENDIENTE'
ESTADO_GASTO_PAGADO = 'PAGADO'

ESTADO_GASTO_CHOICES = (
    (ESTADO_GASTO_PENDIENTE, 'Pendiente de Pago'),
    (ESTADO_GASTO_PAGADO, 'Pagado'),
)

# ============================================================
# ESTADOS DE SOLICITUD DE COTIZACION
# ============================================================

ESTADO_SOLICITUD_PENDIENTE = 'PENDIENTE'
ESTADO_SOLICITUD_ENVIADA = 'ENVIADA'
ESTADO_SOLICITUD_RECIBIDA = 'RECIBIDA'
ESTADO_SOLICITUD_CANCELADA = 'CANCELADA'

ESTADO_SOLICITUD_CHOICES = (
    (ESTADO_SOLICITUD_PENDIENTE, 'Pendiente'),
    (ESTADO_SOLICITUD_ENVIADA, 'Enviada'),
    (ESTADO_SOLICITUD_RECIBIDA, 'Recibida'),
    (ESTADO_SOLICITUD_CANCELADA, 'Cancelada'),
)

# ============================================================
# ESTADOS DE RECEPCION DE COMPRA
# ============================================================

ESTADO_RECEPCION_PENDIENTE = 'PENDIENTE'
ESTADO_RECEPCION_PARCIAL = 'PARCIAL'
ESTADO_RECEPCION_COMPLETA = 'COMPLETA'
ESTADO_RECEPCION_CANCELADA = 'CANCELADA'

ESTADO_RECEPCION_CHOICES = (
    (ESTADO_RECEPCION_PENDIENTE, 'Pendiente'),
    (ESTADO_RECEPCION_PARCIAL, 'Parcialmente Recibida'),
    (ESTADO_RECEPCION_COMPLETA, 'Completamente Recibida'),
    (ESTADO_RECEPCION_CANCELADA, 'Cancelada'),
)

# ============================================================
# ESTADOS DE DEVOLUCION A PROVEEDOR
# ============================================================

ESTADO_DEVOLUCION_BORRADOR = 'BORRADOR'
ESTADO_DEVOLUCION_CONFIRMADA = 'CONFIRMADA'
ESTADO_DEVOLUCION_ENVIADA = 'ENVIADA'
ESTADO_DEVOLUCION_ACEPTADA = 'ACEPTADA'
ESTADO_DEVOLUCION_CANCELADA = 'CANCELADA'

ESTADO_DEVOLUCION_CHOICES = (
    (ESTADO_DEVOLUCION_BORRADOR, 'Borrador'),
    (ESTADO_DEVOLUCION_CONFIRMADA, 'Confirmada'),
    (ESTADO_DEVOLUCION_ENVIADA, 'Enviada al Proveedor'),
    (ESTADO_DEVOLUCION_ACEPTADA, 'Aceptada por Proveedor'),
    (ESTADO_DEVOLUCION_CANCELADA, 'Cancelada'),
)

TRANSICIONES_DEVOLUCION = {
    ESTADO_DEVOLUCION_BORRADOR: [ESTADO_DEVOLUCION_CONFIRMADA, ESTADO_DEVOLUCION_CANCELADA],
    ESTADO_DEVOLUCION_CONFIRMADA: [ESTADO_DEVOLUCION_ENVIADA, ESTADO_DEVOLUCION_CANCELADA],
    ESTADO_DEVOLUCION_ENVIADA: [ESTADO_DEVOLUCION_ACEPTADA, ESTADO_DEVOLUCION_CANCELADA],
    ESTADO_DEVOLUCION_ACEPTADA: [],  # Estado final
    ESTADO_DEVOLUCION_CANCELADA: [],  # Estado final
}

# Motivos de devolución
MOTIVO_DEVOLUCION_DEFECTO = 'DEFECTO'
MOTIVO_DEVOLUCION_ERROR = 'ERROR'
MOTIVO_DEVOLUCION_GARANTIA = 'GARANTIA'
MOTIVO_DEVOLUCION_CADUCADO = 'CADUCADO'
MOTIVO_DEVOLUCION_DANADO = 'DANADO'
MOTIVO_DEVOLUCION_OTRO = 'OTRO'

MOTIVO_DEVOLUCION_CHOICES = (
    (MOTIVO_DEVOLUCION_DEFECTO, 'Producto Defectuoso'),
    (MOTIVO_DEVOLUCION_ERROR, 'Error en Pedido'),
    (MOTIVO_DEVOLUCION_GARANTIA, 'Garantía'),
    (MOTIVO_DEVOLUCION_CADUCADO, 'Producto Caducado'),
    (MOTIVO_DEVOLUCION_DANADO, 'Producto Dañado'),
    (MOTIVO_DEVOLUCION_OTRO, 'Otro'),
)

# ============================================================
# ESTADOS DE LIQUIDACION DE IMPORTACION
# ============================================================

ESTADO_LIQUIDACION_BORRADOR = 'BORRADOR'
ESTADO_LIQUIDACION_LIQUIDADA = 'LIQUIDADA'
ESTADO_LIQUIDACION_CANCELADA = 'CANCELADA'

ESTADO_LIQUIDACION_CHOICES = (
    (ESTADO_LIQUIDACION_BORRADOR, 'Borrador'),
    (ESTADO_LIQUIDACION_LIQUIDADA, 'Liquidada'),
    (ESTADO_LIQUIDACION_CANCELADA, 'Cancelada'),
)

TRANSICIONES_LIQUIDACION = {
    ESTADO_LIQUIDACION_BORRADOR: [ESTADO_LIQUIDACION_LIQUIDADA, ESTADO_LIQUIDACION_CANCELADA],
    ESTADO_LIQUIDACION_LIQUIDADA: [],  # Estado final
    ESTADO_LIQUIDACION_CANCELADA: [],  # Estado final
}

# ============================================================
# TIPOS DE GASTO DGII (606)
# ============================================================

TIPO_GASTO_PERSONAL = '01'
TIPO_GASTO_TRABAJOS = '02'
TIPO_GASTO_ARRENDAMIENTOS = '03'
TIPO_GASTO_ACTIVOS_FIJOS = '04'
TIPO_GASTO_REPRESENTACION = '05'
TIPO_GASTO_OTRAS_DEDUCCIONES = '06'
TIPO_GASTO_FINANCIEROS = '07'
TIPO_GASTO_EXTRAORDINARIOS = '08'
TIPO_GASTO_COSTO_VENTA = '09'
TIPO_GASTO_ADQUISICIONES = '10'
TIPO_GASTO_SEGUROS = '11'

TIPO_GASTO_DGII_CHOICES = (
    (TIPO_GASTO_PERSONAL, '01 - Gastos de Personal'),
    (TIPO_GASTO_TRABAJOS, '02 - Gastos por Trabajos, Suministros y Servicios'),
    (TIPO_GASTO_ARRENDAMIENTOS, '03 - Arrendamientos'),
    (TIPO_GASTO_ACTIVOS_FIJOS, '04 - Gastos de Activos Fijos'),
    (TIPO_GASTO_REPRESENTACION, '05 - Gastos de Representación'),
    (TIPO_GASTO_OTRAS_DEDUCCIONES, '06 - Otras Deducciones Admitidas'),
    (TIPO_GASTO_FINANCIEROS, '07 - Gastos Financieros'),
    (TIPO_GASTO_EXTRAORDINARIOS, '08 - Gastos Extraordinarios'),
    (TIPO_GASTO_COSTO_VENTA, '09 - Compras y Gastos que forman parte del Costo de Venta'),
    (TIPO_GASTO_ADQUISICIONES, '10 - Adquisiciones de Activos'),
    (TIPO_GASTO_SEGUROS, '11 - Gastos de Seguros'),
)

# ============================================================
# TIPOS DE LINEA
# ============================================================

TIPO_LINEA_ALMACENABLE = 'ALMACENABLE'
TIPO_LINEA_GASTO = 'GASTO'
TIPO_LINEA_ACTIVO = 'ACTIVO'

TIPO_LINEA_CHOICES = (
    (TIPO_LINEA_ALMACENABLE, 'Inventario'),
    (TIPO_LINEA_GASTO, 'Gasto Directo'),
    (TIPO_LINEA_ACTIVO, 'Activo Fijo'),
)

# ============================================================
# INCOTERMS
# ============================================================

INCOTERM_FOB = 'FOB'
INCOTERM_CIF = 'CIF'
INCOTERM_EXW = 'EXW'
INCOTERM_FCA = 'FCA'
INCOTERM_CFR = 'CFR'
INCOTERM_DAP = 'DAP'
INCOTERM_DDP = 'DDP'

INCOTERM_CHOICES = (
    (INCOTERM_FOB, 'FOB - Free On Board'),
    (INCOTERM_CIF, 'CIF - Cost, Insurance and Freight'),
    (INCOTERM_EXW, 'EXW - Ex Works'),
    (INCOTERM_FCA, 'FCA - Free Carrier'),
    (INCOTERM_CFR, 'CFR - Cost and Freight'),
    (INCOTERM_DAP, 'DAP - Delivered at Place'),
    (INCOTERM_DDP, 'DDP - Delivered Duty Paid'),
)

# ============================================================
# METODOS DE PRORRATEO
# ============================================================

METODO_PRORRATEO_VALOR = 'VALOR'
METODO_PRORRATEO_PESO = 'PESO'
METODO_PRORRATEO_VOLUMEN = 'VOLUMEN'
METODO_PRORRATEO_UNIDADES = 'UNIDADES'

METODO_PRORRATEO_CHOICES = (
    (METODO_PRORRATEO_VALOR, 'Por Valor FOB'),
    (METODO_PRORRATEO_PESO, 'Por Peso'),
    (METODO_PRORRATEO_VOLUMEN, 'Por Volumen'),
    (METODO_PRORRATEO_UNIDADES, 'Por Unidades'),
)

# ============================================================
# TIPOS DE GASTO DE IMPORTACION
# ============================================================

TIPO_GASTO_IMPORT_FLETE = 'FLETE'
TIPO_GASTO_IMPORT_SEGURO = 'SEGURO'
TIPO_GASTO_IMPORT_ADUANA = 'ADUANA'
TIPO_GASTO_IMPORT_IMPUESTOS = 'IMPUESTOS'
TIPO_GASTO_IMPORT_TRANSPORTE = 'TRANSPORTE'
TIPO_GASTO_IMPORT_ALMACENAJE = 'ALMACENAJE'
TIPO_GASTO_IMPORT_AGENTE = 'AGENTE'
TIPO_GASTO_IMPORT_OTROS = 'OTROS'

TIPO_GASTO_IMPORTACION_CHOICES = (
    (TIPO_GASTO_IMPORT_FLETE, 'Flete Internacional'),
    (TIPO_GASTO_IMPORT_SEGURO, 'Seguro de Carga'),
    (TIPO_GASTO_IMPORT_ADUANA, 'Gastos de Aduana'),
    (TIPO_GASTO_IMPORT_IMPUESTOS, 'Impuestos de Importación'),
    (TIPO_GASTO_IMPORT_TRANSPORTE, 'Transporte Local'),
    (TIPO_GASTO_IMPORT_ALMACENAJE, 'Almacenaje'),
    (TIPO_GASTO_IMPORT_AGENTE, 'Comisión Agente Aduanal'),
    (TIPO_GASTO_IMPORT_OTROS, 'Otros Gastos'),
)

# ============================================================
# CATEGORIAS DE RETENCION
# ============================================================

CATEGORIA_RETENCION_ISR = 'ISR'
CATEGORIA_RETENCION_ITBIS = 'ITBIS'

CATEGORIA_RETENCION_CHOICES = (
    (CATEGORIA_RETENCION_ISR, 'Impuesto Sobre la Renta'),
    (CATEGORIA_RETENCION_ITBIS, 'ITBIS Retenido'),
)

# ============================================================
# VALORES POR DEFECTO
# ============================================================

TASA_CAMBIO_DEFAULT = Decimal('1.0000')
SUBTOTAL_DEFAULT = Decimal('0.00')
IMPUESTOS_DEFAULT = Decimal('0.00')
DESCUENTOS_DEFAULT = Decimal('0.00')
TOTAL_DEFAULT = Decimal('0.00')
MONTO_PAGADO_DEFAULT = Decimal('0.00')

# Tolerancia para comparaciones decimales
TOLERANCIA_DECIMAL = Decimal('0.01')

# ============================================================
# MENSAJES DE ERROR
# ============================================================

ERROR_PROVEEDOR_EMPRESA = 'El proveedor debe pertenecer a la misma empresa.'
ERROR_ORDEN_EMPRESA = 'La orden de compra debe pertenecer a la misma empresa.'
ERROR_COMPRA_EMPRESA = 'La compra debe pertenecer a la misma empresa.'
ERROR_ALMACEN_EMPRESA = 'El almacén debe pertenecer a la misma empresa.'
ERROR_TIPO_RETENCION_EMPRESA = 'El tipo de retención debe pertenecer a la misma empresa.'

ERROR_TOTAL_NEGATIVO = 'El total no puede ser negativo.'
ERROR_SUBTOTAL_NEGATIVO = 'El subtotal no puede ser negativo.'
ERROR_IMPUESTOS_NEGATIVOS = 'Los impuestos no pueden ser negativos.'
ERROR_DESCUENTO_NEGATIVO = 'El descuento no puede ser negativo.'
ERROR_MONTO_NEGATIVO = 'El monto no puede ser negativo.'
ERROR_CANTIDAD_POSITIVA = 'La cantidad debe ser mayor a cero.'
ERROR_CANTIDAD_NEGATIVA = 'La cantidad no puede ser negativa.'
ERROR_COSTO_NEGATIVO = 'El costo unitario no puede ser negativo.'
ERROR_TASA_CAMBIO = 'La tasa de cambio debe ser mayor a cero.'
ERROR_PORCENTAJE_RANGO = 'El porcentaje debe estar entre 0 y 100.'

ERROR_TRANSICION_ESTADO = 'No se puede cambiar de {estado_actual} a {estado_nuevo}'
ERROR_FECHA_FUTURA = 'La fecha no puede ser futura.'
ERROR_FECHA_ENTREGA = 'La fecha de entrega esperada no puede ser anterior a la fecha de emisión.'

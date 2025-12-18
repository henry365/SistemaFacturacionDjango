"""
Configuración centralizada del Sistema de Facturación.

Este módulo contiene las constantes de negocio y valores predeterminados
que pueden ser sobrescritos por la configuración específica de cada empresa.
"""

# =============================================================================
# CONFIGURACIÓN FISCAL DGII (República Dominicana)
# =============================================================================
DGII_CONFIG = {
    # Tipos de Comprobantes Fiscales (NCF)
    'TIPOS_NCF': {
        '01': 'Factura de Crédito Fiscal',
        '02': 'Factura de Consumo',
        '03': 'Nota de Débito',
        '04': 'Nota de Crédito',
        '11': 'Comprobante de Compras',
        '12': 'Registro Único de Ingresos',
        '13': 'Comprobante para Gastos Menores',
        '14': 'Comprobante de Regímenes Especiales',
        '15': 'Comprobante Gubernamental',
        '16': 'Comprobante para Exportaciones',
        '17': 'Comprobante para Pagos al Exterior',
    },

    # Tipos de Anulación
    'TIPOS_ANULACION': {
        '01': 'Deterioro de Factura Pre-impresa',
        '02': 'Errores de Impresión (Factura Pre-impresa)',
        '03': 'Impresión Defectuosa',
        '04': 'Corrección de la Información',
        '05': 'Cambio de Productos',
        '06': 'Devolución de Productos',
        '07': 'Omisión de Productos',
        '08': 'Errores en Secuencia de NCF',
        '09': 'Por Cese de Operaciones',
        '10': 'Pérdida o Hurto de Talonarios',
    },

    # Tipos de Bienes y Servicios (para reportes DGII)
    'TIPOS_BIENES_SERVICIOS': {
        '01': 'Gastos de Personal',
        '02': 'Gastos por Trabajos, Suministros y Servicios',
        '03': 'Arrendamientos',
        '04': 'Gastos de Activos Fijos',
        '05': 'Gastos de Representación',
        '06': 'Otras Deducciones Admitidas',
        '07': 'Gastos Financieros',
        '08': 'Gastos Extraordinarios',
        '09': 'Compras y Gastos que forman parte del Costo de Venta',
        '10': 'Adquisiciones de Activos',
        '11': 'Gastos de Seguros',
    },

    # Tasas de Impuestos
    'ITBIS_TASA': 0.18,  # 18%
    'ITBIS_TASA_REDUCIDA': 0.16,  # 16% (algunos productos)
    'ITBIS_EXENTO': 0.00,  # Exento

    # Retenciones
    'RETENCION_ISR_SERVICIOS': 0.10,  # 10% personas físicas
    'RETENCION_ISR_ALQUILERES': 0.10,  # 10%
    'RETENCION_ITBIS': 0.30,  # 30% del ITBIS para agentes de retención

    # Formatos de reportes
    'FORMATO_606': {
        'nombre': 'Formato de Envío 606',
        'descripcion': 'Compras de Bienes y Servicios',
        'version': '1.0',
    },
    'FORMATO_607': {
        'nombre': 'Formato de Envío 607',
        'descripcion': 'Ventas de Bienes y Servicios',
        'version': '1.0',
    },
    'FORMATO_608': {
        'nombre': 'Formato de Envío 608',
        'descripcion': 'Comprobantes Anulados',
        'version': '1.0',
    },
}


# =============================================================================
# CONFIGURACIÓN DE FACTURACIÓN
# =============================================================================
FACTURACION_CONFIG = {
    # Plazos de crédito
    'DIAS_CREDITO_DEFAULT': 30,
    'DIAS_CREDITO_OPCIONES': [15, 30, 45, 60, 90],

    # Alertas
    'DIAS_ALERTA_VENCIMIENTO': 7,  # Días antes del vencimiento para alertar
    'DIAS_CONSIDERAR_VENCIDA': 1,  # Días después del vencimiento

    # Moneda
    'MONEDA_DEFAULT': 'DOP',
    'MONEDAS_SOPORTADAS': ['DOP', 'USD', 'EUR'],

    # Descuentos
    'DESCUENTO_MAXIMO_PORCENTAJE': 25.0,  # Máximo 25% de descuento
    'PERMITIR_DESCUENTO_FACTURA': True,

    # Numeración
    'PREFIJO_FACTURA': 'FAC',
    'PREFIJO_COTIZACION': 'COT',
    'PREFIJO_NOTA_CREDITO': 'NC',
    'PREFIJO_NOTA_DEBITO': 'ND',

    # Redondeo
    'DECIMALES_PRECIO': 2,
    'DECIMALES_CANTIDAD': 2,
    'DECIMALES_TOTAL': 2,
}


# =============================================================================
# CONFIGURACIÓN DE INVENTARIO
# =============================================================================
INVENTARIO_CONFIG = {
    # Stock
    'STOCK_MINIMO_DEFAULT': 10,
    'STOCK_MAXIMO_DEFAULT': 1000,

    # Método de costeo
    'METODO_COSTEO': 'PROMEDIO',  # PROMEDIO, PEPS, UEPS
    'METODOS_COSTEO_DISPONIBLES': ['PROMEDIO', 'PEPS', 'UEPS'],

    # Control de stock
    'PERMITIR_STOCK_NEGATIVO': False,
    'VALIDAR_STOCK_EN_FACTURACION': True,

    # Alertas de inventario
    'HABILITAR_ALERTAS_STOCK': True,
    'PORCENTAJE_STOCK_CRITICO': 20,  # % del stock mínimo

    # Lotes y vencimientos
    'USAR_LOTES': True,
    'ALERTAR_VENCIMIENTO_DIAS': 30,  # Días antes del vencimiento

    # Reservas
    'TIEMPO_RESERVA_MINUTOS': 60,  # Tiempo que dura una reserva
    'AUTO_LIBERAR_RESERVAS': True,
}


# =============================================================================
# CONFIGURACIÓN DE NOTIFICACIONES
# =============================================================================
NOTIFICACIONES_CONFIG = {
    # Emails de facturación
    'HABILITAR_EMAIL_FACTURA': True,
    'HABILITAR_EMAIL_COTIZACION': True,
    'HABILITAR_EMAIL_NOTA_CREDITO': False,

    # Emails de cobranza
    'HABILITAR_EMAIL_CXC_VENCIDA': True,
    'HABILITAR_EMAIL_CXC_POR_VENCER': True,
    'DIAS_ANTES_VENCIMIENTO_EMAIL': 3,

    # Emails de inventario
    'HABILITAR_EMAIL_STOCK_BAJO': True,
    'HABILITAR_EMAIL_STOCK_CRITICO': True,

    # Configuración de envío
    'HORA_ENVIO_ALERTAS': '08:00',  # Hora del día para enviar alertas
    'DIAS_ENTRE_RECORDATORIOS': 3,  # Días entre recordatorios de CxC
    'MAX_RECORDATORIOS': 5,  # Máximo de recordatorios por cuenta
}


# =============================================================================
# CONFIGURACIÓN DE REPORTES
# =============================================================================
REPORTES_CONFIG = {
    # Paginación
    'PAGE_SIZE_DEFAULT': 100,
    'PAGE_SIZE_MAX': 500,
    'PAGE_SIZE_OPCIONES': [25, 50, 100, 250, 500],

    # Exportación
    'FORMATOS_EXPORTACION': ['xlsx', 'csv', 'pdf'],
    'FORMATO_EXPORTACION_DEFAULT': 'xlsx',

    # Caché
    'CACHE_REPORTES_SEGUNDOS': 300,  # 5 minutos
    'HABILITAR_CACHE_REPORTES': True,

    # Dashboard
    'MESES_DASHBOARD_DEFAULT': 12,
    'ACTUALIZAR_DASHBOARD_SEGUNDOS': 60,
}


# =============================================================================
# CONFIGURACIÓN DE COMPRAS
# =============================================================================
COMPRAS_CONFIG = {
    # Plazos de pago
    'DIAS_PAGO_DEFAULT': 30,
    'DIAS_PAGO_OPCIONES': [15, 30, 45, 60, 90],

    # Alertas
    'DIAS_ALERTA_PAGO': 5,  # Días antes del vencimiento

    # Órdenes de compra
    'PREFIJO_ORDEN_COMPRA': 'OC',
    'REQUIERE_APROBACION': True,
    'MONTO_MINIMO_APROBACION': 50000.00,  # Montos mayores requieren aprobación

    # Recepciones
    'PERMITIR_RECEPCION_PARCIAL': True,
    'DIAS_MAX_RECEPCION': 30,  # Días máximos para recibir después de la OC
}


# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================
SEGURIDAD_CONFIG = {
    # Sesiones
    'TIEMPO_SESION_MINUTOS': 480,  # 8 horas
    'CERRAR_SESION_INACTIVIDAD': True,
    'MINUTOS_INACTIVIDAD': 30,

    # Contraseñas
    'LONGITUD_MINIMA_PASSWORD': 8,
    'REQUIERE_MAYUSCULAS': True,
    'REQUIERE_NUMEROS': True,
    'REQUIERE_ESPECIALES': False,

    # Intentos de login
    'MAX_INTENTOS_LOGIN': 5,
    'BLOQUEO_MINUTOS': 15,

    # Auditoría
    'REGISTRAR_ACCIONES': True,
    'DIAS_RETENER_LOGS': 365,
}


# =============================================================================
# FUNCIÓN HELPER PARA OBTENER CONFIGURACIÓN
# =============================================================================
def get_config_defaults():
    """
    Retorna todos los valores de configuración por defecto.
    Útil para inicializar la configuración de una nueva empresa.
    """
    return {
        'fiscal': DGII_CONFIG.copy(),
        'facturacion': FACTURACION_CONFIG.copy(),
        'inventario': INVENTARIO_CONFIG.copy(),
        'notificaciones': NOTIFICACIONES_CONFIG.copy(),
        'reportes': REPORTES_CONFIG.copy(),
        'compras': COMPRAS_CONFIG.copy(),
        'seguridad': SEGURIDAD_CONFIG.copy(),
    }


def get_config_value(section: str, key: str, default=None):
    """
    Obtiene un valor específico de configuración.

    Args:
        section: Sección de configuración (fiscal, facturacion, etc.)
        key: Clave dentro de la sección
        default: Valor por defecto si no existe

    Returns:
        El valor de configuración o el default
    """
    configs = {
        'fiscal': DGII_CONFIG,
        'facturacion': FACTURACION_CONFIG,
        'inventario': INVENTARIO_CONFIG,
        'notificaciones': NOTIFICACIONES_CONFIG,
        'reportes': REPORTES_CONFIG,
        'compras': COMPRAS_CONFIG,
        'seguridad': SEGURIDAD_CONFIG,
    }

    section_config = configs.get(section, {})
    return section_config.get(key, default)

"""
Permisos personalizados para el módulo DGII

Este módulo define permisos específicos para acciones críticas en el módulo
de comprobantes fiscales, heredando de BaseEmpresaPermission para mantener
consistencia con los estándares del proyecto.
"""
from core.permissions import BaseEmpresaPermission


class CanGenerarNCF(BaseEmpresaPermission):
    """
    Permiso para generar números de comprobante fiscal (NCF).

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.generar_secuenciancf'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.generar_secuenciancf',
            message='No tiene permiso para generar NCF.'
        )


class CanGenerarReporte606(BaseEmpresaPermission):
    """
    Permiso para generar el reporte 606 de compras.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.generar_reporte_606'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.generar_reporte_606',
            message='No tiene permiso para generar el reporte 606.'
        )


class CanGenerarReporte607(BaseEmpresaPermission):
    """
    Permiso para generar el reporte 607 de ventas.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.generar_reporte_607'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.generar_reporte_607',
            message='No tiene permiso para generar el reporte 607.'
        )


class CanGenerarReporte608(BaseEmpresaPermission):
    """
    Permiso para generar el reporte 608 de anulados.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.generar_reporte_608'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.generar_reporte_608',
            message='No tiene permiso para generar el reporte 608.'
        )


class CanGestionarTipoComprobante(BaseEmpresaPermission):
    """
    Permiso para gestionar tipos de comprobantes fiscales.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.gestionar_tipocomprobante'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.gestionar_tipocomprobante',
            message='No tiene permiso para gestionar tipos de comprobante.'
        )


class CanGestionarSecuencia(BaseEmpresaPermission):
    """
    Permiso para gestionar secuencias NCF.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'dgii.gestionar_secuenciancf'
    """

    def __init__(self):
        super().__init__(
            permission_codename='dgii.gestionar_secuenciancf',
            message='No tiene permiso para gestionar secuencias NCF.'
        )

"""
Permisos personalizados para el módulo Cuentas por Pagar

Este módulo define permisos específicos para acciones críticas en el módulo
de cuentas por pagar, heredando de BaseEmpresaPermission para mantener
consistencia con los estándares del proyecto.
"""
from core.permissions import BaseEmpresaPermission


class CanAplicarPago(BaseEmpresaPermission):
    """
    Permiso para aplicar pagos a cuentas por pagar.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_pagar.aplicar_pagoproveedor'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_pagar.aplicar_pagoproveedor',
            message='No tiene permiso para aplicar pagos.'
        )


class CanReversarPago(BaseEmpresaPermission):
    """
    Permiso para reversar pagos a proveedores.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_pagar.reversar_pagoproveedor'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_pagar.reversar_pagoproveedor',
            message='No tiene permiso para reversar pagos.'
        )


class CanAnularCuentaPorPagar(BaseEmpresaPermission):
    """
    Permiso para anular cuentas por pagar.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_pagar.anular_cuentaporpagar'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_pagar.anular_cuentaporpagar',
            message='No tiene permiso para anular cuentas por pagar.'
        )


class CanMarcarVencidas(BaseEmpresaPermission):
    """
    Permiso para marcar cuentas por pagar como vencidas.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_pagar.marcar_vencidas'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_pagar.marcar_vencidas',
            message='No tiene permiso para marcar cuentas como vencidas.'
        )

"""
Permisos personalizados para el módulo Cuentas por Cobrar

Este módulo define permisos específicos para acciones críticas en el módulo
de cuentas por cobrar, heredando de BaseEmpresaPermission para mantener
consistencia con los estándares del proyecto.
"""
from core.permissions import BaseEmpresaPermission


class CanAplicarCobro(BaseEmpresaPermission):
    """
    Permiso para aplicar cobros a cuentas por cobrar.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_cobrar.aplicar_cobrocliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_cobrar.aplicar_cobrocliente',
            message='No tiene permiso para aplicar cobros.'
        )


class CanReversarCobro(BaseEmpresaPermission):
    """
    Permiso para reversar cobros de clientes.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_cobrar.reversar_cobrocliente'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_cobrar.reversar_cobrocliente',
            message='No tiene permiso para reversar cobros.'
        )


class CanAnularCuentaPorCobrar(BaseEmpresaPermission):
    """
    Permiso para anular cuentas por cobrar.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_cobrar.anular_cuentaporcobrar'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_cobrar.anular_cuentaporcobrar',
            message='No tiene permiso para anular cuentas por cobrar.'
        )


class CanMarcarVencidas(BaseEmpresaPermission):
    """
    Permiso para marcar cuentas por cobrar como vencidas.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'cuentas_cobrar.marcar_vencidas'
    """

    def __init__(self):
        super().__init__(
            permission_codename='cuentas_cobrar.marcar_vencidas',
            message='No tiene permiso para marcar cuentas como vencidas.'
        )

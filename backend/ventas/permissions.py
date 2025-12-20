"""
Permisos personalizados para el módulo Ventas

Este módulo define permisos específicos para gestión de ventas
utilizando BaseEmpresaPermission para validar multi-tenancy.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarCotizacion(BaseEmpresaPermission):
    """
    Permiso para gestionar cotizaciones.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_cotizacion'
    - Y pertenece a la misma empresa que la cotización
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_cotizacion',
            message='No tiene permiso para gestionar cotizaciones.'
        )


class CanGestionarFactura(BaseEmpresaPermission):
    """
    Permiso para gestionar facturas.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_factura'
    - Y pertenece a la misma empresa que la factura
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_factura',
            message='No tiene permiso para gestionar facturas.'
        )


class CanGestionarPagoCaja(BaseEmpresaPermission):
    """
    Permiso para gestionar pagos en caja.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_pago_caja'
    - Y pertenece a la misma empresa que el pago
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_pago_caja',
            message='No tiene permiso para gestionar pagos en caja.'
        )


class CanGestionarNotaCredito(BaseEmpresaPermission):
    """
    Permiso para gestionar notas de crédito.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_nota_credito'
    - Y pertenece a la misma empresa que la nota
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_nota_credito',
            message='No tiene permiso para gestionar notas de crédito.'
        )


class CanGestionarNotaDebito(BaseEmpresaPermission):
    """
    Permiso para gestionar notas de débito.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_nota_debito'
    - Y pertenece a la misma empresa que la nota
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_nota_debito',
            message='No tiene permiso para gestionar notas de débito.'
        )


class CanGestionarDevolucionVenta(BaseEmpresaPermission):
    """
    Permiso para gestionar devoluciones de venta.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_devolucion_venta'
    - Y pertenece a la misma empresa que la devolución
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_devolucion_venta',
            message='No tiene permiso para gestionar devoluciones de venta.'
        )


class CanGestionarListaEspera(BaseEmpresaPermission):
    """
    Permiso para gestionar listas de espera.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'ventas.gestionar_lista_espera'
    - Y pertenece a la misma empresa que la lista
    """

    def __init__(self):
        super().__init__(
            permission_codename='ventas.gestionar_lista_espera',
            message='No tiene permiso para gestionar listas de espera.'
        )

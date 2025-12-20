"""
Permisos para el módulo de Caja

Este módulo define las clases de permisos específicos para Caja,
heredando de BaseEmpresaPermission según la Guía Inicial.
"""
from core.permissions.base import BaseEmpresaPermission, BaseModelPermission


class IsCajaOwnerOrAdmin(BaseEmpresaPermission):
    """
    Permiso para acceso a Cajas.

    Permite acceso si:
    - El usuario es superusuario/staff
    - La caja pertenece a la misma empresa del usuario
    """

    def __init__(self):
        super().__init__(
            permission_codename=None,
            message='No tiene permiso para acceder a esta caja.'
        )


class CanManageCaja(BaseEmpresaPermission):
    """
    Permiso para gestionar (crear, editar, eliminar) Cajas.

    Requiere el permiso 'caja.change_caja' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.change_caja',
            message='No tiene permiso para gestionar cajas.'
        )


class CanOpenSession(BaseEmpresaPermission):
    """
    Permiso para abrir sesiones de caja.

    Requiere el permiso 'caja.add_sesioncaja' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.add_sesioncaja',
            message='No tiene permiso para abrir sesiones de caja.'
        )


class CanCloseSession(BaseEmpresaPermission):
    """
    Permiso para cerrar sesiones de caja.

    Requiere el permiso 'caja.change_sesioncaja' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.change_sesioncaja',
            message='No tiene permiso para cerrar sesiones de caja.'
        )


class CanAuditSession(BaseEmpresaPermission):
    """
    Permiso para arquear (auditar) sesiones de caja.

    Requiere el permiso 'caja.arquear_sesioncaja' o ser admin/staff.
    Este es un permiso especial que debe crearse como permiso custom.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.arquear_sesioncaja',
            message='No tiene permiso para arquear sesiones de caja.'
        )


class CanRegisterMovement(BaseEmpresaPermission):
    """
    Permiso para registrar movimientos de caja.

    Requiere el permiso 'caja.add_movimientocaja' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.add_movimientocaja',
            message='No tiene permiso para registrar movimientos de caja.'
        )


class CanDeleteMovement(BaseEmpresaPermission):
    """
    Permiso para eliminar movimientos de caja.

    Requiere el permiso 'caja.delete_movimientocaja' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.delete_movimientocaja',
            message='No tiene permiso para eliminar movimientos de caja.'
        )


class CanViewCajaReports(BaseEmpresaPermission):
    """
    Permiso para ver reportes de caja.

    Requiere el permiso 'caja.view_reports' o ser admin/staff.
    """

    def __init__(self):
        super().__init__(
            permission_codename='caja.view_reports',
            message='No tiene permiso para ver reportes de caja.'
        )

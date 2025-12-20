"""
Permisos personalizados para el módulo Empresas

Este módulo define permisos específicos para acciones críticas en el módulo
de empresas, heredando de BaseEmpresaPermission para mantener consistencia
con los estándares del proyecto.

Nota: Empresa es el modelo raíz del sistema, por lo que los permisos
se basan principalmente en is_superuser/is_staff, no en empresa.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarEmpresa(BaseEmpresaPermission):
    """
    Permiso para gestionar empresas (CRUD).

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'empresas.gestionar_empresa'
    """

    def __init__(self):
        super().__init__(
            permission_codename='empresas.gestionar_empresa',
            message='No tiene permiso para gestionar empresas.'
        )


class CanActualizarConfiguracionFiscal(BaseEmpresaPermission):
    """
    Permiso para actualizar configuración fiscal.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'empresas.actualizar_configuracion_fiscal'
    """

    def __init__(self):
        super().__init__(
            permission_codename='empresas.actualizar_configuracion_fiscal',
            message='No tiene permiso para actualizar configuración fiscal.'
        )


class CanVerEstadisticas(BaseEmpresaPermission):
    """
    Permiso para ver estadísticas de empresa.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'empresas.ver_estadisticas'
    """

    def __init__(self):
        super().__init__(
            permission_codename='empresas.ver_estadisticas',
            message='No tiene permiso para ver estadísticas.'
        )

"""
Permisos personalizados para el módulo Productos

Este módulo define permisos específicos para acciones en el módulo
de productos, heredando de BaseEmpresaPermission para mantener consistencia
con los estándares del proyecto.

Incluye validación de empresa (multi-tenancy) para todos los objetos.
"""
from core.permissions import BaseEmpresaPermission


class CanGestionarCategoria(BaseEmpresaPermission):
    """
    Permiso para gestionar categorías.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'productos.gestionar_categoria'
    - Y pertenece a la misma empresa que la categoría
    """

    def __init__(self):
        super().__init__(
            permission_codename='productos.gestionar_categoria',
            message='No tiene permiso para gestionar categorías.'
        )


class CanGestionarProducto(BaseEmpresaPermission):
    """
    Permiso para gestionar productos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'productos.gestionar_producto'
    - Y pertenece a la misma empresa que el producto
    """

    def __init__(self):
        super().__init__(
            permission_codename='productos.gestionar_producto',
            message='No tiene permiso para gestionar productos.'
        )


class CanCargarCatalogo(BaseEmpresaPermission):
    """
    Permiso para cargar catálogo masivo.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'productos.cargar_catalogo'
    """

    def __init__(self):
        super().__init__(
            permission_codename='productos.cargar_catalogo',
            message='No tiene permiso para cargar catálogo masivo.'
        )


class CanGestionarImagenes(BaseEmpresaPermission):
    """
    Permiso para gestionar imágenes de productos.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'productos.gestionar_imagenproducto'
    - Y pertenece a la misma empresa que la imagen/producto
    """

    def __init__(self):
        super().__init__(
            permission_codename='productos.gestionar_imagenproducto',
            message='No tiene permiso para gestionar imágenes.'
        )


class CanGestionarReferencias(BaseEmpresaPermission):
    """
    Permiso para gestionar referencias cruzadas.

    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'productos.gestionar_referenciascruzadas'
    - Y pertenece a la misma empresa que las referencias
    """

    def __init__(self):
        super().__init__(
            permission_codename='productos.gestionar_referenciascruzadas',
            message='No tiene permiso para gestionar referencias cruzadas.'
        )

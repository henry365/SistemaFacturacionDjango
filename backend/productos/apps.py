"""
Configuración de la aplicación Productos
"""
from django.apps import AppConfig


class ProductosConfig(AppConfig):
    """
    Configuración del módulo Productos.

    Este módulo gestiona el catálogo de productos, categorías,
    imágenes y referencias cruzadas.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'productos'
    verbose_name = 'Gestión de Productos'

    def ready(self):
        """
        Inicialización del módulo.

        Se ejecuta cuando Django carga la aplicación.
        Importa las señales si existen.
        """
        try:
            import productos.signals  # noqa: F401
        except ImportError:
            pass

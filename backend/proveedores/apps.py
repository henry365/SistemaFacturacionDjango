"""
Configuración de la aplicación Proveedores
"""
from django.apps import AppConfig


class ProveedoresConfig(AppConfig):
    """
    Configuración del módulo Proveedores.

    Este módulo gestiona proveedores, sus datos de contacto,
    identificación y relaciones con compras.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proveedores'
    verbose_name = 'Gestión de Proveedores'

    def ready(self):
        """
        Inicialización del módulo.

        Se ejecuta cuando Django carga la aplicación.
        Importa las señales si existen.
        """
        try:
            import proveedores.signals  # noqa: F401
        except ImportError:
            pass

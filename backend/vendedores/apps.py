"""
Configuración del módulo Vendedores
"""
from django.apps import AppConfig


class VendedoresConfig(AppConfig):
    """
    Configuración del módulo Vendedores.

    Este módulo gestiona vendedores, sus datos de contacto,
    comisiones y relaciones con ventas y clientes.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendedores'
    verbose_name = 'Gestión de Vendedores'

    def ready(self):
        """
        Inicialización del módulo.

        Se ejecuta cuando Django carga la aplicación.
        Importa las señales si existen.
        """
        try:
            import vendedores.signals  # noqa: F401
        except ImportError:
            pass

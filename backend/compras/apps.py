"""
Configuración de la aplicación Compras

Este módulo configura la aplicación de Compras para Django,
incluyendo el registro de signals.
"""
from django.apps import AppConfig


class ComprasConfig(AppConfig):
    """Configuración de la app Compras"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compras'
    verbose_name = 'Gestión de Compras'

    def ready(self):
        """
        Método que se ejecuta cuando la app está lista.

        Registra los signals del módulo.
        """
        # Importar signals para registrarlos
        from . import signals  # noqa: F401

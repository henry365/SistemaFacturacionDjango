"""
Configuración de la aplicación Clientes

Este módulo configura la aplicación de Clientes para Django,
incluyendo el registro de signals.
"""
from django.apps import AppConfig


class ClientesConfig(AppConfig):
    """Configuración de la app Clientes"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clientes'
    verbose_name = 'Gestión de Clientes'

    def ready(self):
        """
        Método que se ejecuta cuando la app está lista.

        Registra los signals del módulo.
        """
        # Importar signals para registrarlos
        from . import signals  # noqa: F401

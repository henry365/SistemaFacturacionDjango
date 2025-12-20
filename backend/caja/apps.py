"""
Configuración de la aplicación Caja

Este módulo configura la aplicación de Caja para Django,
incluyendo el registro de signals.
"""
from django.apps import AppConfig


class CajaConfig(AppConfig):
    """Configuración de la app Caja"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caja'
    verbose_name = 'Gestión de Caja'

    def ready(self):
        """
        Método que se ejecuta cuando la app está lista.

        Registra los signals del módulo.
        """
        # Importar signals para registrarlos
        from . import signals  # noqa: F401

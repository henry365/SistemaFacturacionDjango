from django.apps import AppConfig


class EmpresasConfig(AppConfig):
    """Configuración de la aplicación Empresas"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresas'
    verbose_name = 'Empresas'

    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        # Si se implementan señales en el futuro:
        # import empresas.signals  # noqa: F401
        pass

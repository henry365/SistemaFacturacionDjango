from django.apps import AppConfig


class ActivosConfig(AppConfig):
    name = 'activos'
    verbose_name = 'Activos Fijos'

    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        import activos.signals  # noqa: F401

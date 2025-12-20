from django.apps import AppConfig


class DespachosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'despachos'
    verbose_name = 'Despachos'

    def ready(self):
        """Importa señales cuando la app está lista"""
        import despachos.signals  # noqa: F401

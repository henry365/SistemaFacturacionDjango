from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Configuración del Sistema'

    def ready(self):
        # Importar signals para registrarlos
        from . import models  # noqa: F401

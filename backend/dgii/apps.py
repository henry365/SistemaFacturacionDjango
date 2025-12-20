from django.apps import AppConfig


class DgiiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dgii'
    verbose_name = 'DGII - Comprobantes Fiscales'

    def ready(self):
        """Importa señales cuando la app está lista"""
        import dgii.signals  # noqa: F401

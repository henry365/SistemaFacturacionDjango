from django.apps import AppConfig


class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'
    verbose_name = 'Gestión de Ventas'

    def ready(self):
        """Cargar señales cuando la aplicación esté lista."""
        try:
            import ventas.signals  # noqa: F401
        except ImportError:
            pass

from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Configuración de la aplicación Inventario"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'
    verbose_name = 'Inventario'

    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        # Si se implementan señales en el futuro:
        # import inventario.signals  # noqa: F401
        pass

from django.apps import AppConfig


class CuentasPagarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuentas_pagar'
    verbose_name = 'Cuentas por Pagar'

    def ready(self):
        """Importar signals al iniciar la aplicación."""
        from . import signals  # noqa: F401

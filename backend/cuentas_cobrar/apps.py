from django.apps import AppConfig


class CuentasCobrarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuentas_cobrar'
    verbose_name = 'Cuentas por Cobrar'

    def ready(self):
        """Importar signals al iniciar la aplicación."""
        from . import signals  # noqa: F401

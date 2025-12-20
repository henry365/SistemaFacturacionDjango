from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuarios'

    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        import usuarios.signals  # noqa: F401

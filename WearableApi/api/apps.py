"""
App configuration for API.
Registers signals on app ready.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """
        Importar signals cuando la app está lista.
        Esto registra los receivers automáticamente.
        """
        import api.signals  # noqa
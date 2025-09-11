from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures the signals are connected.
        """
        import catalog.signals  # noqa

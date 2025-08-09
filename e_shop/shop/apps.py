from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):  # pragma: no cover
        # Import signals to ensure they are registered
        from . import signals  # noqa: F401

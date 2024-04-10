"""Main app config"""
from django.apps import AppConfig


class MainConfig(AppConfig):
    """Class representing the main app and its config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    # docstr-coverage:excused `config method`
    def ready(self):
        from . import signals

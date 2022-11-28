"""main app config"""
from django.apps import AppConfig


class MainConfig(AppConfig):
    """
    Class representing main app and its
    config.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

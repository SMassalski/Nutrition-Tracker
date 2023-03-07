"""Authentication app configuration."""
from django.apps import AppConfig


class AuthConfig(AppConfig):
    """Class representing the authentication app and it's config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"

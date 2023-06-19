"""Models related to user functionality."""
from django.contrib.auth.models import AbstractUser
from django.db import models

# TODO: Move to authentication app.


class User(AbstractUser):
    """Custom user model for future modification."""

    models.EmailField(
        blank=True, max_length=254, verbose_name="email address", unique=True
    ),

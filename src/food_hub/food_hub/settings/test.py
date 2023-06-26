"""Test settings"""
from .base import *

# For populate_fdc_data command tests: prevents automatic discovery.
del DATA_DIR

# Faster hasher for a speedup of tests using authentication.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

"""Test settings"""
from .base import *

# For load_fdc_data command tests: prevents automatic discovery.
del DATA_DIR

# Faster hasher for a speedup of tests using authentication.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

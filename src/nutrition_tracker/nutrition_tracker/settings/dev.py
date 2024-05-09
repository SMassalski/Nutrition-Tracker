"""Development settings"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = []

# Settings for the debug toolbar
INSTALLED_APPS.append("debug_toolbar")
MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]

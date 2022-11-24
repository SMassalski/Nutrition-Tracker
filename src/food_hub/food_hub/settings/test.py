"""Test settings"""
from tempfile import mkdtemp

# noinspection PyUnresolvedReferences
from .base import *

MEDIA_ROOT = mkdtemp(prefix="django_test_media_")

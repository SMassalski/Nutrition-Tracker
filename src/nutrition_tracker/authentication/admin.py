from core.admin import ProfileInline
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """User model representation in the admin panel."""

    inlines = UserAdmin.inlines + (ProfileInline,)

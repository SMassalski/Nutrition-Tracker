"""main app admin panel configuration"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main import models


class ProfileInline(admin.TabularInline):
    """Admin inline for the profile model."""

    model = models.Profile


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    """User model representation in the admin panel."""

    inlines = UserAdmin.inlines + (ProfileInline,)


@admin.register(models.Nutrient)
class NutrientAdmin(admin.ModelAdmin):
    """Nutrient model representation in the admin panel."""


@admin.register(models.IntakeRecommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """IntakeRecommendation model representation in the admin panel."""

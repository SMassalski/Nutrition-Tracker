"""main app admin panel configuration"""
import main.models.foods
import main.models.user
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main import models


class ProfileInline(admin.TabularInline):
    """Admin inline for the profile model."""

    model = main.models.user.Profile


@admin.register(main.models.user.User)
class CustomUserAdmin(UserAdmin):
    """User model representation in the admin panel."""

    inlines = UserAdmin.inlines + (ProfileInline,)


@admin.register(main.models.foods.Nutrient)
class NutrientAdmin(admin.ModelAdmin):
    """Nutrient model representation in the admin panel."""


@admin.register(main.models.foods.IntakeRecommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """IntakeRecommendation model representation in the admin panel."""

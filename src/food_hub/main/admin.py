"""main app admin panel configuration"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models.functions import Lower
from main import models

# User and Profile


class ProfileInline(admin.TabularInline):
    """Admin inline for the profile model."""

    model = models.Profile


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    """User model representation in the admin panel."""

    inlines = UserAdmin.inlines + (ProfileInline,)


# Nutrient


class NutrientComponentInline(admin.TabularInline):
    """Admin inline for the `NutrientComponent` model."""

    model = models.NutrientComponent
    fk_name = "target"
    extra = 0


@admin.register(models.Nutrient)
class NutrientAdmin(admin.ModelAdmin):
    """Nutrient model representation in the admin panel."""

    inlines = (NutrientComponentInline,)
    ordering = (Lower("name"),)


@admin.register(models.NutrientType)
class NutrientTypeAdmin(admin.ModelAdmin):
    """NutrientType model representation in the admin panel."""


# Recommendation


@admin.register(models.IntakeRecommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """IntakeRecommendation model representation in the admin panel."""

    ordering = (Lower("nutrient__name"), "age_min", "sex")

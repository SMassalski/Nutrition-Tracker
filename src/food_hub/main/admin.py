"""main app admin panel configuration"""
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.urls import path
from main import models
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED

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


# Ingredient


@admin.register(models.FoodDataSource)
class FoodDataSourceAdmin(admin.ModelAdmin):
    """FoodDataSource model representation in the admin panel."""


class IngredientNutrientInline(admin.TabularInline):
    """Admin inline for the `IngredientNutrient` model."""

    model = models.IngredientNutrient
    extra = 0


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ingredient model representation in the admin panel."""

    search_fields = ["name"]
    inlines = (IngredientNutrientInline,)
    ordering = (Lower("name"),)


# Profile


class MealInline(admin.StackedInline):
    """Admin inline for the `Meal` model."""

    model = models.Meal
    extra = 0
    show_change_link = True
    ordering = ("date",)


class RecipeInline(admin.TabularInline):
    """Admin inline for the `Recipe` model."""

    model = models.Recipe
    fields = ("name", "final_weight")
    extra = 0
    show_change_link = True
    ordering = (Lower("name"),)


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile model representation in the admin panel."""

    inlines = (RecipeInline,)
    readonly_fields = ("energy_requirement",)


@admin.register(models.WeightMeasurement)
class WeightMeasurementAdmin(admin.ModelAdmin):
    """WeightMeasurement model representation in the admin panel."""

    search_fields = ["profile__user__username", "date"]
    ordering = ["profile__user__username", "date"]
    list_display = ["date", "user"]
    list_filter = ["date"]
    search_help_text = "Search by profile and date."

    @admin.display(description="Profile", ordering="profile__user__username")
    def user(self, obj):
        """The name of the measurement's profile."""
        return obj.profile.user.username


class MealIngredientInline(admin.TabularInline):
    """Admin inline for the `MealIngredient` model."""

    model = models.MealIngredient
    raw_id_fields = ["ingredient"]
    extra = 1


class MealRecipeInline(admin.TabularInline):
    """Admin inline for the `MealRecipe` model."""

    model = models.MealRecipe
    raw_id_fields = ["recipe"]
    extra = 1


@admin.register(models.Meal)
class MealAdmin(admin.ModelAdmin):
    """Meal model representation in the admin panel."""

    search_fields = ["owner__user__username", "date"]
    ordering = [Lower("owner__user__username"), "date"]
    list_display = ["date", "user"]
    inlines = [MealIngredientInline, MealRecipeInline]
    list_filter = ["date"]
    search_help_text = "Search by owner and date."

    class Media:
        js = ["bundle.js"]

    @admin.display(description="Owner", ordering="owner__user__username")
    def user(self, obj):
        """The name of the meal's owner."""
        return obj.owner.user.username

    # docstr-coverage: inherited
    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path(
                "empty_meals/",
                self.admin_site.admin_view(self.clear_empty_meals),
                name="empty-meals",
            )
        ]
        return new_urls + urls

    def clear_empty_meals(self, request, **kwargs):
        """
        Delete meals without ingredients or recipes and are not in
        any of the users' sessions.
        """
        if request.method.lower() != "delete":
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)

        if not self.has_delete_permission(request):
            raise PermissionDenied

        call_command("clearemptymeals")
        self.message_user(
            request, "Empty meals removed.", messages.SUCCESS, fail_silently=True
        )
        return HttpResponse(headers={"HX-Refresh": "true"})


class RecipeIngredientInline(admin.TabularInline):
    """Admin inline for the `RecipeIngredient` model."""

    model = models.RecipeIngredient
    raw_id_fields = ["ingredient"]
    extra = 0


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Recipe model representation in the admin panel."""

    search_fields = ["owner__user__username", "name"]
    list_display = ["name", "user"]
    readonly_fields = ["slug"]
    inlines = [RecipeIngredientInline]
    search_help_text = "Search by owner and name."

    @admin.display(description="Owner", ordering="owner__user__username")
    def user(self, obj):
        """The name of the recipe's owner."""
        return obj.owner.user.username

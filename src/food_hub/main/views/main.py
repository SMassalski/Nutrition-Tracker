"""Main app's regular views"""
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from main import models

from .session_util import is_meal_expired, ping_meal_interact


class ProfileView(TemplateView):
    """
    View for setting up a user profile for intake recommendation
    calculations.
    Passes the 'next' query param value to the response data.
    The query param field name can be changed by setting the
    `redirect_url_field` attribute.
    """

    redirect_url_field = "next"
    template_name = "main/profile.html"

    # docstr-coverage: inherited
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["next"] = self.request.GET.get(self.redirect_url_field)
        return data


class MealView(TemplateView):
    """View for viewing, creating and editing meals.

    This class only handles the layout and current meal management.
    """

    template_name = "main/meal.html"

    # docstr-coverage: inherited
    def get(self, request, *args, **kwargs) -> HttpResponse:

        response = super().get(request, *args, **kwargs)

        # Retrieve or create the current meal. Check if expired.
        meal_id = self.request.session.get("meal_id")

        if (
            meal_id is None
            or is_meal_expired(self.request)
            or not models.Meal.objects.filter(pk=meal_id).exists()
        ):
            meal = models.Meal.objects.get_or_create(
                owner=self.request.user.profile, date=timezone.now().date()
            )[0]
            self.request.session["meal_id"] = meal.id

        ping_meal_interact(self.request)

        return response


class RecipeEditView(TemplateView):
    """View for viewing and modifying recipes.

    Selects the recipe based on the slug and the request profile.
    """

    template_name = "main/recipe_edit.html"

    # docstr-coverage: inherited
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get("slug")
        context["recipe"] = models.Recipe.objects.get(
            slug=slug, owner=self.request.user.profile
        )

        return context

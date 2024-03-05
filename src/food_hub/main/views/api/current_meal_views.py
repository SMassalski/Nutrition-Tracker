"""Views for operations related to session 'current meal' functionality.
"""
from datetime import date

from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
from main import models, serializers
from main.views.mixins import MealInteractionMixin
from main.views.session_util import get_current_meal_id
from rest_framework.generics import CreateAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

__all__ = ("CurrentMealRedirectView", "CurrentMealView")


class CurrentMealRedirectView(RedirectView):
    """Redirect to the view endpoint for the current meal."""

    # docstr-coverage: inherited
    def get_redirect_url(self, *args, **kwargs):
        meal_id = get_current_meal_id(self.request, True)
        kwargs["meal"] = meal_id
        return super().get_redirect_url(*args, **kwargs)


class CurrentMealView(MealInteractionMixin, RetrieveModelMixin, CreateAPIView):
    """View allowing the user to change the current meal.

    The current meal selection effects the information displayed and
    modified at the `meal` endpoint.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = serializers.CurrentMealSerializer
    template_name = "main/data/current_meal.html"

    # docstr-coverage: inherited
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["owner_id"] = self.request.user.profile.id
        return context

    # docstr-coverage: inherited
    def get_object(self):
        meal_id = get_current_meal_id(self.request, True)
        return get_object_or_404(models.Meal, pk=meal_id)

    def get(self, request, *args, **kwargs):
        """Get the current meal's data."""
        response = self.retrieve(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            response.data["date_obj"] = date.fromisoformat(response.data.get("date"))

        return response

    def post(self, request, *args, **kwargs):
        """Set the current meal by date."""
        response = super().post(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            response.data["date_obj"] = date.fromisoformat(response.data.get("date"))

        # Session update
        request.session["meal_id"] = response.data.get("id")

        response.headers["HX-Trigger"] = "currentMealChanged"

        return response

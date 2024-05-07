"""Views for operations related to session 'current meal' functionality.
"""
from datetime import timedelta

from core import models, serializers
from core.views.generics import CreateAPIView
from core.views.mixins import HTMXEventMixin, MealInteractionMixin, RetrieveModelMixin
from core.views.session_util import get_current_meal_id
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.status import is_success

__all__ = ("CurrentMealRedirectView", "CurrentMealView")


class CurrentMealRedirectView(RedirectView):
    """Redirect to the view endpoint for the current meal."""

    # docstr-coverage: inherited
    def get_redirect_url(self, *args, **kwargs):
        meal_id = get_current_meal_id(self.request, True)
        kwargs["meal"] = meal_id
        return super().get_redirect_url(*args, **kwargs)


class CurrentMealView(
    HTMXEventMixin, MealInteractionMixin, RetrieveModelMixin, CreateAPIView
):
    """View allowing the user to change the current meal.

    The current meal selection effects the information displayed and
    modified at the `meal` endpoint.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = serializers.CurrentMealSerializer
    template_name = "core/data/current_meal.html"
    htmx_events = ["currentMealChanged"]

    # docstr-coverage: inherited
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user.profile)

    # docstr-coverage: inherited
    def get_object(self):
        meal_id = get_current_meal_id(self.request, True)
        return get_object_or_404(models.Meal, pk=meal_id)

    # docstr-coverage: inherited
    def get_template_context(self, data):
        ret = {}
        if "obj" in data:
            date = data["obj"].date
            ret["yesterday"] = str(date - timedelta(days=1))
            ret["tomorrow"] = str(date + timedelta(days=1))

        return ret

    def get(self, request, *args, **kwargs):
        """Get the current meal's data."""
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Set the current meal by date."""
        response = super().post(request, *args, **kwargs)

        # Session update
        if is_success(response.status_code):
            request.session["meal_id"] = response.data["obj"].id

        return response

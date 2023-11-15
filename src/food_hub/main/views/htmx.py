"""Main app's HTMX API views."""
from datetime import date

from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView
from main import models, serializers
from main.models import Ingredient, MealIngredient
from main.permissions import IsMealComponentOwnerPermission, IsMealOwnerPermission
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.status import HTTP_200_OK, is_success

from .session_util import get_current_meal_id, ping_meal_interact

UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class MealInteractionMixin:
    """Mixin that updates the last meal interaction on each request."""

    # docstr-coverage: inherited
    def finalize_response(self, request, response, *args, **kwargs):
        ping_meal_interact(request)
        return super().finalize_response(request, response, *args, **kwargs)


class MealEditMixin(MealInteractionMixin):
    """Mixin for views that modify a meal's components.

    Adds the `mealComponentsChanged` HTMX trigger header to responses to
    requests with unsafe methods.
    """

    # docstr-coverage: inherited
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if is_success(response.status_code) and request.method in UNSAFE_METHODS:
            response["HX-Trigger"] = _update_header_str(
                response.get("HX-Trigger"), "mealComponentsChanged"
            )
        return response


class CurrentMealRedirectView(RedirectView):
    """Redirect to the view endpoint for the current meal."""

    # docstr-coverage: inherited
    def get_redirect_url(self, *args, **kwargs):
        meal_id = get_current_meal_id(self.request, True)
        kwargs["meal_id"] = meal_id
        return super().get_redirect_url(*args, **kwargs)


class MealIngredientView(MealEditMixin, ListCreateAPIView):
    """View for adding foods to a meal."""

    template_name = "main/data/meal_ingredient_list.html"
    table_row_template = "main/data/meal_ingredient_table_row.html"

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = serializers.MealIngredientSerializer
    permission_classes = [IsMealOwnerPermission]
    lookup_url_kwarg = "meal_id"

    # docstr-coverage: inherited
    def get_queryset(self):
        pk = self.kwargs["meal_id"]
        # Reverse order allows pagination and appending element
        # features together without additional complexity.
        return (
            MealIngredient.objects.filter(meal__id=pk)
            .select_related("ingredient")
            .order_by("-id")
        )

    # docstr-coverage: inherited
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["meal_id"] = self.kwargs["meal_id"]
        return context

    def get_template_names(self):
        """Select the template to be used.

        The selection is based on the request method.

        Returns
        -------
        List[str]
        """
        if self.request.method == "POST":
            return [self.table_row_template]
        else:
            return [self.template_name]


class MealIngredientDetailView(MealEditMixin, RetrieveUpdateDestroyAPIView):
    """
    View for retrieve, update and delete operations on MealIngredients.
    """

    queryset = MealIngredient.objects.select_related("ingredient")
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = serializers.MealIngredientSerializer
    permission_classes = [IsMealComponentOwnerPermission]

    template_query_param = "template"

    template_name = "main/data/meal_ingredient_table_row.html"
    form_template_name = "main/data/meal_ingredient_row_form.html"

    def get_template_names(self):
        """Select the template to be used.

        The selection is based on the request method and the
        `template_query_param`.

        Returns
        -------
        List[str]
        """
        if self.request.method == "GET":
            template_type = self.request.GET.get(self.template_query_param)
            if template_type and template_type.lower() == "form":
                return [self.form_template_name]
        return [self.template_name]

    def delete(self, *args, **kwargs):
        """Delete a meal ingredient"""
        super().delete(*args, **kwargs)
        # HTMX does not perform a swap when the response has a
        # no content (204) status.
        # NOTE: Using the usual rest_framework.response.Response
        #   caused a NoReverseMatch exception (for some reason arguments
        #   are removed).
        return HttpResponse(status=HTTP_200_OK)


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


class IngredientPreviewView(RetrieveAPIView):
    """Ingredient preview (selected ingredient information)."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientPreviewSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "main/data/ingredient_preview.html"

    def get(self, request, *args, **kwargs):
        """Retrieve ingredient preview data."""
        response = super().get(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            response.data["meal_id"] = get_current_meal_id(self.request, True)

        return response


class MealNutrientIntakeView(ListAPIView):
    """View for displaying the meal's dietary intakes.

    Attributes
    ----------
    display_order: Iterable[str]
        The names of NutrientTypes to be included in the `nutrient_data`
        context var (in that order). Default: ("Vitamin", "Mineral",
        "Fatty acid type", "Amino acid")
    no_recommendations: Iterable[str]
        The names of Nutrients to display even if they don't have
        a recommendation. Default: ['Polyunsaturated fatty acids',
        'Monounsaturated fatty acids']
    skip_amdr: Iterable[str]
        The names of Nutrients for which to skip recommendation entries
        that have an 'AMDR' `dri_type`. Default: ["Linoleic acid",
        "alpha-Linolenic acid"]
    """

    serializer_class = serializers.NutrientIntakeSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    pagination_class = None
    template_name = "main/data/nutrient_tables.html"
    permission_classes = [IsMealOwnerPermission]
    lookup_url_kwarg = "meal_id"

    display_order = (
        "Vitamin",
        "Mineral",
        "Fatty acid type",
        "Amino acid",
    )

    no_recommendations = [
        "Polyunsaturated fatty acids",
        "Monounsaturated fatty acids",
    ]

    skip_amdr = ["Linoleic acid", "alpha-Linolenic acid"]

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        self._meal = None
        super().__init__(*args, **kwargs)

    # docstr-coverage: inherited
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["meal"] = self._meal
        context["display_order"] = self.display_order

        return context

    # docstr-coverage: inherited
    def get_queryset(self):
        queryset = (
            models.Nutrient.objects.exclude(
                ~Q(name__in=self.no_recommendations), recommendations=None
            )
            .select_related("energy", "child_type")
            .prefetch_related(
                "types",
                Prefetch(
                    "recommendations",
                    queryset=models.IntakeRecommendation.objects.for_profile(
                        self._meal.owner
                    ).exclude(
                        dri_type=models.IntakeRecommendation.AMDR,
                        nutrient__name__in=self.skip_amdr,
                    ),
                ),
            )
        )
        return queryset

    def get(self, *args, **kwargs):
        """List nutrient intakes grouped by type.

        Includes intake information from the selected meal.
        """
        # Avoid repeated lookups in get_serializer_context() and
        # get_queryset().
        self._meal = get_object_or_404(
            models.Meal, pk=self.kwargs.get(self.lookup_url_kwarg)
        )
        response = super().get(*args, **kwargs)
        if not isinstance(response.data, dict):
            response.data = {"results": response.data}

        return response


def _update_header_str(header: str, value: str) -> str:
    """Add the `value` to the `header` in a form readable by htmx"""
    if not header:
        return value
    return ", ".join(header.split(", ") + [value])

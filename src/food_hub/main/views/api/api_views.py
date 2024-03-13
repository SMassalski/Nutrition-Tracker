"""Main app's api views."""
from datetime import date, timedelta

from django.db.models import Prefetch
from django.db.models.functions import Lower
from django.http import Http404
from main import models, serializers
from main.models.foods import Ingredient, Nutrient
from main.views.generics import (
    GenericView,
    GenericViewSet,
    ListAPIView,
    ModelViewSet,
    RetrieveAPIView,
)
from main.views.mixins import (
    CreateModelMixin,
    HTMXEventMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from main.views.session_util import get_current_meal_id
from rest_framework.decorators import action, api_view, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.mixins import DestroyModelMixin
from rest_framework.renderers import (
    BrowsableAPIRenderer,
    JSONRenderer,
    TemplateHTMLRenderer,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

__all__ = (
    "api_root",
    "IngredientView",
    "IngredientDetailView",
    "NutrientView",
    "NutrientDetailView",
    "IngredientPreviewView",
    "MealIngredientPreviewView",
    "MealRecipePreviewView",
    "WeightMeasurementViewSet",
    "ProfileApiView",
    "LastMonthIntakeView",
    "TrackedNutrientViewSet",
)


# TODO: Remove unused views
@api_view(["GET"])
@renderer_classes([BrowsableAPIRenderer, JSONRenderer])
def api_root(request, format=None):
    """Browsable API root"""
    return Response(
        {
            "Ingredients": reverse("ingredient-list", request=request),
            "Nutrients": reverse("nutrient-list", request=request),
        }
    )


class IngredientView(ListAPIView):
    """List of ingredients.

    Include a query in the `search` query parameter to only
    list the ingredients with matching names.
    """

    queryset = Ingredient.objects.order_by("name")
    serializer_class = serializers.IngredientSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]
    template_name = "main/data/component_search_result_list.html"

    # docstr-coverage: inherited
    def get_template_context(self, data):
        target = self.request.GET.get("target", "").lower()
        preview_url_name = (
            "recipe-ingredient-preview"
            if target == "recipe"
            else "meal-ingredient-preview"
        )
        return {"obj_type": "ingredients", "preview_url_name": preview_url_name}


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]


class NutrientView(ListAPIView):
    """List of nutrients."""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientSerializer


class NutrientDetailView(RetrieveAPIView):
    """Nutrient details."""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientDetailSerializer


class IngredientPreviewView(RetrieveAPIView):
    """Ingredient preview (selected ingredient information)."""

    queryset = Ingredient.objects.all()
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "main/data/preview.html"

    refresh_event = None
    component_field = "ingredient"

    # docstr-coverage: inherited
    def get_template_context(self, data):
        calories = data["obj"].calories
        total = sum(calories.values())
        calories = {nutrient: val * 100 / total for nutrient, val in calories.items()}

        return {"component_field": self.component_field, "calories": calories}


class MealIngredientPreviewView(IngredientPreviewView):
    """View for displaying an ingredient's preview.

    A template response includes the id of the meal the form will add
    the ingredient to.
    """

    target_pattern = "meal-ingredient-list"
    refresh_event = "currentMealChanged"

    # docstr-coverage: inherited
    def get_template_context(self, data):
        ret = super().get_template_context(data)
        ret["refresh_event"] = self.refresh_event

        meal_id = get_current_meal_id(self.request, True)
        ret["target_url"] = (
            reverse(self.target_pattern, args=(meal_id,))
            if self.target_pattern
            else None
        )
        return ret


class MealRecipePreviewView(MealIngredientPreviewView):
    """View for displaying recipe previews in the context of a meal."""

    queryset = models.Recipe.objects.all()
    target_pattern = "meal-recipe-list"
    component_field = "recipe"


class WeightMeasurementViewSet(ModelViewSet):
    """Add weight measurements to the user's profile."""

    serializer_class = serializers.WeightMeasurementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    list_template = "main/data/weight_measurement_list.html"
    row_template = "main/data/weight_measurement_list_row.html"
    row_form_template = "main/data/weight_measurement_list_form_row.html"
    modal_template = "main/modals/add_weight_measurement.html"
    add_template = "main/data/weight_measurement_add.html"

    template_name = row_template

    template_map = {
        "list": list_template,
        "retrieve": {"form": row_form_template, "default": row_template},
        "create": {"modal": modal_template, "default": add_template},
        "update": row_template,
        "partial_update": row_template,
        "destroy": "main/blank.html",
    }

    # docstr-coverage: inherited
    def get_queryset(self):
        return models.WeightMeasurement.objects.filter(
            profile=self.request.user.profile
        ).order_by("-id")

    # docstr-coverage: inherited
    def get_fail_headers(self, data):
        headers = super().get_success_headers(data)

        if self.action == "create":
            if self.template == "modal":
                headers["HX-Reselect"] = "#add-weight-measurement"
                headers["HX-Reswap"] = "outerHTML"
            else:
                headers["HX-Reswap"] = "innerHTML"

        return headers

    # docstr-coverage: inherited
    def get_template_context(self, data):
        ret = {}
        if self.action == "create":
            ret["success"] = data["serializer"].is_valid()
        return ret


class ProfileApiView(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericView
):
    """
    View allowing users to perform create, update and retrieve
    operations on the `Profile` model.
    """

    serializer_class = serializers.ProfileSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "main/data/profile_information_form.html"

    redirect_url_field = "next"

    # docstr-coverage: inherited
    def get_object(self):
        return self.request.user.profile

    # docstr-coverage: inherited
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # docstr-coverage: inherited
    def get_template_context(self, data):
        method = self.request.method.lower()
        ret_data = {}
        if method == "get":
            redirect_url = self.request.GET.get(self.redirect_url_field)
            if redirect_url:
                ret_data["next"] = redirect_url

        elif method in ("post", "patch"):
            ret_data["success"] = data["serializer"].is_valid()

        return ret_data

    # docstr-coverage: inherited
    def get_success_headers(self, data):
        ret = super().get_success_headers(data)

        redirect_url = self.request.GET.get(self.redirect_url_field)
        if self.request.method.lower() == "post" and redirect_url:
            ret.update({"HX-Redirect": redirect_url})

        return ret

    def get(self, request, *args, **kwargs):
        """Retrieve the current user's profile data."""
        try:
            response = super().retrieve(request, *args, **kwargs)
        except models.Profile.DoesNotExist:
            if not self.uses_template_renderer:
                raise Http404
            response = Response(self.get_template_context({}))

        return response

    def post(self, request, *args, **kwargs):
        """Create the current user's profile.

        Supports redirect after success if the `next` query param is
        provided.
        The query param name can be changed by setting the
        view's `redirect_url_field` attribute.
        """
        return self.create(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Update the current user's profile."""
        return self.partial_update(request, *args, **kwargs)


class LastMonthIntakeView(RetrieveAPIView):
    """
    List intakes of a nutrient by date from the last 30 days.
    """

    serializer_class = serializers.ByDateIntakeSerializer
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)

    # docstr-coverage: inherited
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["date_min"] = date.today() - timedelta(days=30)
        ctx["date_max"] = date.today()
        return ctx

    # docstr-coverage: inherited
    def get_queryset(self):
        return models.Nutrient.objects.prefetch_related(
            Prefetch(
                "recommendations",
                queryset=models.IntakeRecommendation.objects.for_profile(
                    self.request.user.profile
                ),
            )
        )


class TrackedNutrientViewSet(
    HTMXEventMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet
):
    """View set for operations on the profile's tracked nutrients."""

    renderer_classes = (TemplateHTMLRenderer, JSONRenderer)
    serializer_class = serializers.TrackedNutrientSerializer
    template_name = "main/data/tracked_nutrients_card.html"
    pagination_class = None
    htmx_events = ["trackedNutrientsChanged"]

    template_map = {
        "create": "main/data/tracked_nutrient_list_row.html",
        "list": {"list": "main/data/tracked_nutrient_list.html"},
        "form": {
            "add": "main/data/tracked_nutrient_list.html",
            "default": "main/components/tracked_nutrients_row_form.html",
        },
    }

    # docstr-coverage: inherited
    def get_queryset(self):
        profile = self.request.user.profile
        queryset = models.Profile.tracked_nutrients.through.objects.filter(
            profile=profile
        ).select_related("nutrient")
        return queryset

    # docstr-coverage: inherited
    def perform_create(self, serializer):
        profile = self.request.user.profile
        serializer.save(profile=profile)

    @action(detail=False, methods=["get"], renderer_classes=[TemplateHTMLRenderer])
    def form(self, request, *args, **kwargs):
        """Display the 'add tracked nutrient' row form."""
        if self.template == "add":
            # Without `results` the template is just the 'add button' row
            return Response()

        nutrients = models.Nutrient.objects.exclude(
            tracking_profiles=self.request.user.profile
        ).order_by(Lower("name"))
        return Response({"nutrients": nutrients})

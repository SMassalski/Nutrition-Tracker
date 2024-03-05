"""Main app's api views."""
from datetime import date, datetime, timedelta

from django.db.models import Prefetch
from django.db.models.functions import Lower
from django.http import Http404
from main import models, serializers
from main.models.foods import Ingredient, Nutrient
from main.views.mixins import HTMXEventMixin
from main.views.session_util import get_current_meal_id
from rest_framework.decorators import action, api_view, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.renderers import (
    BrowsableAPIRenderer,
    JSONRenderer,
    TemplateHTMLRenderer,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet, ModelViewSet

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

    def get(self, *args, **kwargs):
        """List ingredients."""
        response = super().get(*args, **kwargs)
        response.data["obj_type"] = "ingredients"
        return response


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, TemplateHTMLRenderer]


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
    serializer_class = serializers.IngredientPreviewSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "main/data/preview.html"

    refresh_event = None
    component_field = "ingredient"

    def get(self, request, *args, **kwargs):
        """Retrieve ingredient preview data."""
        response = super().get(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):

            response.data["component_field"] = self.component_field

        return response


class MealIngredientPreviewView(IngredientPreviewView):
    """View for displaying an ingredient's preview.

    A template response includes the id of the meal the form will add
    the ingredient to.
    """

    target_pattern = "meal-ingredient-list"
    refresh_event = "currentMealChanged"

    # docstr-coverage: inherited
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            meal_id = get_current_meal_id(self.request, True)
            response.data["target_url"] = (
                reverse(self.target_pattern, args=(meal_id,))
                if self.target_pattern
                else None
            )
            response.data["refresh_event"] = self.refresh_event

        return response


class MealRecipePreviewView(MealIngredientPreviewView):
    """View for displaying recipe previews in the context of a meal."""

    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipePreviewSerializer
    target_pattern = "meal-recipe-list"
    component_field = "recipe"


class WeightMeasurementViewSet(ModelViewSet):
    """Add weight measurements to the user's profile."""

    serializer_class = serializers.WeightMeasurementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    template_query_param = "template"
    list_template = "main/data/weight_measurement_list.html"
    row_template = "main/data/weight_measurement_list_row.html"
    row_form_template = "main/data/weight_measurement_list_form_row.html"
    modal_template = "main/modals/add_weight_measurement.html"
    add_template = "main/data/weight_measurement_add.html"

    template_name = row_template

    # docstr-coverage: inherited
    def get_template_names(self):
        template_type = self.request.GET.get(self.template_query_param)
        if self.action == "list":
            return [self.list_template]

        if self.action == "retrieve":
            if template_type and template_type.lower() == "form":
                return [self.row_form_template]
            else:
                return [self.row_template]

        if self.action == "create":
            if template_type and template_type.lower() == "modal":
                return [self.modal_template]
            return [self.add_template]

        if self.action in ("update", "partial_update"):
            return [self.row_template]

        return [self.template_name]

    # docstr-coverage: inherited
    def get_queryset(self):
        return models.WeightMeasurement.objects.filter(
            profile=self.request.user.profile
        ).order_by("-id")

    # docstr-coverage: inherited
    def create(self, request, *args, **kwargs):
        if not isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        headers = {}
        data = {"success": False, "serializer": serializer}
        if serializer.is_valid(raise_exception=False):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            data["success"] = True
            data["datetime"] = datetime.fromisoformat(serializer.data["time"])
            status = HTTP_201_CREATED

        else:
            template_type = self.request.GET.get(self.template_query_param)
            if template_type and template_type.lower() == "modal":
                headers["HX-Reselect"] = "#add-weight-measurement"
                headers["HX-Reswap"] = "outerHTML"
            else:
                headers["HX-Reswap"] = "innerHTML"

            status = HTTP_400_BAD_REQUEST

        data.update(serializer.data)
        return Response(data, status=status, headers=headers)

    # docstr-coverage: inherited
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            for entry in response.data["results"]:
                entry["datetime"] = datetime.fromisoformat(entry["time"])

        return response

    # docstr-coverage: inherited
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            response.data["datetime"] = datetime.fromisoformat(response.data["time"])

        return response

    # docstr-coverage: inherited
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            response.data["datetime"] = datetime.fromisoformat(response.data["time"])

        return response


class ProfileApiView(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericAPIView
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

    def get(self, request, *args, **kwargs):
        """Retrieve the current user's profile data."""
        try:
            response = super().retrieve(request, *args, **kwargs)
        except models.Profile.DoesNotExist:
            if not isinstance(request.accepted_renderer, TemplateHTMLRenderer):
                raise Http404
            response = Response({})

        redirect_url = request.GET.get(self.redirect_url_field)
        if redirect_url:
            response.data["next"] = redirect_url
        return response

    def post(self, request, *args, **kwargs):
        """Create the current user's profile.

        Supports redirect after success if the `next` query param is
        provided.
        The query param name can be changed by setting the
        view's `redirect_url_field` attribute.
        """
        if not isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            return super().create(request, *args, **kwargs)

        headers = {}
        data = {}
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            status = HTTP_201_CREATED
            data["success"] = True

            redirect_url = request.GET.get(self.redirect_url_field)
            if redirect_url:
                headers["HX-Redirect"] = redirect_url

        else:
            status = HTTP_400_BAD_REQUEST

        data.update(serializer.data)
        return Response(data, status=status, headers=headers)

    def patch(self, request, *args, **kwargs):
        """Update the current user's profile."""
        response = super().partial_update(request, *args, **kwargs)
        response.data["success"] = True
        return response


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

    # docstr-coverage: inherited
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = {"results": response.data}
        return response

    # docstr-coverage: inherited
    def get_template_names(self):

        query_template = self.request.GET.get("template")

        if self.action == "create":
            return ["main/data/tracked_nutrient_list_row.html"]

        if self.action == "list":
            if query_template == "list":
                return ["main/data/tracked_nutrient_list.html"]
            return [self.template_name]

        if self.action == "form":
            if query_template == "add":
                return ["main/data/tracked_nutrient_list.html"]
            return ["main/components/tracked_nutrients_row_form.html"]

        return [self.template_name]

    @action(detail=False, methods=["get"], renderer_classes=[TemplateHTMLRenderer])
    def form(self, request, *args, **kwargs):
        """Display the 'add tracked nutrient' row form."""
        if self.request.GET.get("template") == "add":
            # Without `results` the template is just the 'add button' row
            return Response()

        nutrients = models.Nutrient.objects.exclude(
            tracking_profiles=self.request.user.profile
        ).order_by(Lower("name"))
        return Response({"nutrients": nutrients})

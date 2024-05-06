"""Views for operations on `Profile` and related model."""
from datetime import date, timedelta

from django.db.models import Prefetch
from django.db.models.functions import Lower
from django.http import Http404
from main import models, serializers
from main.permissions import (
    CreateWithoutProfilePermission,
    HasProfilePermission,
    IsOwnerPermission,
)
from main.renderers import BrowsableAPIRenderer
from main.views.generics import (
    GenericView,
    GenericViewSet,
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
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse

__all__ = (
    "LastMonthIntakeView",
    "ProfileApiView",
    "TrackedNutrientViewSet",
    "WeightMeasurementViewSet",
    "LastMonthCalorieView",
    "MalconsumptionView",
)


class WeightMeasurementViewSet(HTMXEventMixin, ModelViewSet):
    """CRUD operations on weight measurements."""

    serializer_class = serializers.WeightMeasurementSerializer
    detail_serializer_class = serializers.WeightMeasurementDetailSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]
    htmx_events = ["weightChanged"]
    permission_classes = [IsOwnerPermission, HasProfilePermission]

    list_template = "main/data/weight_measurement_list.html"
    row_template = "main/data/weight_measurement_list_row.html"
    row_form_template = "main/data/weight_measurement_list_form_row.html"
    modal_template = "main/modals/add_weight_measurement_modal.html"

    template_name = row_template

    template_map = {
        "list": list_template,
        "retrieve": {"form": row_form_template, "default": row_template},
        "create": {"modal": modal_template, "default": row_template},
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
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

    # docstr-coverage: inherited
    def get_fail_headers(self, data):
        headers = super().get_success_headers(data)

        if self.action == "create":
            if self.template == "modal":
                headers["HX-Reselect"] = "#add-weight-measurement"
                headers["HX-Reswap"] = "outerHTML"
            else:
                headers["HX-Reswap"] = "none"

        return headers

    # docstr-coverage: inherited
    def get_template_context(self, data):
        ret = {}
        if self.action == "create":
            ret["success"] = data["serializer"].is_valid()
        return ret

    @action(
        methods=["get"],
        detail=False,
        renderer_classes=[JSONRenderer, BrowsableAPIRenderer],
    )
    def last_month_weights(self, request, *_args, **_kwargs):
        """
        List the average weight measurement value for each day with at
        least one measurement, within the last 30 days.
        """
        weights = request.user.profile.weight_by_date(
            date_max=date.today(), date_min=date.today() - timedelta(days=30)
        )
        data = {k.strftime("%b %d"): round(v, 1) for k, v in weights.items()}

        return Response(data)


class ProfileApiView(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericView
):
    """
    Create, update or retrieve the user's profile.
    """

    serializer_class = serializers.ProfileSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]
    template_name = "main/data/profile_information_form.html"

    # Creating a profile by a user, that already has one, would be
    # prevented in validation by nature of the user-profile relation
    # being a one-to-one relation. The permission is here to hide the
    # creation form in the DRF browsable API.
    permission_classes = [CreateWithoutProfilePermission, IsAuthenticated]

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
    permission_classes = [HasProfilePermission]

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


class LastMonthCalorieView(RetrieveAPIView):
    """
    List caloric contribution of nutrients by date from the last 30 days.
    """

    serializer_class = serializers.ByDateCalorieSerializer
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)
    permission_classes = [HasProfilePermission]

    # docstr-coverage: inherited
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["date_min"] = date.today() - timedelta(days=30)
        ctx["date_max"] = date.today()
        return ctx

    # docstr-coverage: inherited
    def get_object(self):
        return self.request.user.profile


class TrackedNutrientViewSet(
    HTMXEventMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet
):
    """View set for operations on the profile's tracked nutrients."""

    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)
    serializer_class = serializers.TrackedNutrientSerializer
    template_name = "main/data/tracked_nutrients_card.html"
    pagination_class = None
    htmx_events = ["trackedNutrientsChanged"]

    # Unowned objects are hidden through queryset filtering,
    # so IsOwnerPermission isn't necessary
    permission_classes = [HasProfilePermission]

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


class MalconsumptionView(GenericView):
    """List under- and overconsumed nutrients and the degree.

    Attributes
    ---------
    exclude: Iterable
        Names of nutrients to exclude from the results.
    """

    template_name = "main/data/malconsumption_cards.html"
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]
    exclude = None
    permission_classes = [HasProfilePermission]

    # docstr-coverage: inherited
    def get_queryset(self):
        profile = self.request.user.profile
        date_min = date.today() - timedelta(days=30)
        malconsumptions = profile.malnutrition(date_min=date_min)

        nutrients = models.Nutrient.objects.exclude(name__in=self.exclude or [])
        data = [
            {
                "id": n.id,
                "nutrient_url": reverse(
                    "nutrient-detail", args=[n.id], request=self.request
                ),
                "name": n.name,
                "magnitude": malconsumptions[n.id],
            }
            for n in nutrients
            if n.id in malconsumptions
        ]

        return sorted(list(data), key=lambda t: t["magnitude"], reverse=True)

    def get(self, request, *args, **kwargs):
        """List under- and overconsumed nutrients."""

        data = self.get_queryset()

        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)

        return Response(data)

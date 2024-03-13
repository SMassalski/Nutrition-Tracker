"""API views intended for use only through inheritance."""
from functools import cached_property

from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from main import models, permissions, serializers
from main.views.generics import ListAPIView, ModelViewSet
from main.views.mixins import HTMXEventMixin
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

__all__ = ("ComponentCollectionViewSet", "NutrientIntakeView")


class ComponentCollectionViewSet(HTMXEventMixin, ModelViewSet):
    """A viewset base class for component collections.

    Component collection view sets provide an api for models that have
    a many-to-many relation with another model in a hierarchical fashion
    i.e., a collection model entry contains many component model
    entries.

    The serializer class must be a serializer for the relation's
    'through' model.

    Setting the `queryset`, `permission_classes` and `template_name`
    attributes will not work without overriding their respective
    methods.

    Attributes
    ----------
    collection_model: django.db.models.Model
    component_field_name: str
        The name of the collection model's field referencing the
        component model.
    htmx_events: List[str]
        The HTMX events that indicate a change in the collection.
        The events are included in the `HX-Trigger` response header for
        requests with unsafe methods.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    template_name = "main/data/collection_component_list_table_row.html"
    list_template_name = "main/data/collection_component_list.html"
    list_row_form_template_name = "main/data/collection_component_list_row_form.html"

    template_query_param = "template"

    collection_model = None
    component_field_name = None

    template_map = {
        "list": list_template_name,
        "retrieve": {"form": list_row_form_template_name},
        "destroy": "main/blank.html",
    }

    @classmethod
    def _get_collection_field(cls):
        """The m2m field indicated by the `component_field_name`."""
        return cls.collection_model._meta.get_field(cls.component_field_name)

    @classmethod
    def through_model(cls):
        """The 'through' model for the collection - component relation."""
        return getattr(cls.collection_model, cls.component_field_name).through

    @classmethod
    def through_collection_field_name(cls) -> str:
        """The name of the through model's field referencing the
        collection.
        """
        return cls._get_collection_field().m2m_field_name()

    @classmethod
    def through_component_field_name(cls) -> str:
        """The name of the through model's field referencing the
        component.
        """
        return cls._get_collection_field().m2m_reverse_field_name()

    # docstr-coverage: inherited
    def get_template_context(self, data):
        url = (
            f"{self.through_collection_field_name()}-"
            f"{self.through_component_field_name()}-detail"
        )
        ret = {"url_name": url}
        if "obj" in data:
            ret["component_name"] = getattr(
                data["obj"], self.through_component_field_name()
            ).name
        return ret

    # docstr-coverage: inherited
    def get_permissions(self):
        perms = super().get_permissions()
        if self.detail:
            return perms + [permissions.IsCollectionComponentOwnerPermission()]
        return perms + [permissions.IsCollectionOwnerPermission()]

    # docstr-coverage: inherited
    def perform_create(self, serializer):
        lookup_kwarg = (
            getattr(self, "list_lookup_url_kwarg", None)
            or self.through_collection_field_name()
        )
        lookup = {
            f"{self.through_collection_field_name()}_id": self.kwargs[lookup_kwarg]
        }
        serializer.save(**lookup)

    # docstr-coverage: inherited
    def get_queryset(self):

        if self.detail:
            return self.through_model()._default_manager.select_related(
                self.through_component_field_name()
            )

        # If `list`, filter by collection
        lookup_kwarg = (
            getattr(self, "list_lookup_url_kwarg", None)
            or self.through_collection_field_name()
        )
        lookup = {self.through_collection_field_name(): self.kwargs[lookup_kwarg]}
        return (
            self.through_model()
            ._default_manager.filter(**lookup)
            .annotate(component_name=F(f"{self.through_component_field_name()}__name"))
            .select_related(self.through_component_field_name())
            .order_by("-id")
        )


class NutrientIntakeView(ListAPIView):
    """View for displaying dietary intakes.

    Displays the dietary intakes from a collection of ingredients
    (and recipes).
    """

    collection_model = models.Meal
    lookup_url_kwarg = "pk"
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    pagination_class = None
    template_name = "main/data/nutrient_tables.html"
    permission_classes = [permissions.IsOwnerPermission]
    serializer_class = serializers.NutrientIntakeSerializer

    @cached_property
    def obj(self):
        """The collection object."""
        return get_object_or_404(
            self.collection_model, pk=self.kwargs.get(self.lookup_url_kwarg)
        )

    @cached_property
    def intakes(self):
        """Nutrient intake in the selected collection."""
        self.check_object_permissions(self.request, self.obj)
        return self.obj.get_intakes()

    # docstr-coverage: inherited
    def get_queryset(self):
        return (
            models.Nutrient.objects.select_related("energy", "child_type")
            .prefetch_related(
                "types",
                Prefetch(
                    "recommendations",
                    queryset=models.IntakeRecommendation.objects.for_profile(
                        self.request.user.profile
                    ),
                ),
            )
            .order_by("name")
        )

    # docstr-coverage: inherited
    def get_template_context(self, data):

        queryset = data["results"]
        profile = self.request.user.profile
        intakes = self.intakes

        tracked = {nutrient.id for nutrient in profile.tracked_nutrients.all()}

        # Nutrient access by name
        n_data = {}
        for nutrient in queryset:
            recs = {}
            n_data[_slugify_underscore(nutrient.name)] = {
                "obj": nutrient,
                "recommendations": recs,
                "intake": self.intakes.get(nutrient.id, 0),
                "highlight": nutrient.id in tracked,
                "children": [],
            }
            # Set up recommendations with the profile and intakes
            # and allow access by `dri_type`.
            for recommendation in nutrient.recommendations.all():
                recommendation.set_up(profile, intakes.get(nutrient.id, 0))
                recs[_slugify_underscore(recommendation.dri_type)] = recommendation

        # Group data by nutrient type
        types = {type_.name for nutrient in queryset for type_ in nutrient.types.all()}
        by_type = {t: {} for t in types}
        by_type["none"] = {}
        for name, nutrient in n_data.items():
            nutrient_types = nutrient["obj"].types.all()
            if len(nutrient_types) == 0:
                by_type["none"][name] = nutrient
                continue
            for t in nutrient_types:
                by_type[t.name][name] = nutrient
        by_type = {_slugify_underscore(k): v for k, v in by_type.items()}

        # Set up access to nutrients with the `child_type` through the children key
        for nutrient in n_data.values():
            if hasattr(nutrient["obj"], "child_type"):
                nutrient["children"] = by_type.get(
                    _slugify_underscore(nutrient["obj"].child_type.name)
                )

        energy_progress = (
            profile.energy_progress(n_data["energy"]["intake"])
            if "energy" in n_data
            else None
        )
        return {
            "by_type": by_type,
            "by_name": n_data,
            "energy_requirement": profile.energy_requirement,
            "energy_progress": energy_progress,
            "calories": self.obj.calorie_ratio,
        }


def _slugify_underscore(s: str) -> str:
    """Slugify with underscores instead of hyphens.

    This allows to convert strings to a format that can be used as
    a template context var.
    """
    return slugify(s).replace("-", "_")

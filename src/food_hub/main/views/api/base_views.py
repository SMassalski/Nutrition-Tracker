"""API views intended for use only through inheritance."""
from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from main import models, permissions, serializers
from main.mixins import HTMXEventMixin
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import ModelViewSet

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

    def get_template_names(self):
        """Select the template to be used.

        The selection is based on the request method and the
        `template_query_param`.

        Returns
        -------
        List[str]
        """
        if self.action == "list":
            return [self.list_template_name]
        elif self.action == "retrieve":
            template_type = self.request.GET.get(self.template_query_param)
            if template_type and template_type.lower() == "form":
                return [self.list_row_form_template_name]
        return [self.template_name]

    # docstr-coverage: inherited
    def get_permissions(self):
        perms = super().get_permissions()
        if self.detail:
            return perms + [permissions.IsCollectionComponentOwnerPermission()]
        return perms + [permissions.IsCollectionOwnerPermission()]

    # docstr-coverage: inherited
    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.action == "create":
            # Add the collection id
            lookup_kwarg = (
                getattr(self, "list_lookup_url_kwarg", None)
                or self.through_collection_field_name()
            )
            context[self.through_collection_field_name()] = self.kwargs[lookup_kwarg]

        return context

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
            .select_related(self.through_component_field_name())
            .order_by("-id")
        )

    # docstr-coverage: inherited
    def destroy(self, request, *args, **kwargs):
        super().destroy(self, *args, **kwargs)
        # HTMX does not perform a swap when the response has a
        # no content (204) status.
        # NOTE: Using the usual rest_framework.response.Response
        #   caused a NoReverseMatch exception (for some reason arguments
        #   are removed).
        return HttpResponse(status=HTTP_200_OK)


class NutrientIntakeView(ListAPIView):
    """View for displaying dietary intakes.

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
    collection_model: django.db.models.Model
        The model of the object the nutrient intakes are retrieved from.
        If the model does not have a `get_intakes()` method,
        the view's `get_intakes()` method must be overridden.
    """

    serializer_class = serializers.NutrientIntakeSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    pagination_class = None
    template_name = "main/data/nutrient_tables.html"
    permission_classes = [permissions.IsOwnerPermission]

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

    collection_model = None

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        self._obj = None
        super().__init__(*args, **kwargs)

    def get_intakes(self):
        """Get the nutrient intakes displayed by the view."""
        return self._obj.get_intakes()

    # docstr-coverage: inherited
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["intakes"] = self.get_intakes()
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
                        self.request.user.profile
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

        Includes intake information from the selected model entry.
        """
        self._obj = get_object_or_404(
            self.collection_model, pk=self.kwargs.get(self.lookup_url_kwarg)
        )
        self.check_object_permissions(self.request, self._obj)
        response = super().get(*args, **kwargs)
        if not isinstance(response.data, dict):
            response.data = {"results": response.data}

        return response

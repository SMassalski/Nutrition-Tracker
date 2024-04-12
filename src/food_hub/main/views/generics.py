"""
Custom versions of DRF's generic views for better template support.
"""
from main.views.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.viewsets import ViewSetMixin

__all__ = (
    "GenericView",
    "ListAPIView",
    "CreateAPIView",
    "UpdateAPIView",
    "DestroyAPIView",
    "GenericViewSet",
    "ModelViewSet",
)


class GenericView(GenericAPIView):
    """Base class for generic views.

    This is a reimplementation of DRF's `GenericAPIView` for better
    template support.

    The `template_map` can be set to select templates based on the
    request's HTTP method and the value of the `template` query
    parameter. The template map should follow the format:
    template_map = {
        "<method>": "<template>",
        "<method2>": {
            "<template_query_param>": "<template>",
            "default": "<template>",
        }
        "default": "<template>"
    }
    """

    @property
    def template(self):
        """The value of the `template` query parameter."""
        val = self.request.GET.get("template")
        return val.lower() if val else None

    @property
    def uses_template_renderer(self):
        """
        True if the template renderer will render the response.
        """
        return isinstance(self.request.accepted_renderer, TemplateHTMLRenderer)

    # docstr-coverage: inherited
    def get_template_names(self):

        if hasattr(self, "template_map"):

            method_val = self.template_map.get(self.request.method.lower())
            method_val = method_val or self.template_map.get("default")

            if method_val:
                if isinstance(method_val, str):
                    return [method_val]

                # qp_val - Value from template query param
                qp_val = method_val.get(self.template) or method_val.get("default")
                if qp_val:
                    return [qp_val]

        if hasattr(self, "template_name"):
            return [self.template_name]

        return [None]

    def get_template_context(self, data):
        """Additional data to include in a template response."""
        return {}

    def get_success_headers(self, data):
        """
        Headers included in the response if the request was successful.
        """
        return {}

    def get_fail_headers(self, data):
        """
        Headers included in a 'bad request' template response.
        """
        return {}


class CreateAPIView(CreateModelMixin, GenericView):
    """Generic view for creating a model instance.

    This is a reimplementation of the DRF `CreateAPIView` using
    `GenericView` for better template support.
    """

    def post(self, request, *args, **kwargs):
        """Create a model instance."""
        return self.create(request, *args, **kwargs)


class ListAPIView(ListModelMixin, GenericView):
    """Generic view for listing a queryset.

    This is a reimplementation of the DRF `ListAPIView` using
    `GenericView` for better template support.
    """

    def get(self, request, *args, **kwargs):
        """List a queryset."""
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(RetrieveModelMixin, GenericView):
    """Generic view for retrieving a model instance.

    This is a reimplementation of the DRF `RetrieveAPIView` using
    `GenericView` for better template support.
    """

    def get(self, request, *args, **kwargs):
        """Retrieve a model instance."""
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(DestroyModelMixin, GenericView):
    """Generic view for destroying a model instance.

    This is a reimplementation of the DRF `DestroyAPIView` using
    `GenericView` for better template support.
    """

    def delete(self, request, *args, **kwargs):
        """Destroy a model instance."""
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(UpdateModelMixin, GenericView):
    """Generic view for updating a model instance.

    This is a reimplementation of the DRF `UpdateAPIView` using
    `GenericView` for better template support.
    """

    def put(self, request, *args, **kwargs):
        """Update a model instance."""
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Partially update a model instance."""
        return self.partial_update(request, *args, **kwargs)


class GenericViewSet(ViewSetMixin, GenericView):
    """
    View set without any actions but includes GenericView behavior.

    The template map differs from how it works in the `GenericView`
    as it uses actions instead of methods as keys.
    """

    # docstr-coverage: inherited
    def get_template_names(self):

        if hasattr(self, "template_map"):
            action_val = self.template_map.get(self.action.lower())
            action_val = action_val or self.template_map.get("default")

            if action_val:
                if isinstance(action_val, str):
                    return [action_val]

                # qp_val: Value from template query param
                qp_val = action_val.get(self.template) or action_val.get("default")
                if qp_val:
                    return [qp_val]

        if hasattr(self, "template_name"):
            return [self.template_name]

        return [None]

    # docstr-coverage: inherited
    def get_serializer_class(self):
        if self.detail and hasattr(self, "detail_serializer_class"):
            return self.detail_serializer_class
        return self.serializer_class


class ModelViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    """
    View set that provides default CRUD actions using `GenericView`.
    """

    pass

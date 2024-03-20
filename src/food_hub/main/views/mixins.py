"""Main app's mixins."""
from typing import Iterable

from main.views.session_util import ping_meal_interact
from rest_framework.mixins import CreateModelMixin as CreateMixin
from rest_framework.mixins import DestroyModelMixin as DestroyMixin
from rest_framework.mixins import ListModelMixin as ListMixin
from rest_framework.mixins import RetrieveModelMixin as RetrieveMixin
from rest_framework.mixins import UpdateModelMixin as UpdateMixin
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    is_success,
)

__all__ = (
    "MealInteractionMixin",
    "HTMXEventMixin",
    "CreateModelMixin",
    "ListModelMixin",
    "RetrieveModelMixin",
    "UpdateModelMixin",
    "DestroyModelMixin",
)

UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class MealInteractionMixin:
    """Mixin that updates the last meal interaction on each request."""

    # docstr-coverage: inherited
    def finalize_response(self, request, response, *args, **kwargs):
        ping_meal_interact(request)
        return super().finalize_response(request, response, *args, **kwargs)


class HTMXEventMixin:
    """Mixin that adds events to the HX-Trigger header.

    The values in `htmx_events` are added to the HX-Trigger header to
    responses to requests with unsafe methods.
    """

    htmx_events = []

    # docstr-coverage: inherited
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if is_success(response.status_code) and request.method in UNSAFE_METHODS:
            hx_trigger = _extend_comma_delimited_str(
                response.get("HX-Trigger"), self.htmx_events
            )
            if hx_trigger:
                response["HX-Trigger"] = hx_trigger
        return response


def _extend_comma_delimited_str(base: str, extensions: Iterable[str]) -> str:
    """Extend a string delimited by ', ' with strings in `extensions`."""
    if not extensions:
        return base
    if not base:
        return ", ".join(extensions)
    return ", ".join(base.split(", ") + list(extensions))


class CreateModelMixin(CreateMixin):
    """Create a model instance.

    This is a reimplementation of the `CreateModelMixin` for use with
    `GenericViews`.
    """

    # docstr-coverage: inherited
    def create(self, request, *args, **kwargs):
        if not self.uses_template_renderer:
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        data = {"serializer": serializer}
        if serializer.is_valid():
            self.perform_create(serializer)
            data["obj"] = serializer.instance
            status = HTTP_201_CREATED
        else:
            status = HTTP_400_BAD_REQUEST

        data.update(self.get_template_context(data))
        headers = (
            self.get_success_headers(data)
            if is_success(status)
            else self.get_fail_headers(data)
        )
        return Response(data, status=status, headers=headers)

    # docstr-coverage: inherited
    def get_success_headers(self, data):
        if self.uses_template_renderer and data is not None:
            return super().get_success_headers(data["serializer"].data)
        return super().get_success_headers(data)


class ListModelMixin(ListMixin):
    """List a queryset.

    This is a reimplementation of the `ListModelMixin` for use with
    `GenericViews`.
    The mixin behavior differs in cases where pagination is off,
    in that the results are wrapped in a dict (under the 'results' key).
    """

    # docstr-coverage: inherited
    def list(self, request, *args, **kwargs):
        if not self.uses_template_renderer:
            response = super().list(request, *args, **kwargs)

            # Wrap data in dict if pagination is off for consistency.
            if self.paginator is None:
                response.data = {"results": response.data}
            return response

        queryset = self.filter_queryset(self.get_queryset())
        paginated = self.paginate_queryset(queryset)

        response = (
            self.get_paginated_response(paginated)
            if paginated is not None
            else Response({"results": queryset})
        )

        response.data.update(self.get_template_context(response.data))
        return response


class RetrieveModelMixin(RetrieveMixin):
    """Retrieve a model instance.

    This is a reimplementation of the `RetrieveModelMixin` for use with
    `GenericViews`.
    """

    # docstr-coverage: inherited
    def retrieve(self, request, *args, **kwargs):

        if not self.uses_template_renderer:
            return super().retrieve(request, *args, **kwargs)

        data = {"obj": self.get_object()}
        data.update(self.get_template_context(data))
        return Response(data)


class UpdateModelMixin(UpdateMixin):
    """Update a model instance.

    This is a reimplementation of the `UpdateModelMixin` for use with
    `GenericViews`.
    """

    # docstr-coverage: inherited
    def update(self, request, *args, **kwargs):

        if not self.uses_template_renderer:
            return super().update(request, *args, **kwargs)

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        data = {"serializer": serializer, "obj": instance}
        if serializer.is_valid():
            self.perform_update(serializer)

            # Clear prefetch cache as per the comment in UpdateModelMixin source.
            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}

            status = HTTP_200_OK
        else:
            status = HTTP_400_BAD_REQUEST

        data.update(self.get_template_context(data))
        headers = (
            self.get_success_headers(data)
            if is_success(status)
            else self.get_fail_headers(data)
        )
        return Response(data, status=status, headers=headers)


class DestroyModelMixin(DestroyMixin):
    """Destroy a model instance.

    This is a reimplementation of the `UpdateModelMixin` for use with
    `GenericViews`.
    """

    # docstr-coverage: inherited
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.headers = (
            self.get_success_headers(response.data)
            if is_success(response.status_code)
            else self.get_fail_headers(response.data)
        )
        return response

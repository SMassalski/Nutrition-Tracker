"""Main app's mixins."""
from typing import Iterable

from main.views.session_util import ping_meal_interact
from rest_framework.status import is_success

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
    """Extend a string delimited by ', ' by strings in `extensions`."""
    if not extensions:
        return base
    if not base:
        return ", ".join(extensions)
    return ", ".join(base.split(", ") + list(extensions))

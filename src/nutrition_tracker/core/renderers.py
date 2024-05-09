"""Custom renderers."""
from django.urls import resolve
from rest_framework.renderers import BrowsableAPIRenderer as BrowsableRenderer
from rest_framework.reverse import reverse

__all__ = ("BrowsableAPIRenderer",)


class BrowsableAPIRenderer(BrowsableRenderer):
    """
    BrowsableAPIRenderer that enforces the api format in breadcrumbs.
    """

    # docstr-coverage: inherited
    def get_breadcrumbs(self, request):
        breadcrumbs = super().get_breadcrumbs(request)

        ret = []
        for name, url in breadcrumbs:
            match = resolve(url)
            match.kwargs.pop("format", None)
            ret.append(
                (name, reverse(match.view_name, kwargs=match.kwargs, format="api"))
            )
        return ret

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
        ret = super().get_breadcrumbs(request)
        ret = [
            (name, reverse(resolve(url).url_name, format="api")) for name, url in ret
        ]
        return ret

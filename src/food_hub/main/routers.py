"""Main app's custom routers."""
from django.urls import re_path
from rest_framework.routers import DynamicRoute, Route, SimpleRouter


class ModelCollectionRouter(SimpleRouter):
    """Router intended for use with ModelCollectionViewSet subclasses."""

    routes = [
        # List route.
        Route(
            url=r"^{prefix}/{list_lookup}/{component_field}{trailing_slash}$",
            mapping={"get": "list", "post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{list_lookup}/{component_field}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=False,
            initkwargs={},
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{component_field}/{lookup}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{component_field}/{lookup}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=True,
            initkwargs={},
        ),
    ]

    @staticmethod
    def get_list_lookup_regex(viewset, lookup_prefix=""):
        """Given a viewset, return the portion of URL regex that is used
        to match against a single collection instance.
        """
        base_regex = "(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})"
        lookup_field = viewset.through_collection_field_name()
        lookup_url_kwarg = (
            getattr(viewset, "list_lookup_url_kwarg", None) or lookup_field
        )
        lookup_value = getattr(viewset, "lookup_value_regex", "[^/.]+")
        return base_regex.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value,
        )

    # docstr-coverage: inherited
    def get_urls(self):
        ret = []

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            list_lookup = self.get_list_lookup_regex(viewset)
            routes = self.get_routes(viewset)
            component_field = getattr(viewset, "component_field_name", "component")

            for route in routes:

                # Skip if action doesn't exist on the viewset
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                regex = route.url.format(
                    prefix=prefix,
                    lookup=lookup,
                    list_lookup=list_lookup,
                    component_field=component_field,
                    trailing_slash=self.trailing_slash,
                )

                # remove the preceding slash if the prefix is empty to
                # avoid double slashes
                if not prefix and regex[:2] == "^/":
                    regex = "^" + regex[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update(
                    {
                        "basename": basename,
                        "detail": route.detail,
                    }
                )

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename)
                ret.append(re_path(regex, view, name=name))

        return ret

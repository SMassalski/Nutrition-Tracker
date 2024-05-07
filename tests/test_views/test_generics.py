"""
Tests of the custom generic views and view sets from the
core.views.generics module.
"""
from core.views.generics import GenericView, GenericViewSet
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from .util import create_api_request


class TestGenericView:
    class View(GenericView):
        renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

        def get(self, request, *args, **kwargs):
            return Response({"uses_template_renderer": self.uses_template_renderer})

    def test_template_property(self):
        view = self.View()
        expected = "val"
        request = create_api_request("get", query_params={"template": expected})
        view.setup(request)

        assert view.template == expected

    def test_template_property_always_lowercase(self):
        view = self.View()
        request = create_api_request("get", query_params={"template": "VaL"})
        view.setup(request)
        expected = "val"

        assert view.template == expected

    def test_template_property_none(self):
        view = self.View()
        request = create_api_request("get", query_params={"template": ""})
        view.setup(request)

        assert view.template is None

    def test_uses_template_renderer_html_format_true(self):
        view = self.View()
        request = create_api_request("get", format="html")
        response = view.as_view()(request)

        assert response.data["uses_template_renderer"] is True

    def test_uses_template_renderer_json_format_false(self):
        view = self.View()
        request = create_api_request("get", format="json")
        response = view.as_view()(request)

        assert response.data["uses_template_renderer"] is False

    def test_get_template_names_template_map_by_method(self):
        expected = "template"
        template_map = {"get": expected}
        view = self.View(template_map=template_map)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_template_map_by_template_query_param(self):
        expected = "expected"
        template_map = {"get": {"exp": expected, "default": "template"}}
        view = self.View(template_map=template_map)
        request = create_api_request("get", query_params={"template": "exp"})
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_template_map_missing_method(self):
        expected = "expected"
        template_map = {"post": "template", "default": expected}
        view = self.View(template_map=template_map)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_empty_template_map_but_has_template_name(self):
        expected = "expected"
        view = self.View(template_map={}, template_name=expected)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_no_template_map_but_has_template_name(self):
        expected = "expected"
        view = self.View(template_name=expected)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_method_and_template_combination_missing(self):
        expected = "expected"
        template_map = {"get": {"tmp": "template"}, "default": "template"}
        view = self.View(template_map=template_map, template_name=expected)
        request = create_api_request("get", query_params={"template": "tqp"})
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_no_template_map_no_template_name_none(self):

        view = self.View()
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual is None


class TestGenericViewSet:
    class ViewSet(GenericViewSet):
        def list(self, request, *args, **kwargs):
            return Response()

    class Serializer:
        pass

    class DetailSerializer:
        pass

    def test_get_template_names_template_map_by_action(self):
        expected = "template"
        template_map = {"list": expected}
        view = self.ViewSet(action="list", template_map=template_map)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_template_map_by_template_query_param(self):
        expected = "expected"
        template_map = {"list": {"exp": expected, "default": "template"}}
        view = self.ViewSet(action="list", template_map=template_map)
        request = create_api_request("get", query_params={"template": "exp"})
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_template_map_missing_method(self):
        expected = "expected"
        template_map = {"create": "template", "default": expected}
        view = self.ViewSet(action="list", template_map=template_map)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_empty_template_map_but_has_template_name(self):
        expected = "expected"
        view = self.ViewSet(action="list", template_map={}, template_name=expected)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_no_template_map_but_has_template_name(self):
        expected = "expected"
        view = self.ViewSet(action="list", template_name=expected)
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_method_and_template_combination_missing(self):
        expected = "expected"
        template_map = {"list": {"tmp": "template"}, "default": "template"}
        view = self.ViewSet(
            action="list", template_map=template_map, template_name=expected
        )
        request = create_api_request("get", query_params={"template": "tqp"})
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual == expected

    def test_get_template_names_no_template_map_no_template_name_none(self):

        view = self.ViewSet(action="list")
        request = create_api_request("get")
        view.setup(request)

        actual = view.get_template_names()[0]

        assert actual is None

    def test_get_serializer_class_detail_false(self):

        view = self.ViewSet(
            detail=False,
            serializer_class=self.Serializer,
            detail_serializer_class=self.DetailSerializer,
        )
        request = create_api_request("get")
        view.setup(request)
        expected = self.Serializer

        actual = view.get_serializer_class()

        assert actual is expected

    def test_get_serializer_class_detail_true(self):

        view = self.ViewSet(
            detail=True,
            serializer_class=self.Serializer,
            detail_serializer_class=self.DetailSerializer,
        )
        request = create_api_request("get")
        view.setup(request)
        expected = self.DetailSerializer

        actual = view.get_serializer_class()

        assert actual is expected

    def test_get_serializer_class_detail_true_no_detail_serializer(self):

        view = self.ViewSet(
            detail=True,
            serializer_class=self.Serializer,
        )
        request = create_api_request("get")
        view.setup(request)
        expected = self.Serializer

        actual = view.get_serializer_class()

        assert actual is expected

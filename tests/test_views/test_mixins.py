"""Tests of core app's mixins."""
from core.views import mixins
from rest_framework.response import Response
from rest_framework.views import APIView

from .util import create_api_request


class HtmxEventView(mixins.HTMXEventMixin, APIView):
    def post(self, request):
        return Response()

    def get(self, request):
        return Response()


class TestHtmxEventMixin:
    def test_adds_hx_trigger_header_if_events_are_set(self):
        view = HtmxEventView.as_view(htmx_events=["event"])
        request = create_api_request("post")

        response = view(request)

        assert response.headers["HX-Trigger"] == "event"

    def test_no_hx_trigger_header_if_no_events_are_set(self):
        view = HtmxEventView.as_view()
        request = create_api_request("post")

        response = view(request)

        assert "HX-Trigger" not in response.headers

    def test_appends_to_hx_trigger_header_if_already_exists(self):
        class NewHtmxEventView(HtmxEventView):
            htmx_events = ["another_event"]

            def post(self, request):
                return Response(headers={"HX-Trigger": "event"})

        view = NewHtmxEventView.as_view()
        request = create_api_request("post")

        response = view(request)

        assert response.headers["HX-Trigger"] == "event, another_event"

    def test_safe_method_does_not_set_the_header(self):
        view = HtmxEventView.as_view(htmx_events=["event"])
        request = create_api_request("get")

        response = view(request)

        assert "HX-Trigger" not in response.headers

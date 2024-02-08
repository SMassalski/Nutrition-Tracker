"""Tests of main app's view decorators."""
import pytest
from django.http.response import HttpResponse
from django.views import View
from main.decorators import profile_required
from rest_framework.status import is_redirect, is_success


class TestProfileRequired:
    @pytest.fixture
    def function_view(self):
        @profile_required
        def view(request):
            return HttpResponse()

        return view

    @pytest.fixture
    def class_based_view(self):
        class CBView(View):
            def get(self, request):
                return HttpResponse()

        return profile_required(CBView.as_view())

    def test_function_view_request_with_profile_ok(
        self, rf, user, saved_profile, function_view
    ):
        request = rf.get("")
        request.user = user

        response = function_view(request)

        assert is_success(response.status_code)

    def test_function_view_request_without_profile_redirect(
        self, rf, user, function_view
    ):
        request = rf.get("")
        request.user = user

        response = function_view(request)

        assert is_redirect(response.status_code)

    def test_class_based_view_request_with_profile_ok(
        self, rf, user, saved_profile, class_based_view
    ):
        request = rf.get("")
        request.user = user

        response = class_based_view(request)

        assert is_success(response.status_code)

    def test_class_based_view_request_without_profile_redirect(
        self, rf, user, class_based_view
    ):
        request = rf.get("")
        request.user = user

        response = class_based_view(request)

        assert is_redirect(response.status_code)

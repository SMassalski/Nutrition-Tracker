"""Tests of views related to session 'current meal' functionality."""
from datetime import date

import pytest
from django.http import Http404
from main import models
from main.views.api import current_meal_views as views
from rest_framework.reverse import reverse
from rest_framework.status import is_redirect, is_success

from tests.test_views.util import create_api_request


class TestCurrentMealView:
    """Tests of the CurrentMealView"""

    view = views.CurrentMealView()

    @pytest.fixture(autouse=True)
    def _profile(self, saved_profile):
        """Set up a profile for the user."""
        pass

    # POST

    def test_response_has_current_meal_changed_header(self, user):
        """
        A response from a valid CurrentMealView request has a
        currentMealChanged htmx trigger header.
        """
        data = {"date": "2020-06-21"}
        request = create_api_request("post", user, data, use_session=True)

        response = self.view.as_view()(request)

        assert response.headers["HX-Trigger"] == "currentMealChanged"

    def test_invalid_request_no_response_current_meal_changed_header(self, user):
        """
        A response from an invalid CurrentMealView request doesn't
        have a currentMealChanged htmx trigger header.
        """
        data = {}

        request = create_api_request("post", user, data, use_session=True)

        response = self.view.as_view()(request)

        assert response.headers.get("HX-Trigger") != "currentMealChanged"

    def test_creates_meal(self, user):
        """
        The CurrentMealView creates a new meal if there isn't one.
        """
        date_str = "2020-06-21"
        expected_date = date.fromisoformat(date_str)
        data = {"date": date_str}
        request = create_api_request("post", user, data, use_session=True)

        self.view.as_view()(request)

        assert models.Meal.objects.filter(
            owner=user.profile, date=expected_date
        ).exists()

    # General

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_valid_request_status_code(self, user, meal, method):
        """
        A valid request to the CurrentMealView returns with a success
        code.
        """
        data = {"date": "2020-06-21"}
        request = create_api_request(method, user, data, use_session=True)
        request.session["meal_id"] = meal.id

        response = self.view.as_view()(request)

        assert is_success(response.status_code)

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_context_contains_meal_date_date_obj_if_template_renderer_used(
        self, user, meal, method
    ):
        """
        The CurrentMealView response context contains the current meal
        date under the key `meal_date` if the `TemplateHTMLRenderer`
        was used.
        """
        date_str = "2020-06-15"  # match meal's date for simplicity
        expected = date.fromisoformat(date_str)
        data = {"date": date_str}
        request = create_api_request(method, user, data, use_session=True)
        request.session["meal_id"] = meal.id

        response = self.view.as_view()(request)

        assert response.data.get("date_obj") == expected

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_context_doesnt_contain_meal_date_date_obj_if_template_renderer_wasnt_used(
        self, user, meal, method
    ):
        data = {"date": "2020-06-21"}
        request = create_api_request(
            method,
            user=user,
            data=data,
            format="json",
            use_session=True,
        )
        request.session["meal_id"] = meal.id

        response = self.view.as_view()(request)

        assert "date_obj" not in response.data

    def test_updates_last_meal_interact(self, user, meal, saved_profile):
        data = {"date": "2020-06-21"}
        request = create_api_request("post", user, data, use_session=True)

        self.view.as_view()(request)

        assert request.session.get("last_meal_interact")


class TestCurrentMealRedirectView:
    """Tests of the CurrentMealRedirectView class."""

    def test_meal_response_status_code(self, user, meal):
        """
        A request to the view returns a response with a redirect status code.
        """
        request = create_api_request("get", user, use_session=True)
        request.session["meal_id"] = meal.id
        view = views.CurrentMealRedirectView.as_view(
            pattern_name="meal-ingredient-list"
        )

        response = view(request)

        assert is_redirect(response.status_code)

    @pytest.mark.parametrize(
        ("url_name", "redirect_url_name"),
        (
            ("current-meal-ingredients", "meal-ingredient-list"),
            ("current-meal-intakes", "meal-intakes"),
        ),
    )
    def test_meal_ingredient_redirects_to_correct_endpoint(
        self, client_with_meal, meal, url_name, redirect_url_name
    ):
        """
        A request to the view redirects to the correct meal's
        ingredients endpoint.
        """
        url = reverse(url_name)
        expected_url = reverse(redirect_url_name, args=[meal.pk])

        response = client_with_meal.get(url)

        assert response.url == expected_url

    def test_returns_404_if_no_current_meal_entry_exists(self, user):
        """
        A GET request to the view returns with a 404 status code
        if there is no current meal set in the session.
        """
        request = create_api_request("get", user, use_session=True)
        view = views.CurrentMealRedirectView.as_view(pattern_name="meal-ingredients")

        # Checked with raises because the CurrentMealRedirectView is
        # not an APIView
        with pytest.raises(Http404):
            view(request)

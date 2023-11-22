"""Tests of views from the `hypermedia_views` module."""
from main.views.api import hypermedia_views as views
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from .util import create_api_request


class TestMealComponentTabView:

    url = reverse("add-meal-component-tabs")

    def test_endpoint_ok(self, logged_in_api_client):

        response = logged_in_api_client.get(self.url)

        assert is_success(response.status_code)

    def test_selects_active_tab_based_on_tab_query_param(self):
        request = create_api_request("get", query_params={"tab": "recipes"})
        view = views.MealComponentTabView.as_view(
            tabs=[("Ingredients", "ingredient-list"), ("Recipes", "recipe-list")]
        )

        response = view(request)

        assert ("Recipes", True) in response.data["tabs"]

    def test_data_includes_active_tabs_url(self):
        request = create_api_request("get", query_params={"tab": "ingredients"})
        view = views.MealComponentTabView.as_view(
            tabs=[("Ingredients", "ingredient-list"), ("Recipes", "recipe-list")]
        )
        expected = reverse("ingredient-list")

        response = view(request)

        assert response.data["url"] == expected

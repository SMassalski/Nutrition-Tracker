"""Tests of main app's API views"""
import json

import pytest
from main.views.api import api_views as views
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from tests.test_views.util import create_api_request

# API root


class TestRootView:
    """Tests of the API root view."""

    url = reverse("api-root")

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf):
        """Set up a get request to the API root view."""
        self.request = rf.get(self.url)

    def test_endpoint_ok(self):
        response = views.api_root(self.request)

        assert is_success(response.status_code)

    def test_urls_persist_format(self):
        response = views.api_root(self.request, format="json")

        for url in response.data.values():
            assert url.rstrip("/").endswith(".json")


# Ingredient views


class TestIngredientListView:
    """Tests of the API ingredient list view."""

    url = reverse("ingredient-list")

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf):
        """Set up a get request to the ingredient list view."""
        self.request = rf.get(self.url)

    def test_status_code(self, db):
        """IngredientView response has a `200` status code."""
        response = views.IngredientView.as_view()(self.request)

        assert response.status_code == status.HTTP_200_OK

    def test_lists_ingredients(self, db, ingredient_1, ingredient_2):
        """
        IngredientView response contains a list of ingredient records.
        """
        response = views.IngredientView.as_view()(self.request, format="json")
        response.render()

        result = {item["name"] for item in json.loads(response.content)["results"]}
        expected = {ingredient_1.name, ingredient_2.name}
        assert result == expected

    def test_html_format_uses_the_correct_template(
        self, ingredient_1, logged_in_client
    ):
        response = logged_in_client.get(self.url)

        assert (
            response.templates[0].name == "main/data/component_search_result_list.html"
        )


class TestIngredientDetailView:
    """Tests of the ingredient detail view."""

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf, ingredient_1):
        """Set up a get request to the ingredient detail view."""
        self.pk = ingredient_1.pk
        url = reverse("ingredient-detail", args=[self.pk])
        self.request = rf.get(url)
        self.view = views.IngredientDetailView.as_view()

    def test_status_code(self, db):
        """IngredientDetailView response has a `200` status code"""
        response = self.view(self.request, pk=self.pk)

        assert response.status_code == status.HTTP_200_OK

    def test_fields(self, db, ingredient_1):
        """IngredientDetailView response entry contains the correct fields"""
        response = self.view(self.request, pk=self.pk, format="json")
        response.render()

        result = set(json.loads(response.content).keys())
        expected = {"external_id", "name", "dataset", "nutrients"}
        assert result == expected

    def test_nutrients_field(self, db, ingredient_1, ingredient_nutrient_1_1):
        """IngredientDetailView response entry contains the correct fields"""
        response = self.view(self.request, pk=self.pk, format="json")
        response.render()

        result = set(json.loads(response.content)["nutrients"][0].keys())
        expected = {"url", "nutrient", "amount"}
        assert result == expected


class TestIngredientPreviewView:
    def test_get_template_context_has_component_field(self, ingredient_1):
        expected = "value"
        view = views.IngredientPreviewView.as_view(component_field=expected)
        request = create_api_request("get")

        response = view(request, pk=ingredient_1.id)

        actual = response.data["component_field"]
        assert actual == expected

    def test_get_template_context_calories_is_calorie_ratio(
        self, ingredient_1, ingredient_nutrient_1_1, nutrient_1, nutrient_1_energy
    ):
        expected = 100
        view = views.IngredientPreviewView.as_view(component_field=expected)
        request = create_api_request("get")

        response = view(request, pk=ingredient_1.id)

        actual = response.data["calories"][nutrient_1.name]
        assert actual == expected  # would be 15 if calories property was used


# Nutrient view


class TestNutrientListView:
    """Tests of the nutrient list view."""

    url = reverse("nutrient-list")

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf):
        """Set up a get request to the nutrient list view."""
        self.request = rf.get(self.url)

    def test_status_code(self, db):
        """NutrientView response has a 200 status code."""
        response = views.NutrientView.as_view()(self.request)

        assert response.status_code == status.HTTP_200_OK

    def test_lists_nutrients(self, db, nutrient_1, nutrient_2):
        """NutrientView response contains a list of nutrient records."""
        response = views.NutrientView.as_view()(self.request, format="json")
        response.render()

        result = {item["name"] for item in json.loads(response.content)["results"]}
        expected = {nutrient_1.name, nutrient_2.name}
        assert result == expected

    def test_fields(self, db, nutrient_1):
        """NutrientView response entry contains the correct fields."""
        response = views.NutrientView.as_view()(self.request, format="json")
        response.render()

        result = set(json.loads(response.content)["results"][0].keys())
        expected = {"name", "url"}
        assert result == expected


class TestNutrientDetailView:
    """Tests of the nutrient detail view."""

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf, nutrient_1):
        """Set up a get request to the nutrient detail view."""
        self.pk = nutrient_1.pk
        url = reverse("nutrient-detail", args=[self.pk])
        self.request = rf.get(url)
        self.view = views.NutrientDetailView.as_view()

    def test_status_code(self, db, nutrient_1):
        """NutrientDetailView response has a 200 status code."""
        response = self.view(self.request, pk=self.pk)

        assert response.status_code == status.HTTP_200_OK

    def test_fields(self, db, nutrient_1):
        """NutrientDetailView response entry contains the correct fields."""
        response = self.view(self.request, pk=self.pk, format="json")
        response.render()

        result = set(json.loads(response.content).keys())
        expected = {"name", "unit"}
        assert result == expected

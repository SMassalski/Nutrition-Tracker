"""Tests of main app's API views"""
import json
from datetime import datetime

import pytest
from main.serializers import WeightMeasurementSerializer
from main.views import api as views
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from .util import create_api_request

# API root


class TestRootView:
    """Tests of the API root view."""

    url = reverse("api-root")

    @pytest.fixture(autouse=True)
    def set_up_request(self, rf):
        """Set up a get request to the API root view."""
        self.request = rf.get(self.url)

    def test_get_status_code(self):
        """
        api_root_view() response to a GET request has a 200 status code.
        """
        response = views.api_root(self.request)

        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_links_to_list_views(self):
        """
        api_root_view() response contains urls to ingredient and
        nutrient list views.
        """
        response = views.api_root(self.request, format="json")
        response.render()

        content = json.loads(response.content)
        assert content.get("Ingredients").endswith("api/ingredients/")
        assert content.get("Nutrients").endswith("api/nutrients/")


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

    def test_fields(self, db, ingredient_1):
        """IngredientView response entry contains the correct fields."""
        response = views.IngredientView.as_view()(self.request, format="json")
        response.render()

        result = set(json.loads(response.content)["results"][0].keys())
        expected = {"id", "name", "url", "preview_url"}
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


class TestWeightMeasurementViewSet:

    view_class = views.WeightMeasurementViewSet

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_endpoint_ok_list(self, method, logged_in_api_client, saved_profile):
        url = reverse("weight-measurement-list")

        response = getattr(logged_in_api_client, method)(url, data={"value": 80})

        assert is_success(response.status_code)

    @pytest.mark.parametrize("method", ("get", "patch", "put", "delete"))
    def test_endpoint_ok_detail(self, method, logged_in_api_client, weight_measurement):
        url = reverse("weight-measurement-detail", args=(weight_measurement.id,))

        response = getattr(logged_in_api_client, method)(
            url, data={"value": 81, "time": weight_measurement.time}
        )

        assert is_success(response.status_code)

    @pytest.mark.parametrize(
        ("method", "action", "template_param", "expected"),
        (
            ("get", "list", None, "main/data/weight_measurement_list.html"),
            ("get", "retrieve", None, "main/data/weight_measurement_list_row.html"),
            (
                "get",
                "retrieve",
                "form",
                "main/data/weight_measurement_list_form_row.html",
            ),
            ("post", "create", None, "main/data/weight_measurement_add.html"),
            ("post", "create", "modal", "main/modals/add_weight_measurement.html"),
            ("put", "update", None, "main/data/weight_measurement_list_row.html"),
            (
                "patch",
                "partial_update",
                None,
                "main/data/weight_measurement_list_row.html",
            ),
            ("delete", "destroy", None, "main/data/weight_measurement_list_row.html"),
        ),
    )
    def test_get_template_names(
        self, method, action, template_param, expected, user, saved_profile
    ):
        query_params = {"template": template_param} if template_param else None
        request = create_api_request(method, user, query_params=query_params)
        view = self.view_class(action=action)
        view.setup(request)

        assert view.get_template_names() == [expected]

    @pytest.mark.parametrize("method", ("get", "put", "patch"))
    def test_datetime_in_template_response_detail(
        self, method, user, weight_measurement
    ):
        request = create_api_request(method, user, {"value": 1})
        method_map = {"put": "update", "patch": "partial_update", "get": "retrieve"}
        view = self.view_class.as_view(method_map, detail=True)

        response = view(request, pk=weight_measurement.id)

        assert isinstance(response.data["datetime"], datetime)

    def test_datetime_in_template_response_list_action(self, user, weight_measurement):
        request = create_api_request("get", user)

        view = self.view_class.as_view({"get": "list"}, detail=False)

        response = view(request)

        assert isinstance(response.data["results"][0]["datetime"], datetime)

    # Create

    def test_create_serializer_in_response_data_valid_request(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, {"value": 1})

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        serializer = response.data.get("serializer")
        assert isinstance(serializer, WeightMeasurementSerializer)

    def test_create_serializer_in_response_data_invalid_request(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, {})

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        serializer = response.data.get("serializer")
        assert isinstance(serializer, WeightMeasurementSerializer)

    def test_create_success_in_response_data_valid_request(self, user, saved_profile):
        request = create_api_request("post", user, {"value": 1})

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        success = response.data.get("success")
        assert success is True

    def test_create_success_in_response_data_invalid_request(self, user, saved_profile):
        request = create_api_request("post", user, {})

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        success = response.data.get("success")
        assert success is False

    def test_create_invalid_request_inner_html_reswap_in_response_header(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, {})

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert response.headers["HX-Reswap"] == "innerHTML"

    def test_create_invalid_request_modal_template_outer_html_reswap_in_response_header(
        self, user, saved_profile
    ):
        request = create_api_request(
            "post", user, {}, query_params={"template": "modal"}
        )

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert response.headers["HX-Reswap"] == "outerHTML"

    def test_create_invalid_request_modal_template_reselect_in_response_header(
        self, user, saved_profile
    ):
        request = create_api_request(
            "post", user, {}, query_params={"template": "modal"}
        )

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert response.headers["HX-Reselect"] == "#add-weight-measurement"

    def test_datetime_in_template_response_create_action(
        self, user, weight_measurement
    ):
        request = create_api_request("post", user, {"value": 1})
        method_map = {"post": "create"}
        view = self.view_class.as_view(method_map, detail=False)

        response = view(request)

        assert isinstance(response.data["datetime"], datetime)

    def test_create_json_request_success_not_included_in_response_data(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, {"value": 1}, format="json")

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert "success" not in response.data

    def test_create_json_request_serializer_not_included_in_response_data(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, {"value": 1}, format="json")

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert "serializer" not in response.data

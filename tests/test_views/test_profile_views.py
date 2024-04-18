from datetime import date, timedelta

import main.views
import pytest
from main import models
from main.serializers import WeightMeasurementSerializer
from main.views import api as views
from rest_framework.exceptions import PermissionDenied
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, is_success

from tests.test_views.util import create_api_request


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
            url, data={"value": 81, "date": "2022-02-10"}
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
            ("delete", "destroy", None, "main/blank.html"),
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

    def test_last_month_excludes_dates_older_than_30_days(
        self, user, saved_profile, weight_measurement
    ):
        date_ = date.today() - timedelta(days=31)
        weight_measurement.date = date_
        weight_measurement.save()

        request = create_api_request("get", user, format="json")

        response = self.view_class.as_view({"get": "last_month_weights"}, detail=False)(
            request
        )

        assert date_.strftime("%b %d") not in response.data

    def test_last_month_rounds_value_to_first_decimal_place(
        self, user, saved_profile, weight_measurement
    ):
        date_ = date.today()
        weight_measurement.date = date_
        weight_measurement.value = 80.11
        weight_measurement.save()

        request = create_api_request("get", user, format="json")

        response = self.view_class.as_view({"get": "last_month_weights"}, detail=False)(
            request
        )

        assert response.data[date_.strftime("%b %d")] == 80.1

    def test_unsafe_method_response_has_weight_changed_event_header(
        self, user, saved_profile
    ):
        request = create_api_request("post", user, data={"value": 80}, format="json")

        response = self.view_class.as_view({"post": "create"}, detail=False)(request)

        assert response.headers["HX-Trigger"] == "weightChanged"

    # Permissions

    def test_denies_access_to_non_owners(
        self, saved_profile, new_user, weight_measurement
    ):
        request = create_api_request("get", new_user)
        request.user = new_user

        # Prevent AttributeError caused by using WSGIRequest
        request.authenticators = False

        view = self.view_class()

        with pytest.raises(PermissionDenied):
            view.check_object_permissions(request, weight_measurement)

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_only_allows_users_with_profile(self, user, method):
        request = create_api_request(method, user)
        view = views.WeightMeasurementViewSet.as_view(
            detail=False, actions={"get": "list", "post": "create"}
        )

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN


class TestProfileAPIView:

    view_class = main.views.api.profile_views.ProfileApiView

    @pytest.fixture
    def data(self):
        """Default request data."""
        return {
            "age": 20,
            "height": 180,
            "weight": 100,
            "sex": "M",
            "activity_level": "S",
        }

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_endpoint_ok(self, logged_in_api_client, method, data):
        url = reverse("profile")

        response = getattr(logged_in_api_client, method)(url, data=data)

        assert is_success(response.status_code)

    def test_endpoint_ok_patch(self, logged_in_api_client, saved_profile):
        url = reverse("profile")
        data = {
            "age": 20,
            "height": 180,
        }

        response = logged_in_api_client.patch(url, data=data)

        assert is_success(response.status_code)

    # GET method

    def test_get_passes_next_query_param_to_data(self, user):
        request = create_api_request("get", user, query_params={"next": "/"})
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["next"] == "/"

    def test_get_no_next_query_param(self, user):
        request = create_api_request("get", user)
        view = self.view_class.as_view()

        response = view(request)

        assert "next" not in response.data

    def test_get_json_format_404_response_without_profile(self, user):
        request = create_api_request("get", user, format="json")
        view = self.view_class.as_view()

        response = view(request)

        assert response.status_code == HTTP_404_NOT_FOUND

    def test_get_no_profile_template_response_ok_and_empty(self, user):
        request = create_api_request("get", user)
        view = self.view_class.as_view()

        response = view(request)

        assert is_success(response.status_code)
        assert response.data == {}

    def test_get_with_profile_retrieves_users_profile(self, user, saved_profile):
        request = create_api_request("get", user)
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["obj"] == saved_profile

    # POST method

    def test_post_with_next_param_redirects_on_success(self, data, user):
        request = create_api_request("post", user, data, query_params={"next": "/"})
        view = self.view_class.as_view()

        response = view(request)

        assert response.headers["HX-Redirect"] == "/"

    def test_post_with_next_param_does_not_redirect_on_fail(self, data, user):
        del data["age"]  # missing data to make the request invalid
        request = create_api_request("post", user, data, query_params={"next": "/"})
        view = self.view_class.as_view()

        response = view(request)

        assert "HX-Redirect" not in response.headers

    def test_post_valid_request_has_success_var_in_data(self, user, data):
        request = create_api_request("post", user, data)
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["success"] is True

    def test_post_invalid_request_data_success_false(self, user, data):
        data["age"] = 0.1
        request = create_api_request("post", user, data)
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["success"] is False

    def test_post_json_format_ok(self, user, data):
        request = create_api_request("post", user, data, format="json")
        view = self.view_class.as_view()

        response = view(request)
        assert is_success(response.status_code)

    def test_post_not_allowed_if_profile_exists(self, data, saved_profile):
        request = create_api_request("post", saved_profile.user, data)
        view = self.view_class.as_view()

        response = view(request)
        assert response.status_code == HTTP_403_FORBIDDEN

    # PATCH method

    def test_patch_valid_request_has_success_var_in_data(
        self, user, data, saved_profile
    ):
        request = create_api_request("patch", user, data)
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["success"] is True

    def test_patch_invalid_request_data_success_false(self, user, data, saved_profile):
        data["age"] = -20
        request = create_api_request("patch", user, data)
        view = self.view_class.as_view()

        response = view(request)

        assert response.data["success"] is False


class TestLastMonthIntakeView:
    def test_endpoint_ok(self, logged_in_api_client, nutrient_1, saved_profile):
        url = reverse("last-month-intake", args=(nutrient_1.id,))
        response = logged_in_api_client.get(url)

        assert is_success(response.status_code)

    def test_only_retrieves_intakes_from_last_30_days(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        user,
        saved_profile,
    ):
        meal.date = date.today() - timedelta(days=15)
        meal.save()
        meal_2.date = date.today() - timedelta(days=40)
        meal_2.save()
        request = create_api_request("get", user)
        view = main.views.api.profile_views.LastMonthIntakeView.as_view()
        date_str = meal.date.strftime("%b %d")
        expected = {
            (date.today() - timedelta(days=30 - i)).strftime("%b %d"): None
            for i in range(31)
        }
        expected[date_str] = 300.0

        response = view(request, pk=nutrient_1.id)

        assert response.data["intakes"] == expected

    def test_only_retrieves_recommendations_for_users_profile(
        self,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        user,
        saved_profile,
        recommendation,
    ):
        meal.date = date.today() - timedelta(days=15)
        meal.save()
        recommendation.dri_type = recommendation.RDAKG
        recommendation.save()
        request = create_api_request("get", user)
        view = main.views.api.profile_views.LastMonthIntakeView.as_view()

        response = view(request, pk=nutrient_1.id)

        assert response.data["recommendations"][0]["amount_min"] == 400
        assert response.data["recommendations"][0]["amount_max"] == 400

    # Permissions

    def test_only_allows_users_with_profile(self, user):
        request = create_api_request("get", user)
        view = views.LastMonthIntakeView.as_view()

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN


class TestLastMonthCalorieView:
    def test_returns_calories_for_the_last_30_days(self, user, saved_profile):
        request = create_api_request("get", user)
        view = views.LastMonthCalorieView.as_view()
        expected = [
            (date.today() - timedelta(days=30 - i)).strftime("%b %d") for i in range(31)
        ]

        response = view(request)

        assert response.data["caloric_intake"]["dates"] == expected

    # Permissions

    def test_only_allows_users_with_profile(self, user):
        request = create_api_request("get", user)
        view = views.LastMonthCalorieView.as_view()

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN


class TestTrackedNutrientViewSet:
    @pytest.mark.parametrize("method", ("get", "post"))
    def test_endpoint_ok_list(
        self, logged_in_api_client, saved_profile, method, nutrient_1
    ):
        url = reverse("tracked-nutrient-list")
        response = getattr(logged_in_api_client, method)(
            url, data={"nutrient": nutrient_1.id}
        )

        assert is_success(response.status_code)

    def test_endpoint_ok_get_list_template(
        self, logged_in_api_client, saved_profile, nutrient_1
    ):
        url = reverse("tracked-nutrient-list") + "?template=list"
        response = logged_in_api_client.get(url)

        assert is_success(response.status_code)

    def test_endpoint_ok_detail(self, logged_in_api_client, saved_profile, nutrient_1):
        instance = models.Profile.tracked_nutrients.through.objects.create(
            profile=saved_profile, nutrient=nutrient_1
        )
        url = reverse("tracked-nutrient-detail", args=(instance.id,))
        response = logged_in_api_client.delete(url)

        assert is_success(response.status_code)

    @pytest.mark.parametrize("template", ("add", None))
    def test_endpoint_ok_form(
        self, logged_in_api_client, saved_profile, nutrient_1, template
    ):
        query_str = f"?template={template}" if template else ""
        url = reverse("tracked-nutrient-form") + query_str
        response = logged_in_api_client.get(url)

        assert is_success(response.status_code)

    @pytest.mark.parametrize(
        ("action", "template_qp", "expected"),  # Template query param
        (
            ("list", None, "main/data/tracked_nutrients_card.html"),
            ("list", "list", "main/data/tracked_nutrient_list.html"),
            ("create", None, "main/data/tracked_nutrient_list_row.html"),
            ("form", None, "main/components/tracked_nutrients_row_form.html"),
            ("form", "add", "main/data/tracked_nutrient_list.html"),
        ),
    )
    def test_get_template(self, action, template_qp, expected):
        view = main.views.api.profile_views.TrackedNutrientViewSet(action=action)

        query_params = {"template": template_qp} if template_qp else None
        request = create_api_request("get", query_params=query_params)
        view.setup(request)

        actual = view.get_template_names()[0]

        assert expected == actual

    def test_list_wraps_data_in_dict(self, user, saved_profile):
        request = create_api_request("get", user)
        view = main.views.api.profile_views.TrackedNutrientViewSet.as_view(
            {"get": "list"}
        )

        response = view(request)

        assert list(response.data.keys()) == ["results"]

    def test_create_uses_profile_from_the_request(
        self, user, saved_profile, nutrient_1
    ):
        request = create_api_request("post", user, data={"nutrient": nutrient_1.id})
        view = main.views.api.profile_views.TrackedNutrientViewSet.as_view(
            {"post": "create"}
        )

        view(request)

        assert nutrient_1 in saved_profile.tracked_nutrients.all()

    def test_create_response_has_event_header(self, user, saved_profile, nutrient_1):
        request = create_api_request("post", user, data={"nutrient": nutrient_1.id})
        view = main.views.api.profile_views.TrackedNutrientViewSet.as_view(
            {"post": "create"}
        )
        expected = "trackedNutrientsChanged"

        actual = view(request).headers["HX-Trigger"]

        assert expected == actual

    def test_delete_response_has_event_header(self, user, saved_profile, nutrient_1):
        saved_profile.tracked_nutrients.add(nutrient_1)
        request = create_api_request("delete", user)
        view = main.views.api.profile_views.TrackedNutrientViewSet.as_view(
            {"delete": "destroy"}
        )
        expected = "trackedNutrientsChanged"

        actual = view(request, pk=nutrient_1.id).headers["HX-Trigger"]

        assert expected == actual

    # Permissions

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_only_allows_users_with_profile(self, user, method):
        request = create_api_request(method, user)
        view = views.TrackedNutrientViewSet.as_view(
            detail=False, actions={"get": "list", "post": "create"}
        )

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN

    def test_hides_instance_for_users_that_dont_own_it(
        self, new_user, nutrient_1, saved_profile
    ):
        TrackedNutrient = models.Profile.tracked_nutrients.through
        instance = TrackedNutrient.objects.create(
            profile=saved_profile, nutrient=nutrient_1
        )
        request = create_api_request("delete", new_user)
        view = views.TrackedNutrientViewSet.as_view(
            detail=True, actions={"delete": "destroy"}
        )

        response = view(request, pk=instance.id)

        assert response.status_code == HTTP_404_NOT_FOUND


class TestMalconsumptionView:
    @pytest.fixture
    def recommendations(self, nutrient_1, nutrient_2):
        """IntakeRecommendation instances.

        If using the meal_ingredient, ingredient_nutrient_1_1
        and ingredient_nutrient_1_2, nutrient_1 will be underconsumed.

        age_min: 0
        dri_type: RDA
        nutrient: nutrient_1
        sex: "B"
        amount_min: 500

        age_min: 0
        dri_type: RDA
        nutrient: nutrient_2
        sex: "B"
        amount_min: 10
        """
        return models.IntakeRecommendation.objects.bulk_create(
            [
                models.IntakeRecommendation(
                    age_min=0,
                    dri_type=models.IntakeRecommendation.RDA,
                    nutrient=nutrient_1,
                    sex="B",
                    amount_min=500,
                ),
                models.IntakeRecommendation(
                    age_min=0,
                    dri_type=models.IntakeRecommendation.RDA,
                    nutrient=nutrient_2,
                    sex="B",
                    amount_min=10,
                ),
            ]
        )

    @pytest.fixture
    def meal(self, meal):
        meal.date = date.today()
        meal.save()
        return meal

    def test_endpoint_ok(self, user, saved_profile, logged_in_api_client):
        url = reverse("malconsumptions")

        response = logged_in_api_client.get(url)

        assert is_success(response.status_code)

    def test_lists_malconsumed_nutrients(
        self,
        user,
        meal_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1,
        recommendations,
    ):

        request = create_api_request("get", user)
        view = views.MalconsumptionView.as_view()

        response = view(request)

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == nutrient_1.id

    def test_data_fields(
        self,
        user,
        meal_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        recommendations,
    ):
        request = create_api_request("get", user)
        view = views.MalconsumptionView.as_view()

        response = view(request)

        for field in ("id", "name", "magnitude"):
            assert field in response.data["results"][0]

    def test_exclude_attribute_excludes_nutrients_from_results(
        self,
        user,
        meal_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1,
        recommendations,
    ):

        request = create_api_request("get", user)
        view = views.MalconsumptionView.as_view(exclude=[nutrient_1.name])

        response = view(request)

        assert len(response.data["results"]) == 0

    def test_excludes_meals_older_than_30_days(
        self,
        user,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1,
        recommendations,
    ):
        meal.date = date.today() - timedelta(days=31)
        meal.save()

        request = create_api_request("get", user)
        view = views.MalconsumptionView.as_view()

        response = view(request)

        # Empty because there is no data
        assert len(response.data["results"]) == 0

    # Permissions

    def test_only_allows_users_with_profile(self, user):
        request = create_api_request("get", user)
        view = views.MalconsumptionView.as_view()

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN

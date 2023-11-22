"""Tests of meal-related views."""
import pytest
from django.conf import settings
from main import models
from main.views.api import MealIngredientPreviewView
from main.views.api.meal_views import MealNutrientIntakeView
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, is_success

from tests.test_views.util import create_api_request, is_pagination_on


class TestMealNutrientIntakeView:
    """Tests of the MealNutrientIntakeView class."""

    @pytest.fixture
    def _request(self, user, meal):
        """An authenticated request and user.

        Includes a session with a meal.
        """
        _request = create_api_request("get", user, use_session=True)
        _request.session["meal_id"] = meal.id
        return _request

    def test_get_ok(self, client_with_meal, meal):
        """
        A GET request to the view returns with a success status code.
        """
        url = reverse("meal-intakes", args=(meal.id,))
        response = client_with_meal.get(url)

        assert is_success(response.status_code)

    # View
    def test_results_fields(
        self, nutrient_1_with_type, _request, saved_recommendation, meal
    ):
        """
        MealNutrientIntakeView context contains the NutrientIntakeSerializer data.
        """
        expected_fields = {
            "id",
            "name",
            "unit",
            "energy",
            "recommendations",
            "types",
            "child_type",
            "children",
            "intake",
        }
        display_order = ("nutrient_type",)
        view = MealNutrientIntakeView().as_view(display_order=display_order)

        response = view(_request, meal=meal.id)
        print(f"{response.data = }")
        fields = set(response.data["results"][0]["nutrients"][0].keys())
        assert fields == expected_fields

    def test_get_num_queries(
        self,
        _request,
        django_assert_num_queries,
        nutrient_1_with_type,
        meal_ingredient,
        many_recommendations,
        meal,
    ):
        """
        The view's GET method uses the smallest number of queries
        possible.
        """
        # Turning on pagination makes this test fail
        view = MealNutrientIntakeView().as_view(display_order=None)

        with django_assert_num_queries(6):
            # 1) Get the meal (in this case meal already exists)
            # 2) Get intakes from recipes. (Meal.get_intakes())
            # 3) Get intakes from ingredients. (Meal.get_intakes())
            # 4) Get Nutrients with select_related child_type and energy. (queryset)
            # 5) `prefetch_related()` for the `types` field. (queryset)
            # 6) `prefetch_related()` for the `recommendations` field. (queryset)
            _ = view(_request, meal=meal.id)

    def test_exclude_nutrients_without_recommendations(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        saved_recommendation,
        meal,
    ):
        """
        The view only includes nutrients with at least one related
        IntakeRecommendation.
        """
        view = MealNutrientIntakeView().as_view(display_order=None)

        response = view(_request, meal=meal.id)

        assert len(response.data["results"]) == 1

    # View attributes
    def test_nutrient_data_uses_display_order(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        many_recommendations,
        meal,
    ):
        """
        The view uses the `display_order` attribute.
        """
        display_order = ("nutrient_type", "child_type")
        expected = ("Displayed Name", "Child Name")
        view = MealNutrientIntakeView().as_view(display_order=display_order)

        response = view(_request, meal=meal.id)

        type_names = tuple(group["type_name"] for group in response.data["results"])
        assert type_names == expected

    def test_no_recommendations_attribute(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        many_recommendations,
        meal,
    ):
        """
        The view response includes nutrients without recommendations
        if the nutrient's name is in the `no_recommendations` attribute.
        """
        view = MealNutrientIntakeView().as_view(
            display_order=None, no_recommendations=["test_nutrient_2"]
        )

        response = view(_request, meal=meal.id)

        assert len(response.data["results"]) == 2

    def test_skip_amdr_attribute(
        self,
        _request,
        nutrient_1_with_type,
        saved_recommendation,
        meal,
    ):
        """
        Meal view nutrient_data only excludes recommendation entries
        if the nutrient's name is in the `skip_amdr` attribute and the
        recommendation has an 'AMDR' `dri_type`.
        """
        models.IntakeRecommendation.objects.create(
            dri_type=models.IntakeRecommendation.AMDR,
            sex="B",
            age_min=0,
            nutrient=nutrient_1_with_type,
        )
        view = MealNutrientIntakeView().as_view(
            display_order=None, skip_amdr=["test_nutrient"]
        )

        response = view(_request, meal=meal.id)

        recommendations = response.data["results"][0]["nutrients"][0]["recommendations"]
        assert len(recommendations) == 1

    @pytest.mark.skipif(
        is_pagination_on(),
        reason="Test is irrelevant, because pagination is turned off globally",
    )
    def test_no_pagination(self, _request, nutrient_type, meal):
        """The view doesn't paginate by default."""

        # Create more nutrients than `page_size` and a recommendation
        # for each of them
        num_nutrients = settings.REST_FRAMEWORK.get("PAGE_SIZE") + 5
        nutrients = [
            models.Nutrient(name=f"nutrient_{x}", unit=models.Nutrient.GRAMS)
            for x in range(num_nutrients)
        ]
        nutrients = models.Nutrient.objects.bulk_create(nutrients)
        recommendations = [
            models.IntakeRecommendation(
                nutrient=nut,
                dri_type=models.IntakeRecommendation.RDA,
                age_min=0,
                sex="B",
            )
            for nut in nutrients
        ]
        models.IntakeRecommendation.objects.bulk_create(recommendations)

        # Assign each nutrient a type
        for nutrient in nutrients:
            nutrient.types.add(nutrient_type)

        view = MealNutrientIntakeView().as_view(display_order=None)

        response = view(_request, meal=meal.id)

        assert len(response.data["results"][0]["nutrients"]) == num_nutrients

    def test_deny_permission_if_not_owner_of_the_meal(self, meal_ingredient, new_user):
        request = create_api_request("get", new_user, use_session=True)
        view = MealNutrientIntakeView().as_view(display_order=None)

        response = view(request, meal=meal_ingredient.meal_id)

        assert response.status_code == HTTP_403_FORBIDDEN


class TestMealIngredientPreviewView:
    """Test of the ingredient preview view."""

    @pytest.fixture(autouse=True)
    def _set_up(self, ingredient_1, saved_profile):
        """Set up a get request to the ingredient detail view."""
        self.pk = ingredient_1.pk
        self.url = reverse("meal-ingredient-preview", args=[self.pk])

    def test_uses_the_correct_template(self, client_with_meal):
        """IngredientPreview uses the preview template."""
        response = client_with_meal.get(self.url)

        assert response.templates[0].name == "main/data/preview.html"

    def test_returns_404_if_no_current_meal_entry_exists(self, user, ingredient_1):
        """
        A GET request to the view returns with a 404 status code
        if there is no current meal set in the session.
        """
        request = create_api_request("get", user, use_session=True)

        response = MealIngredientPreviewView().as_view()(request, pk=ingredient_1.pk)

        assert response.status_code == HTTP_404_NOT_FOUND

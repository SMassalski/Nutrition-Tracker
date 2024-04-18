"""Tests of meal-related views."""
import pytest
from django.conf import settings
from main import models
from main.views.api.meal_views import (
    MealIngredientPreviewView,
    MealNutrientIntakeView,
    MealViewSet,
)
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

    def test_get_template_context_by_type_structure(
        self, nutrient_1_with_type, _request, recommendation, meal
    ):
        # {
        #     "<type_name>": {
        #         "<nutrient_name>": {
        #             "obj": "<nutrient_instance>",
        #             "intake": "<nutrient_intake>",
        #             "recommendations": {
        #                 "<dri_type>": "<recommendation_instance (already set up)>"
        #             },
        #         }
        #     }
        # }
        type_ = nutrient_1_with_type.types.first()
        type_.name = "Nutrient Type"
        type_.save()
        nutrient_1_with_type.name = "Nutrient 1"
        nutrient_1_with_type.save()
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.save()
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]

        # keys are lowercase and whitespaces are replaced with underscores
        assert "nutrient_type" in data
        assert "nutrient_1" in data["nutrient_type"]

        nutrient_data = data["nutrient_type"]["nutrient_1"]
        assert "obj" in nutrient_data
        assert "intake" in nutrient_data
        assert "recommendations" in nutrient_data
        assert "highlight" in nutrient_data

        assert "rdakg" in nutrient_data["recommendations"]

    def test_get_template_context_nutrients_without_are_under_none(
        self, nutrient_1, _request, meal
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]

        assert "test_nutrient" in data["none"]

    def test_get_template_context_nutrient_obj_is_nutrient_instance(
        self, nutrient_1_with_type, _request, meal
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]["nutrient_type"]

        assert data["test_nutrient"]["obj"] == nutrient_1_with_type

    def test_get_template_context_nutrient_intake_is_meal_intake_of_nutrient(
        self,
        nutrient_1_with_type,
        _request,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]["nutrient_type"]

        assert data["test_nutrient"]["intake"] == 300

    def test_get_template_context_nutrient_highlight_if_tracked_by_profile(
        self,
        nutrient_1_with_type,
        _request,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        saved_profile,
    ):
        saved_profile.tracked_nutrients.add(nutrient_1_with_type)
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_name"]

        assert data["test_nutrient"]["highlight"] is True
        assert data["test_nutrient_2"]["highlight"] is False

    def test_get_template_context_recommendation_is_an_instance(
        self, nutrient_1_with_type, _request, saved_recommendation, meal
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]["nutrient_type"]

        rec = data["test_nutrient"]["recommendations"]["rda"]
        assert rec == saved_recommendation

    def test_get_template_context_recommendations_are_filtered_for_profile(
        self, nutrient_1_with_type, _request, many_recommendations, meal
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_type"]["nutrient_type"]

        rec = data["test_nutrient"]["recommendations"]["rda"]
        assert rec == many_recommendations[0]

    def test_get_template_context_by_name_keys(
        self, nutrient_1, _request, saved_recommendation, meal
    ):
        view = MealNutrientIntakeView().as_view()

        data = view(_request, meal=meal.id).data["by_name"]["test_nutrient"]

        assert data["obj"] == nutrient_1
        assert "intake" in data
        assert data["recommendations"]["rda"] == saved_recommendation
        assert "children" in data

    def test_get_template_context_energy_requirement_is_profiles_energy_requirement(
        self, nutrient_1, _request, saved_recommendation, meal
    ):
        view = MealNutrientIntakeView().as_view()
        expected = 2311  # from saved profile fixture

        actual = view(_request, meal=meal.id).data["energy_requirement"]

        assert actual == expected

    def test_get_template_context_energy_progress(
        self,
        _request,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
    ):
        nutrient_1.name = "Energy"
        nutrient_1.save()
        view = MealNutrientIntakeView().as_view()
        # ingredient_nutrient (1.5)  * meal_ingredient (200)
        # / 2311 (energy_requirement) * 100 (%)
        expected = 13

        actual = view(_request, meal=meal.id).data["energy_progress"]

        assert actual == expected

    def test_get_template_context_energy_progress_no_energy_in_data_none(
        self,
        _request,
        meal,
    ):
        view = MealNutrientIntakeView().as_view()

        actual = view(_request, meal=meal.id).data["energy_progress"]

        assert actual is None

    def test_get_template_context_calories_is_meals_calorie_ratio(
        self,
        _request,
        meal,
        meal_ingredient,
        recipe,
        meal_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        nutrient_2_energy,
        nutrient_2,
    ):

        view = MealNutrientIntakeView().as_view()

        expected = {"test_nutrient": 97.4, "test_nutrient_2": 2.6}

        actual = view(_request, meal=meal.id).data["calories"]

        assert actual == expected

    def test_get_num_queries(
        self,
        _request,
        django_assert_num_queries,
        nutrient_1_with_type,
        meal_ingredient,
        many_recommendations,
        meal,
        meal_recipe,
        recipe_ingredient,
        nutrient_1_energy,
    ):
        """
        The view's GET method uses the smallest number of queries
        possible.
        """
        # Turning on pagination makes this test fail
        view = MealNutrientIntakeView().as_view()

        with django_assert_num_queries(10):
            # 1) Get the meal (in this case meal already exists)
            # 2) Get intakes from recipes. (Meal.get_intakes())
            # 3) Get intakes from ingredients. (Meal.get_intakes())
            # 4) Get tracked_nutrients
            # 5) Get Nutrients with select_related child_type and energy. (queryset)
            # 6) `prefetch_related()` for the `types` field. (queryset)
            # 7) `prefetch_related()` for the `recommendations` field. (queryset)
            # 8) Nutrient query for meal.recipe_calories
            # 9) Main query for meal.recipe_calories
            # 10) Main query for meal.ingredient_calories
            _ = view(_request, meal=meal.id)

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

        view = MealNutrientIntakeView().as_view()

        response = view(_request, meal=meal.id)

        assert len(response.data["results"]) == num_nutrients

    def test_deny_permission_if_not_owner_of_the_meal(self, meal_ingredient, new_user):
        request = create_api_request("get", new_user, use_session=True)
        view = MealNutrientIntakeView().as_view()

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


class TestMealViewSet:

    # Permissions

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_only_allows_users_with_profile(self, user, method):
        request = create_api_request(method, user)
        view = MealViewSet.as_view(
            detail=False, actions={"get": "list", "post": "create"}
        )

        response = view(request)

        assert response.status_code == HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("method", ("get", "patch", "delete"))
    def test_hides_meal_for_users_that_dont_own_the_meal(self, new_user, meal, method):
        request = create_api_request(method, new_user)
        view = MealViewSet.as_view(
            detail=True,
            actions={"get": "retrieve", "patch": "partial_update", "delete": "destroy"},
        )

        response = view(request, pk=meal.id)

        assert response.status_code == HTTP_404_NOT_FOUND

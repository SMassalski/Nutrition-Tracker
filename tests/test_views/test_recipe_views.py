"""Test of recipe-related views."""
import pytest
from django.conf import settings
from main import models
from main.views.api.recipe_views import RecipeIntakeView, RecipeViewSet
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_403_FORBIDDEN, is_success
from rest_framework.test import APIRequestFactory, force_authenticate

from tests.test_views.util import create_api_request, is_pagination_on


class TestRecipeNutrientIntakeView:
    """Tests of the MealNutrientIntakeView class."""

    @pytest.fixture
    def _request(self, user, meal):
        """An authenticated request and user.

        Includes a session with a meal.
        """
        _request = create_api_request("get", user)
        return _request

    def test_get_ok(self, logged_in_api_client, recipe):
        """
        A GET request to the view returns with a success status code.
        """
        url = reverse("recipe-intakes", args=(recipe.id,))
        response = logged_in_api_client.get(url)

        assert is_success(response.status_code)

    def test_get_template_context_by_type_structure(
        self, nutrient_1_with_type, _request, recommendation, recipe
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
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]

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
        self, nutrient_1, _request, recipe
    ):
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]

        assert "test_nutrient" in data["none"]

    def test_get_template_context_nutrient_obj_is_nutrient_instance(
        self, nutrient_1_with_type, _request, recipe
    ):
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]["nutrient_type"]

        assert data["test_nutrient"]["obj"] == nutrient_1_with_type

    def test_get_template_context_nutrient_intake_is_recipe_intake_of_nutrient(
        self,
        nutrient_1_with_type,
        _request,
        recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
    ):
        recipe.final_weight = 100
        recipe.save()
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]["nutrient_type"]

        assert data["test_nutrient"]["intake"] == 150

    def test_get_template_context_nutrient_highlight_if_tracked_by_profile(
        self,
        nutrient_1_with_type,
        _request,
        recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        saved_profile,
    ):
        saved_profile.tracked_nutrients.add(nutrient_1_with_type)
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_name"]

        assert data["test_nutrient"]["highlight"] is True
        assert data["test_nutrient_2"]["highlight"] is False

    def test_get_template_context_recommendation_is_an_instance(
        self, nutrient_1_with_type, _request, saved_recommendation, recipe
    ):
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]["nutrient_type"]

        rec = data["test_nutrient"]["recommendations"]["rda"]
        assert rec == saved_recommendation

    def test_get_template_context_recommendations_are_filtered_for_profile(
        self, nutrient_1_with_type, _request, many_recommendations, recipe
    ):
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_type"]["nutrient_type"]

        rec = data["test_nutrient"]["recommendations"]["rda"]
        assert rec == many_recommendations[0]

    def test_get_template_context_by_name_keys(
        self, nutrient_1, _request, saved_recommendation, recipe
    ):
        view = RecipeIntakeView().as_view()

        data = view(_request, recipe=recipe.id).data["by_name"]["test_nutrient"]

        assert data["obj"] == nutrient_1
        assert "intake" in data
        assert data["recommendations"]["rda"] == saved_recommendation
        assert "children" in data

    def test_get_template_context_energy_requirement_is_profiles_energy_requirement(
        self, nutrient_1, _request, saved_recommendation, recipe
    ):
        view = RecipeIntakeView().as_view()
        expected = 2311  # from saved profile fixture

        actual = view(_request, recipe=recipe.id).data["energy_requirement"]

        assert actual == expected

    def test_get_template_context_energy_progress(
        self,
        _request,
        recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
    ):
        nutrient_1.name = "Energy"
        nutrient_1.save()
        view = RecipeIntakeView().as_view()
        # ingredient_nutrient (1.5)  * recipe_ingredient (100)
        # / weight (200) * 100 (intakes of recipe are per 100g)
        # / 2311 (energy_requirement) * 100 (%)
        expected = 3

        actual = view(_request, recipe=recipe.id).data["energy_progress"]

        assert actual == expected

    def test_get_template_context_energy_progress_no_energy_in_data_none(
        self,
        _request,
        recipe,
    ):
        view = RecipeIntakeView().as_view()

        actual = view(_request, recipe=recipe.id).data["energy_progress"]

        assert actual is None

    def test_get_template_context_calories_is_recipes_calorie_ratio(
        self,
        _request,
        recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        nutrient_2_energy,
    ):

        view = RecipeIntakeView().as_view()

        expected = {"test_nutrient": 97.4, "test_nutrient_2": 2.6}

        actual = view(_request, recipe=recipe.id).data["calories"]

        assert actual == expected

    def test_get_num_queries(
        self,
        _request,
        django_assert_num_queries,
        nutrient_1_with_type,
        many_recommendations,
        recipe,
        recipe_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1_energy,
    ):
        # Turning on pagination makes this test fail
        view = RecipeIntakeView().as_view()

        with django_assert_num_queries(7):
            # 1) Get the recipe (in this case, the recipe already exists)
            # 2) Get intakes.
            # 3) Get tracked nutrients
            # 4) Get Nutrients with select_related child_type and energy. (queryset)
            # 5) `prefetch_related()` for the `types` field. (queryset)
            # 6) `prefetch_related()` for the `recommendations` field. (queryset)
            # 7) Calorie query.
            _ = view(_request, recipe=recipe.id)

    @pytest.mark.skipif(
        is_pagination_on(),
        reason="Test is irrelevant, because pagination is turned off globally",
    )
    def test_no_pagination(self, _request, nutrient_type, recipe):
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

        view = RecipeIntakeView().as_view()

        response = view(_request, recipe=recipe.id)

        assert len(response.data["results"]) == num_nutrients

    def test_deny_permission_if_not_owner_of_the_recipe(self, recipe, new_user):
        request = create_api_request("get", new_user, use_session=True)
        view = RecipeIntakeView().as_view()

        response = view(request, recipe=recipe.id)

        assert response.status_code == HTTP_403_FORBIDDEN


class TestRecipeViewSet:
    @pytest.mark.parametrize(
        ("method", "detail"),
        (
            ("get", False),
            ("get", True),
            ("post", False),
            ("patch", True),
            ("delete", True),
        ),
    )
    def test_endpoint_ok(self, logged_in_api_client, recipe, method, detail):

        if detail:
            suffix = "detail"
            args = (recipe.id,)
        else:
            suffix = "list"
            args = None
        pattern_name = f"recipe-{suffix}"
        data = {"name": "name", "final_weight": 1}
        url = reverse(pattern_name, args=args)

        response = getattr(logged_in_api_client, method)(url, data)

        assert is_success(response.status_code)

    @pytest.mark.parametrize(
        ("method", "target", "template"),
        (
            ("get", None, "main/data/component_search_result_list.html"),
            ("get", "edit", "main/data/recipe_search_result_list.html"),
            ("post", None, "main/modals/new_recipe_form.html"),
        ),
    )
    def test_get_templates_list(self, recipe, user, method, target, template):
        params = {"target": target} if target else None
        request = create_api_request(method, user, query_params=params)
        view = RecipeViewSet(
            detail=False, action={"get": "list", "post": "create"}[method]
        )
        view.setup(request)

        assert view.get_template_names()[0] == template

    @pytest.mark.parametrize(
        ("method", "expected"),
        (
            ("get", "main/data/recipe_detail_form.html"),
            ("patch", "main/data/recipe_detail_form.html"),
            ("delete", "main/blank.html"),
        ),
    )
    def test_get_templates_detail(self, recipe, user, method, expected):
        request = create_api_request(method, user)
        view = RecipeViewSet(
            detail=True,
            action={
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }[method],
        )
        view.setup(request)

        assert view.get_template_names()[0] == expected

    # List

    def test_lists_only_recipes_owned_by_the_user(self, recipe, user, new_user):

        new_recipe = models.Recipe.objects.create(
            name="new_user's recipe", owner=new_user.profile, final_weight=1
        )
        request = create_api_request("get", new_user)
        view = RecipeViewSet.as_view(detail=False, actions={"get": "list"})

        response = view(request)

        ids = [recipe.id for recipe in response.data["results"]]
        assert ids == [new_recipe.id]

    def test_list_data_contains_object_type(self, user, saved_profile):
        request = create_api_request("get", user)
        view = RecipeViewSet.as_view(detail=False, actions={"get": "list"})

        response = view(request)

        assert response.data["obj_type"] == "recipes"

    # Create

    def test_create_redirects_on_success_if_has_redirect_query_param(
        self, user, saved_profile
    ):
        data = {"name": "name", "final_weight": 1}
        request = APIRequestFactory().post("?redirect=true", data=data)
        force_authenticate(request, user)
        view = RecipeViewSet.as_view(detail=False, actions={"post": "create"})

        response = view(request)

        assert response.headers["HX-Redirect"] == reverse("recipe-edit", ("name-1",))

    # Update

    def test_update_valid_request_has_the_hx_location_header(self, user, recipe):
        data = {"name": "name"}

        request = create_api_request("patch", user, data)
        view = RecipeViewSet.as_view(detail=True, actions={"patch": "partial_update"})

        response = view(request, pk=recipe.id)

        assert response.headers["HX-Location"] == reverse("recipe-edit", ("name-1",))

    # Destroy

    def test_destroy_valid_request_has_the_hx_redirect_header(self, user, recipe):

        request = create_api_request("delete", user)
        view = RecipeViewSet.as_view(detail=True, actions={"delete": "destroy"})

        response = view(request, pk=recipe.id)

        assert response.headers["HX-Redirect"] == reverse("recipe")

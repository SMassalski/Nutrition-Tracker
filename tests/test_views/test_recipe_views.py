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

    # View
    def test_results_fields(
        self, nutrient_1_with_type, _request, saved_recommendation, recipe
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
        view = RecipeIntakeView().as_view(display_order=display_order)

        response = view(_request, recipe=recipe.id)

        fields = set(response.data["results"][0]["nutrients"][0].keys())
        assert fields == expected_fields

    def test_get_num_queries(
        self,
        _request,
        django_assert_num_queries,
        nutrient_1_with_type,
        many_recommendations,
        recipe,
    ):
        """
        The view's GET method uses the smallest number of queries
        possible.
        """
        # Turning on pagination makes this test fail
        view = RecipeIntakeView().as_view(display_order=None)

        with django_assert_num_queries(5):
            # 1) Get the recipe (in this case, the recipe already exists)
            # 2) Get intakes.
            # 3) Get Nutrients with select_related child_type and energy. (queryset)
            # 4) `prefetch_related()` for the `types` field. (queryset)
            # 5) `prefetch_related()` for the `recommendations` field. (queryset)
            _ = view(_request, recipe=recipe.id)

    def test_exclude_nutrients_without_recommendations(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        saved_recommendation,
        recipe,
    ):
        """
        The view only includes nutrients with at least one related
        IntakeRecommendation.
        """
        view = RecipeIntakeView().as_view(display_order=None)

        response = view(_request, recipe=recipe.id)

        assert len(response.data["results"]) == 1

    # View attributes
    def test_nutrient_data_uses_display_order(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        many_recommendations,
        recipe,
    ):
        """
        The view uses the `display_order` attribute.
        """
        display_order = ("nutrient_type", "child_type")
        expected = ("Displayed Name", "Child Name")
        view = RecipeIntakeView().as_view(display_order=display_order)

        response = view(_request, recipe=recipe.id)

        type_names = tuple(group["type_name"] for group in response.data["results"])
        assert type_names == expected

    def test_no_recommendations_attribute(
        self,
        _request,
        nutrient_1_with_type,
        nutrient_2_with_type,
        many_recommendations,
        recipe,
    ):
        """
        The view response includes nutrients without recommendations
        if the nutrient's name is in the `no_recommendations` attribute.
        """
        view = RecipeIntakeView().as_view(
            display_order=None, no_recommendations=["test_nutrient_2"]
        )

        response = view(_request, recipe=recipe.id)

        assert len(response.data["results"]) == 2

    def test_skip_amdr_attribute(
        self,
        _request,
        nutrient_1_with_type,
        saved_recommendation,
        recipe,
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
        view = RecipeIntakeView().as_view(
            display_order=None, skip_amdr=["test_nutrient"]
        )

        response = view(_request, recipe=recipe.id)

        recommendations = response.data["results"][0]["nutrients"][0]["recommendations"]
        assert len(recommendations) == 1

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

        view = RecipeIntakeView().as_view(display_order=None)

        response = view(_request, recipe=recipe.id)

        assert len(response.data["results"][0]["nutrients"]) == num_nutrients

    def test_deny_permission_if_not_owner_of_the_meal(self, recipe, new_user):
        request = create_api_request("get", new_user, use_session=True)
        view = RecipeIntakeView().as_view(display_order=None)

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

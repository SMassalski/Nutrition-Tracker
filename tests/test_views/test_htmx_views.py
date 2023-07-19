"""Tests of main app's hypermedia API views."""
from datetime import date

import pytest
from django.conf import settings
from django.http import Http404
from main import models
from main.views import htmx
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_redirect,
    is_success,
)
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from .util import add_session


@pytest.fixture
def logged_in_client(user):
    """An APIClient authenticated with the user fixture."""
    client = APIClient()
    client.force_login(user)
    return client


def is_pagination_on() -> bool:
    """Check if DRF pagination is enabled globally."""
    return (
        settings.REST_FRAMEWORK.get("PAGE_SIZE") is None
        or settings.REST_FRAMEWORK.get("DEFAULT_PAGINATION_CLASS") is None
    )


def create_request(method, user=None, data=None, format=None, use_session=False):
    """Construct a request.

    Parameters
    ----------
    method: str
        The HTTP method of the request.
    user: models.User
        The user which will be used to authenticate the request.
    data: dict
        The data to include in the request.
    format: str
        The format parameter of the request.
        This is used by the view to select the renderer.
    use_session: bool
        If `True` a session will be attached to the request.

    Returns
    -------
    django.core.handlers.wsgi.WSGIRequest
    """
    path = f"?format={format}" if format else ""

    # Workaround; The renderer is not set to JSON without this for GET requests
    headers = None
    if method.lower() == "get" and format == "json":
        headers = {"Accept": "application/json"}
    request = getattr(APIRequestFactory(), method.lower())(path, data, headers=headers)
    if use_session:
        add_session(request)
    if user:
        force_authenticate(request, user)

    return request


class TestMealIngredientDetail:
    """Tests of the MealIngredientDetail View"""

    view = htmx.MealIngredientDetailView()

    @pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
    def test_endpoint_ok(self, logged_in_client, meal_ingredient, method):
        url = reverse("meal-ingredient-detail", args=(meal_ingredient.pk,))

        response = getattr(logged_in_client, method)(
            url, {"amount": 5, "ingredient": meal_ingredient.ingredient_id}
        )

        assert is_success(response.status_code)

    # HTMX Event Trigger Headers

    @pytest.mark.parametrize(
        ("method", "has_header"), (("get", False), ("put", True), ("delete", True))
    )
    def test_successful_request_meal_changed_header(
        self, user, meal_ingredient, method, has_header
    ):
        """
        A successful request to the MealIngredientDetail view
        returns a response with a `mealComponentsChanged` htmx trigger (except
        for GET requests).
        """
        data = {"amount": 5, "ingredient": meal_ingredient.ingredient_id}
        request = create_request(method, user, data)

        response = self.view.as_view()(request, pk=meal_ingredient.pk)

        assert (
            response.headers.get("HX-Trigger") == "mealComponentsChanged"
        ) is has_header

    @pytest.mark.parametrize("method", ("get", "put", "delete"))
    def test_invalid_request_no_meal_changed_header(
        self, user, meal_ingredient, method
    ):
        """
        An invalid request to the MealIngredientDetail view
        returns a response without a `mealComponentsChanged` htmx trigger.
        """
        request = create_request(method, user)

        response = self.view.as_view()(request, pk=meal_ingredient.pk + 1)

        assert response.headers.get("HX-Trigger") != "mealComponentsChanged"

    # Templates

    @pytest.mark.parametrize("method", ("put", "patch", "delete"))
    def test_get_template_names(self, user, meal_ingredient, method):
        """
        Non-GET requests to the view render with the correct template.
        """
        view = htmx.MealIngredientDetailView()
        data = {"ingredient": meal_ingredient.ingredient_id, "amount": 1}
        request = create_request(method, user, data)

        view.setup(request, pk=meal_ingredient.id)

        template = view.get_template_names()[0]
        assert template == "main/data/meal_ingredient_table_row.html"

    @pytest.mark.parametrize(
        ("template", "expected"),
        (
            ("regular", "main/data/meal_ingredient_table_row.html"),
            ("form", "main/data/meal_ingredient_row_form.html"),
            (None, "main/data/meal_ingredient_table_row.html"),
        ),
    )
    def test_get_template_names_get_method(
        self, user, meal_ingredient, template, expected
    ):
        """
        A GET request to the view renders with the correct template.
        """
        view = htmx.MealIngredientDetailView()
        data = {"template": template}
        if template is None:
            data = None

        request = create_request("get", user, data)

        view.setup(request, pk=meal_ingredient.id)

        assert view.get_template_names()[0] == expected

    # PATCH method

    def test_patch_request_less_than_min(self, user, meal_ingredient):
        """
        The MealIngredientDetail view does not accept PATCH requests
        with an amount value less than 0.1.
        """
        data = {"amount": 0}
        request = create_request("patch", user, data)

        response = self.view.as_view()(request, pk=meal_ingredient.pk)
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_patch_request_updates_entry(self, user, meal_ingredient):
        """
        A PATCH request to the MealIngredientDetail view updates the
        entry.
        """
        new_amount = 5
        data = {"amount": new_amount}
        request = create_request("patch", user, data)

        self.view.as_view()(request, pk=meal_ingredient.pk)

        meal_ingredient.refresh_from_db()
        assert meal_ingredient.amount == new_amount

    # DELETE method

    def test_delete_request_200_code(self, meal_ingredient, user):
        """
        A DELETE request to the MealIngredientDetail view returns an
        empty response with a 200 code.
        HTMX does not perform swaps when the response has a 204
        response.
        """
        request = create_request("delete", user)

        response = self.view.as_view()(request, pk=meal_ingredient.pk)

        assert response.status_code == HTTP_200_OK

    def test_delete_request_deletes_entry(self, user, meal_ingredient):
        """
        A DELETE request to the MealIngredientDetail removes the entry
        from the database.
        """
        request = create_request("delete", user)

        _ = self.view.as_view()(request, pk=meal_ingredient.pk)

        assert not models.MealIngredient.objects.filter(pk=meal_ingredient.pk).exists()

    @pytest.mark.parametrize(
        ("method", "num_queries"), (("get", 2), ("put", 4), ("patch", 4), ("delete", 3))
    )
    def test_num_queries(
        self, django_assert_num_queries, meal_ingredient, user, method, num_queries
    ):
        data = {"ingredient": meal_ingredient.ingredient_id, "amount": 10}
        request = create_request(method, user, data)

        with django_assert_num_queries(num_queries):
            # 1) Get meal_ingredient query
            # 2) Object permission
            # 3) Delete (DELETE request)
            # 3) Select ingredient from data - needed for the response
            # (PUT and PATCH)
            # 4) Update (PUT and PATCH)
            self.view.as_view()(request, pk=meal_ingredient.id)

    # Permissions

    def test_deny_permission_if_not_owner_of_the_meal(self, meal_ingredient, new_user):
        request = create_request("get", new_user)
        response = self.view.as_view()(request, pk=meal_ingredient.id)

        assert response.status_code == HTTP_403_FORBIDDEN

    # Session

    @pytest.mark.parametrize("method", ("get", "put", "patch", "delete"))
    def test_updates_last_meal_interact(
        self, user, meal_ingredient, ingredient_1, method
    ):
        data = {"ingredient": meal_ingredient.ingredient_id, "amount": 10}
        request = create_request(method, user, data, use_session=True)

        self.view.as_view()(request, pk=meal_ingredient.id)

        assert request.session.get("last_meal_interact")


class TestMealIngredientView:
    """Tests of the `MealIngredientView` view."""

    view = htmx.MealIngredientView()

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_endpoint_ok(self, logged_in_client, ingredient_1, meal, method):
        url = reverse("meal-ingredients", args=(meal.pk,))
        data = {"ingredient": ingredient_1.id, "amount": 1}

        response = getattr(logged_in_client, method)(url, data)

        assert is_success(response.status_code)

    # HTMX Event Trigger Headers

    @pytest.mark.parametrize(("method", "has_header"), (("get", False), ("post", True)))
    def test_successful_request_meal_changed_header(
        self, user, meal, ingredient_1, method, has_header
    ):
        """
        A successful request to the MealIngredient view
        returns a response with a `mealComponentsChanged` htmx trigger (except
        for GET requests).
        """
        data = {"amount": 5, "ingredient": ingredient_1.id}
        request = create_request(method, user, data)

        response = self.view.as_view()(request, meal_id=meal.pk)

        assert (
            response.headers.get("HX-Trigger") == "mealComponentsChanged"
        ) is has_header

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_invalid_request_no_meal_changed_header(self, user, meal, method):
        """
        An invalid request to the MealIngredient view
        returns a response without a `mealComponentsChanged` htmx trigger.
        """
        request = create_request(method, user)

        response = self.view.as_view()(request, meal_id=meal.id + 1)

        assert response.headers.get("HX-Trigger") != "mealComponentsChanged"

    # POST method

    def test_post_request_creates_meal_ingredient(self, user, ingredient_1, meal):
        """
        A valid 'POST' request to the MealIngredientView creates
        MealIngredient records.
        """
        data = {"ingredient": ingredient_1.id, "amount": 1}
        request = create_request("post", user, data)

        self.view.as_view()(request, meal_id=meal.id)

        assert models.MealIngredient.objects.filter(
            meal=meal, amount=1, ingredient=ingredient_1
        ).exists()

    def test_post_request_amount_less_than_min(self, user, meal, ingredient_1):
        """
        The MealIngredientView does not accept a POST request with an
        amount value less than 0.1 with bad request status code.
        """
        data = {"ingredient": ingredient_1.id, "amount": 0}
        request = create_request("post", user, data)

        response = self.view.as_view()(request, meal_id=meal.id)

        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_can_create_multiple_identical_meal_ingredients(
        self, logged_in_client, user, ingredient_1, meal
    ):
        """
        Repeated requests to the MealIngredientView create
        multiple MealIngredient records.
        """
        data = {"ingredient": ingredient_1.id, "amount": 1}
        request = create_request("post", user, data)

        self.view.as_view()(request, meal_id=meal.id)
        self.view.as_view()(request, meal_id=meal.id)

        count = models.MealIngredient.objects.filter(
            meal=meal, amount=1, ingredient=ingredient_1
        ).count()
        assert count == 2

    # Permissions

    def test_deny_permission_if_not_owner_of_the_meal(self, new_user, meal):
        request = create_request("get", new_user)

        response = self.view.as_view()(request, meal_id=meal.id)

        assert response.status_code == HTTP_403_FORBIDDEN

    # Templates

    @pytest.mark.parametrize(
        ("method", "template"),
        (
            ("get", "main/data/meal_ingredient_list.html"),
            ("post", "main/data/meal_ingredient_table_row.html"),
            ("delete", "main/data/meal_ingredient_list.html"),  # other
        ),
    )
    def test_get_template_names(self, user, meal, ingredient_1, method, template):
        """
        A GET request to the view renders with the correct template.
        """
        view = htmx.MealIngredientView()
        data = {"ingredient": ingredient_1.id, "amount": 1}
        request = create_request(method, user, data)

        view.setup(request, meal_id=meal.id)

        assert view.get_template_names()[0] == template

    # GET method

    def test_get_lists_meals_ingredients(self, user, meal, ingredient_1):
        """
        A GET request to the view renders the template with a list of
        the meal's ingredients in the context.
        """
        meal_ing = models.MealIngredient.objects.bulk_create(
            [
                models.MealIngredient(meal=meal, ingredient=ingredient_1, amount=1),
                models.MealIngredient(meal=meal, ingredient=ingredient_1, amount=2),
            ]
        )

        request = create_request("get", user)

        response = self.view.as_view()(request, meal_id=meal.id)

        ids = sorted([entry["id"] for entry in response.data["results"]])
        expected = sorted([mi.id for mi in meal_ing])
        assert ids == expected

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_num_queries(
        self, django_assert_num_queries, user, meal_ingredient, ingredient_2, method
    ):
        data = {"ingredient": ingredient_2.id, "amount": 1}
        request = create_request(method, user, data)

        with django_assert_num_queries(3):
            # GET
            # 1) Permission check
            # 2) count() query (pagination).
            # If the count is zero 3) is omitted.
            #
            # 3) Get meal_ingredients query

            # POST
            # 1) Permission Check
            # 2) Get ingredient's info (ingredient from data)
            # 3) Insert POST data
            self.view.as_view()(request, meal_id=meal_ingredient.meal_id)

    # Session

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_updates_last_meal_interact(self, user, meal, ingredient_1, method):
        data = {"ingredient": ingredient_1.id, "amount": 1}
        request = create_request(method, user, data, use_session=True)

        self.view.as_view()(request, meal_id=meal.id)

        assert request.session.get("last_meal_interact")


class TestCurrentMealView:
    """Tests of the CurrentMealView"""

    view = htmx.CurrentMealView()

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
        request = create_request("post", user, data, use_session=True)

        response = self.view.as_view()(request)

        assert response.headers["HX-Trigger"] == "currentMealChanged"

    def test_invalid_request_no_response_current_meal_changed_header(self, user):
        """
        A response from an invalid CurrentMealView request doesn't
        have a currentMealChanged htmx trigger header.
        """
        data = {}

        request = create_request("post", user, data, use_session=True)

        response = self.view.as_view()(request)

        assert response.headers.get("HX-Trigger") != "currentMealChanged"

    def test_creates_meal(self, user):
        """
        The CurrentMealView creates a new meal if there isn't one.
        """
        date_str = "2020-06-21"
        expected_date = date.fromisoformat(date_str)
        data = {"date": date_str}
        request = create_request("post", user, data, use_session=True)

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
        request = create_request(method, user, data, use_session=True)
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
        request = create_request(method, user, data, use_session=True)
        request.session["meal_id"] = meal.id

        response = self.view.as_view()(request)

        assert response.data.get("date_obj") == expected

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_context_doesnt_contain_meal_date_date_obj_if_template_renderer_wasnt_used(
        self, user, meal, method
    ):
        data = {"date": "2020-06-21"}
        request = create_request(
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
        request = create_request("post", user, data, use_session=True)

        self.view.as_view()(request)

        assert request.session.get("last_meal_interact")


class TestIngredientPreviewView:
    """Test of the ingredient preview view."""

    @pytest.fixture(autouse=True)
    def _set_up(self, ingredient_1, saved_profile):
        """Set up a get request to the ingredient detail view."""
        self.pk = ingredient_1.pk
        self.url = reverse("ingredient-preview", args=[self.pk])

    def test_uses_the_correct_template(self, client_with_meal):
        """IngredientPreview uses the preview template."""
        response = client_with_meal.get(self.url)

        assert response.templates[0].name == "main/data/ingredient_preview.html"

    def test_returns_404_if_no_current_meal_entry_exists(self, user, ingredient_1):
        """
        A GET request to the view returns with a 404 status code
        if there is no current meal set in the session.
        """
        request = create_request("get", user, use_session=True)

        response = htmx.IngredientPreviewView().as_view()(request, pk=ingredient_1.pk)

        assert response.status_code == HTTP_404_NOT_FOUND


class TestCurrentMealRedirectView:
    """Tests of the CurrentMealRedirectView class."""

    def test_meal_response_status_code(self, user, meal):
        """
        A request to the view returns a response with a redirect status code.
        """
        request = create_request("get", user, use_session=True)
        request.session["meal_id"] = meal.id
        view = htmx.CurrentMealRedirectView.as_view(pattern_name="meal-ingredients")

        response = view(request)

        assert is_redirect(response.status_code)

    @pytest.mark.parametrize(
        ("url_name", "redirect_url_name"),
        (
            ("current-meal-ingredients", "meal-ingredients"),
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
        request = create_request("get", user, use_session=True)
        view = htmx.CurrentMealRedirectView.as_view(pattern_name="meal-ingredients")

        # Checked with raises because the CurrentMealRedirectView is
        # not an APIView
        with pytest.raises(Http404):
            view(request)


class TestMealNutrientIntakeView:
    """Tests of the MealNutrientIntakeView class."""

    @pytest.fixture
    def _request(self, user, meal):
        """An authenticated request and user.

        Includes a session with a meal.
        """
        _request = create_request("get", user, use_session=True)
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
        view = htmx.MealNutrientIntakeView().as_view(display_order=display_order)

        response = view(_request, meal_id=meal.id)

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
        view = htmx.MealNutrientIntakeView().as_view(display_order=None)

        with django_assert_num_queries(8):
            # 1) Check if profile exists by user and related meal
            # (permission check)
            # 2) Get the meal (in this case meal already exists)
            # 3) Fetch profile. (In the Meal.objects.get_or_create() statement)
            # 4) Get MealIngredients associated with the meal. (Meal.get_intakes())
            # 5) Get IngredientNutrients associated with the MealIngredients.
            # (Meal.get_intakes())
            # 6) Get Nutrients with select_related child_type and energy. (queryset)
            # 7) `prefetch_related()` for the `types` field. (queryset)
            # 8) `prefetch_related()` for the `recommendations` field. (queryset)
            _ = view(_request, meal_id=meal.id)

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
        view = htmx.MealNutrientIntakeView().as_view(display_order=None)

        response = view(_request, meal_id=meal.id)

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
        view = htmx.MealNutrientIntakeView().as_view(display_order=display_order)

        response = view(_request, meal_id=meal.id)

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
        view = htmx.MealNutrientIntakeView().as_view(
            display_order=None, no_recommendations=["test_nutrient_2"]
        )

        response = view(_request, meal_id=meal.id)

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
        view = htmx.MealNutrientIntakeView().as_view(
            display_order=None, skip_amdr=["test_nutrient"]
        )

        response = view(_request, meal_id=meal.id)

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

        view = htmx.MealNutrientIntakeView().as_view(display_order=None)

        response = view(_request, meal_id=meal.id)

        assert len(response.data["results"][0]["nutrients"]) == num_nutrients

    def test_deny_permission_if_not_owner_of_the_meal(self, meal_ingredient, new_user):
        request = create_request("get", new_user, use_session=True)
        view = htmx.MealNutrientIntakeView().as_view(display_order=None)

        response = view(request, meal_id=meal_ingredient.meal_id)

        assert response.status_code == HTTP_403_FORBIDDEN

"""Tests of ComponentCollectionViewSet subclasses."""
import pytest
from core.models import Recipe
from core.views.api.meal_views import MealIngredientViewSet, MealRecipeViewSet
from core.views.api.recipe_views import RecipeIngredientViewSet
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, is_success

from tests.test_views.util import create_api_request


class BaseModelCollectionViewsetTests:
    """Base class for tests subclassing ModelCollectionViewset.

    Concrete classes inheriting from `BaseModelCollectionViewsetTests
    must implement the `collection`, `component` and `extra_component`
    fixtures, that return instances of their respective models.

    Required Attributes
    ------------------
    view_class: class
        The tested viewset class.
    url_pattern_base: str
        The base of the url's name in the url configuration.
        If the url names don't follow the <base>-list, <base>-detail
        convention, the get_pattern_name() method must be overriden.
    collection_change_header: str
        The HTMX event triggered when changes are made to the
        collection.
    """

    list_method_map = {"get": "list", "post": "create"}
    detail_method_map = {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }

    view_class = None
    collection_changed_header = None
    url_pattern_base = None

    def get_pattern_name(self, detail=False):
        """Get the url pattern name used for the view."""
        if detail:
            return f"{self.url_pattern_base}-detail"
        return f"{self.url_pattern_base}-list"

    @pytest.fixture
    def instance(self, collection, component, _setup):
        data = {
            self.list_lookup: collection,
            self.component_field: component,
            "amount": 1,
        }
        return self.model._default_manager.create(**data)

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.component_field = self.view_class.through_component_field_name()
        self.list_lookup = self.view_class.through_collection_field_name()
        self.model = self.view_class.through_model()

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_list_endpoint_ok(
        self, logged_in_api_client, component, collection, method
    ):
        url = reverse(self.get_pattern_name(), args=(collection.pk,))
        data = {self.component_field: component.id, "amount": 1}

        response = getattr(logged_in_api_client, method)(url, data)

        assert is_success(response.status_code)

    @pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
    def test_detail_endpoint_ok(self, logged_in_api_client, instance, method):
        url = reverse(self.get_pattern_name(True), args=(instance.pk,))

        response = getattr(logged_in_api_client, method)(
            url,
            {
                "amount": 5,
                self.component_field: getattr(instance, self.component_field).id,
                self.list_lookup: getattr(instance, self.list_lookup).id,
            },
        )

        assert is_success(response.status_code)

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_list_template_context_url_name(self, user, collection, component, method):
        data = {"amount": 5, self.component_field: component.id}
        request = create_api_request(method, user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        assert response.data["url_name"] == self.get_pattern_name(True)

    @pytest.mark.parametrize("method", ("get", "put", "patch"))
    def test_detail_template_context_url_name(self, user, instance, method):
        data = {
            "amount": 5,
            self.component_field: getattr(instance, self.component_field).id,
        }
        request = create_api_request(method, user, data)

        response = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )

        assert response.data["url_name"] == self.get_pattern_name(True)

    def test_create_template_context_component_name(self, user, collection, component):
        data = {"amount": 5, self.component_field: component.id}
        request = create_api_request("post", user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        assert response.data["component_name"] == component.name

    @pytest.mark.parametrize("method", ("get", "put", "patch"))
    def test_detail_template_context_component_name(
        self, user, instance, component, method
    ):
        data = {
            "amount": 5,
            self.component_field: getattr(instance, self.component_field).id,
        }
        request = create_api_request(method, user, data)

        response = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )

        assert response.data["component_name"] == component.name

    # HTMX Event Trigger Headers

    @pytest.mark.parametrize(("method", "has_header"), (("get", False), ("post", True)))
    def test_list_successful_request_has_a_collection_changed_response_header(
        self, user, collection, component, method, has_header
    ):
        data = {"amount": 5, self.component_field: component.id}
        request = create_api_request(method, user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        assert (
            response.headers.get("HX-Trigger") == self.collection_changed_header
        ) is has_header

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_list_invalid_request_has_no_collection_changed_response_header(
        self, user, collection, method
    ):
        request = create_api_request(method, user)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk + 1}

        response = view(request, **lookup)

        assert response.headers.get("HX-Trigger") != self.collection_changed_header

    @pytest.mark.parametrize(
        ("method", "has_header"), (("get", False), ("put", True), ("delete", True))
    )
    def test_detail_successful_request_has_a_collection_changed_response_header(
        self, user, instance, method, has_header
    ):
        data = {
            "amount": 5,
            self.component_field: getattr(instance, self.component_field).id,
            self.list_lookup: getattr(instance, self.list_lookup).id,
        }
        request = create_api_request(method, user, data)

        response = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )

        assert (
            response.headers.get("HX-Trigger") == self.collection_changed_header
        ) is has_header

    @pytest.mark.parametrize("method", ("get", "put", "delete"))
    def test_detail_invalid_request_has_no_collection_changed_response_header(
        self, user, instance, method
    ):
        request = create_api_request(method, user)

        response = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk + 1
        )

        assert response.headers.get("HX-Trigger") != self.collection_changed_header

    # Permissions

    def test_list_deny_permission_if_not_owner_of_the_collection(
        self, new_user, collection
    ):
        request = create_api_request("get", new_user)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        assert response.status_code == HTTP_403_FORBIDDEN

    def test_detail_deny_permission_if_not_owner_of_the_collection(
        self, instance, new_user
    ):
        request = create_api_request("get", new_user)
        view = self.view_class.as_view(self.detail_method_map, detail=True)
        response = view(request, pk=instance.id)

        assert response.status_code == HTTP_403_FORBIDDEN

    # Templates

    @pytest.mark.parametrize(
        ("method", "template"),
        (
            ("get", "core/data/collection_component_list.html"),
            ("post", "core/data/collection_component_list_table_row.html"),
        ),
    )
    def test_list_get_template_names(
        self, user, collection, component, method, template
    ):
        view = self.view_class(action=self.list_method_map[method], detail=False)
        data = {self.component_field: component.id, "amount": 1}
        request = create_api_request(method, user, data)
        lookup = {self.list_lookup: collection.pk}

        view.setup(request, **lookup)

        assert view.get_template_names()[0] == template

    @pytest.mark.parametrize("method", ("put", "patch"))
    def test_detail_get_template_names_non_get_http_methods(
        self, user, instance, method
    ):

        view = self.view_class(action=self.detail_method_map[method], detail=True)
        data = {
            self.component_field: getattr(instance, self.component_field).id,
            "amount": 1,
        }
        request = create_api_request(method, user, data)
        view.setup(request, pk=instance.id)

        template = view.get_template_names()[0]
        assert template == "core/data/collection_component_list_table_row.html"

    def test_delete_get_template_names_non_get_http_methods(
        self,
        user,
        instance,
    ):
        view = self.view_class(action=self.detail_method_map["delete"], detail=True)

        request = create_api_request("delete", user)
        view.setup(request, pk=instance.id)

        template = view.get_template_names()[0]
        assert template == "core/blank.html"

    @pytest.mark.parametrize(
        ("template", "expected"),
        (
            ("regular", "core/data/collection_component_list_table_row.html"),
            ("form", "core/data/collection_component_list_row_form.html"),
            (None, "core/data/collection_component_list_table_row.html"),
        ),
    )
    def test_detail_get_template_names_get_http_method(
        self, user, instance, template, expected
    ):
        view = self.view_class(action=self.detail_method_map["get"], detail=True)
        data = {"template": template}
        if template is None:
            data = None

        request = create_api_request("get", user, data)

        view.setup(request, pk=instance.id)

        assert view.get_template_names()[0] == expected

    # GET method

    def test_list_get_lists_model_entries(self, user, collection, component):
        """
        A GET request to the view renders the template with a list of
        the meal's ingredients in the context.
        """
        create_kwargs = {self.list_lookup: collection, self.component_field: component}
        instances = self.model._default_manager.bulk_create(
            [
                self.model(**create_kwargs, amount=1),
                self.model(**create_kwargs, amount=2),
            ]
        )
        request = create_api_request("get", user)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        ids = sorted([entry.id for entry in response.data["results"]])
        expected = sorted([i.id for i in instances])
        assert ids == expected

    def test_list_get_annotates_queryset_with_component_name(
        self, user, collection, component
    ):
        """
        A GET request to the view renders the template with a list of
        the meal's ingredients in the context.
        """
        create_kwargs = {
            self.list_lookup: collection,
            self.component_field: component,
        }
        instance = self.model._default_manager.create(**create_kwargs, amount=1)

        request = create_api_request("get", user)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        actual = response.data["results"][0].component_name
        expected = getattr(instance, self.component_field).name
        assert actual == expected

        # POST method

    def test_post_request_creates_model_entries(self, user, component, collection):
        data = {self.component_field: component.id, "amount": 1}
        request = create_api_request("post", user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        view(request, **lookup)

        lookup[self.component_field] = component
        assert self.model._default_manager.filter(**lookup, amount=1).exists()

    def test_post_request_amount_less_than_min_validation(
        self, user, collection, component
    ):
        data = {self.component_field: component.id, "amount": 0}
        request = create_api_request("post", user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        response = view(request, **lookup)

        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_post_can_create_multiple_identical_model_entries(
        self, user, component, collection
    ):
        data = {self.component_field: component.id, "amount": 1}
        request = create_api_request("post", user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        view(request, **lookup)
        view(request, **lookup)

        lookup[self.component_field] = component
        assert self.model._default_manager.filter(**lookup, amount=1).count() == 2

    # PATCH method

    def test_patch_request_less_than_min_amount_validation(self, user, instance):
        data = {"amount": 0}
        request = create_api_request("patch", user, data)

        response = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_patch_request_updates_entry(self, user, instance):
        new_amount = 5
        data = {"amount": new_amount}
        request = create_api_request("patch", user, data)

        self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )

        instance.refresh_from_db()
        assert instance.amount == new_amount

    # DELETE method

    def test_delete_request_deletes_model_entry(self, user, instance):
        request = create_api_request("delete", user)

        _ = self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=instance.pk
        )

        assert not self.model._default_manager.filter(pk=instance.pk).exists()

    # Number of queries

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_list_num_queries(
        self,
        django_assert_num_queries,
        user,
        instance,
        extra_component,
        collection,
        method,
    ):
        data = {self.component_field: extra_component.id, "amount": 1}
        request = create_api_request(method, user, data)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        with django_assert_num_queries(3):
            # GET
            # 1) Permission check
            # 2) count() query (pagination).
            # If the count is zero 3) is omitted.
            #
            # 3) Get model query

            # POST
            # 1) Permission Check
            # 2) Get component's info (component from data)
            # 3) Insert POST data
            view(request, **lookup)

    @pytest.mark.parametrize(
        ("method", "num_queries"), (("get", 2), ("put", 5), ("patch", 5), ("delete", 3))
    )
    def test_detail_num_queries(
        self, django_assert_num_queries, instance, user, method, num_queries
    ):
        data = {
            self.component_field: getattr(instance, self.component_field).id,
            self.list_lookup: getattr(instance, self.list_lookup).id,
            "amount": 10,
        }
        request = create_api_request(method, user, data)

        with django_assert_num_queries(num_queries):
            # 1) Get instance query
            # 2) Object permission
            # 3) Delete (DELETE request)
            # 3) Select collection for writable related field (PUT and
            # PATCH)
            # 4) Select component from data - needed for the response
            # (PUT and PATCH)
            # 5) Update (PUT and PATCH)
            view = self.view_class.as_view(self.detail_method_map, detail=True)
            view(request, pk=instance.id)


class TestMealIngredientViewset(BaseModelCollectionViewsetTests):
    """Tests of the MealIngredientViewset class."""

    view_class = MealIngredientViewSet
    collection_changed_header = "mealComponentsChanged"
    url_pattern_base = "meal-ingredient"

    @pytest.fixture
    def collection(self, meal):
        return meal

    @pytest.fixture
    def component(self, ingredient_1):
        return ingredient_1

    @pytest.fixture
    def extra_component(self, ingredient_2):
        return ingredient_2

    @pytest.fixture
    def instance(self, meal_ingredient):
        return meal_ingredient

    # Session

    @pytest.mark.parametrize("method", ("get", "put", "patch", "delete"))
    def test_detail_updates_last_meal_interact(self, user, meal_ingredient, method):
        data = {"ingredient": meal_ingredient.ingredient_id, "amount": 10}
        request = create_api_request(method, user, data, use_session=True)

        self.view_class.as_view(self.detail_method_map, detail=True)(
            request, pk=meal_ingredient.id
        )

        assert request.session.get("last_meal_interact")

    @pytest.mark.parametrize("method", ("get", "post"))
    def test_list_updates_last_meal_interact(self, user, collection, component, method):
        data = {self.component_field: component.id, "amount": 1}
        request = create_api_request(method, user, data, use_session=True)
        view = self.view_class.as_view(self.list_method_map, detail=False)
        lookup = {self.list_lookup: collection.pk}

        view(request, **lookup)

        assert request.session.get("last_meal_interact")


class TestRecipeIngredientViewset(BaseModelCollectionViewsetTests):
    """Tests of the RecipeIngredientDetail View"""

    view_class = RecipeIngredientViewSet
    collection_changed_header = "recipeComponentsChanged"
    url_pattern_base = "recipe-ingredient"

    @pytest.fixture
    def collection(self, recipe):
        return recipe

    @pytest.fixture
    def component(self, ingredient_1):
        return ingredient_1

    @pytest.fixture
    def extra_component(self, ingredient_2):
        return ingredient_2

    @pytest.fixture
    def instance(self, recipe_ingredient):
        return recipe_ingredient


class TestMealRecipeViewset(BaseModelCollectionViewsetTests):
    """Tests of the RecipeIngredientDetail View"""

    view_class = MealRecipeViewSet
    collection_changed_header = "mealComponentsChanged"
    url_pattern_base = "meal-recipe"

    @pytest.fixture
    def collection(self, meal):
        return meal

    @pytest.fixture
    def component(self, recipe):
        return recipe

    @pytest.fixture
    def extra_component(self, meal):
        """Recipe instance.

        name: "S"
        owner: saved_profile

        ingredient: ingredient_1
        amount: 50
        """
        recipe_2 = Recipe.objects.create(owner=meal.owner, name="S")

        return recipe_2

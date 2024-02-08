"""Tests of main app's regular (non-api) views."""
from datetime import date

from django.urls import reverse
from django.utils import timezone
from main import models
from main.views import main as views
from rest_framework.status import is_success

from .util import add_session, add_session_and_meal


class TestProfileView:
    """Tests of the profile view."""

    def test_endpoint_ok(self, logged_in_client):
        url = reverse("profile")
        response = logged_in_client.get(url)

        assert is_success(response.status_code)

    def test_passes_get_param_to_data(self, rf, user):
        request = rf.get("/?next=/")
        request.user = user
        view = views.ProfileView()
        view.setup(request)

        data = view.get_context_data()

        assert data["next"] == "/"


class TestMealView:
    """Tests of the meal view."""

    def test_endpoint_ok(self, logged_in_client, saved_profile):
        url = reverse("meal")

        response = logged_in_client.get(url)

        assert is_success(response.status_code)

    def test_no_session_meal_creates_meal_if_does_not_exist(
        self, rf, user, saved_profile
    ):
        request = rf.get("")
        request.user = user
        add_session(request)
        view = views.MealView.as_view()

        view(request)

        assert models.Meal.objects.filter(
            owner=saved_profile, date=date.today()
        ).exists()

    def test_num_queries_no_meal(
        self, django_assert_num_queries, rf, user, saved_profile
    ):
        request = rf.get("")
        request.user = user
        add_session(request)
        view = views.MealView.as_view()

        with django_assert_num_queries(4):
            # 1)-4) Get or create a meal
            view(request)

    def test_num_queries(self, django_assert_num_queries, rf, user, meal):
        request = rf.get("")
        request.user = user
        add_session_and_meal(request, meal)
        view = views.MealView.as_view()

        with django_assert_num_queries(0):
            view(request)

    # Session
    def test_no_session_meal_adds_meal_id(self, rf, user, saved_profile):
        request = rf.get("")
        request.user = user
        add_session(request)
        view = views.MealView.as_view()

        view(request)

        assert request.session.get("meal_id")

    def test_updates_last_meal_interact(self, rf, user, meal):
        view = views.MealView.as_view()
        request = rf.get("")
        request.user = user
        add_session_and_meal(request, meal)

        view(request)

        assert request.session.get("last_meal_interact")

    def test_updates_meal_if_expired(self, rf, user, meal, settings):
        view = views.MealView.as_view()
        request = rf.get("")
        request.user = user
        add_session_and_meal(request, meal)
        session = request.session
        session["last_meal_interact"] = str(timezone.now())
        session.save()
        settings.MEAL_EXPIRY_TIME = 0

        view(request)

        assert request.session.get("meal_id") != meal.id


class TestRecipeEditView:
    def test_endpoint_ok(self, recipe, logged_in_client):
        url = reverse("recipe-edit", args=(recipe.slug,))

        response = logged_in_client.get(url)

        assert is_success(response.status_code)

    def test_get_context_data_retrieves_recipe_by_slug_and_owner(
        self, recipe, rf, user
    ):
        request = rf.get("", kwargs=(recipe.slug,))
        request.user = user
        view = views.RecipeEditView()
        view.setup(request, slug=recipe.slug)

        data = view.get_context_data()

        assert data["recipe"] == recipe

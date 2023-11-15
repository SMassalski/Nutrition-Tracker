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

    url = reverse("profile")
    default_data = {
        "age": 20,
        "sex": "M",
        "activity_level": "A",
        "height": 178,
        "weight": 75,
    }

    def test_post_request_creates_a_profile_record(self, user, logged_in_client):
        """
        A correct POST request to profile_view creates a new profile
        record for a logged-in user.
        """
        logged_in_client.post(
            self.url,
            data=self.default_data,
        )

        assert hasattr(user, "profile")

    def test_post_request_updates_a_profile_record(
        self, user, logged_in_client, saved_profile
    ):
        """
        A correct POST request to profile_view updates user's profile
        record for a logged-in user.
        """
        logged_in_client.post(
            self.url,
            data=self.default_data,
        )

        saved_profile.refresh_from_db()
        assert saved_profile.activity_level == "A"

    def test_get_detects_redirect_from_registration(self, logged_in_client):
        """
        Profile view passes to context a boolean indicating the url
        contained the query param 'from` = `registration'.
        """
        url = f"{self.url}?from=registration"

        response = logged_in_client.get(url)

        assert response.context.get("from_registration") is True

    def test_invalid_post_request(self, logged_in_client, user):
        """
        Profile view post request with invalid data does not save the user's
        profile.
        """
        logged_in_client.post(
            self.url,
            data={
                "age": 20,
                "sex": 4,
                "activity_level": "A",
                "height": 178,
            },
        )

        assert not hasattr(user, "profile")


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

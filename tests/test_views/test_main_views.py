"""Tests of main app's regular (non-api) views."""
import pytest
from django.test import RequestFactory
from django.urls import reverse
from main import models
from main.views import main as views


@pytest.fixture
def nutrient_type(db, nutrient_1):
    """A sample NutrientType record.

    name: Test type
    displayed_name: Displayed name
    nutrient: nutrient_1
    """
    instance = models.NutrientType.objects.create(
        name="Test type", displayed_name="Displayed name"
    )
    nutrient_1.types.add(instance)
    return instance


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

    def test_post_request_creates_a_profile_record(self, db, user, logged_in_client):
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
        self, db, user, logged_in_client, saved_profile
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

    def test_get_detects_redirect_from_registration(self, logged_in_client, db):
        """
        Profile view passes to context a boolean indicating the url
        contained the query param 'from` = `registration'.
        """
        url = f"{self.url}?from=registration"

        response = logged_in_client.get(url)

        assert response.context.get("from_registration") is True

    def test_invalid_post_request(self, logged_in_client, db, user):
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

    url = reverse("create-meal")

    @pytest.fixture(autouse=True)
    def setup_request(self, db, user):
        """Set up request and user."""
        self.default_request = RequestFactory().get(self.url)
        self.default_request.user = user
        self.user = user

    @pytest.fixture(autouse=True)
    def setup_profile(self, db, saved_profile):
        """Set up user profile."""
        self.profile = saved_profile

    @pytest.fixture(autouse=True)
    def setup_default_view(self, setup_request):
        """Meal view setup with the default request"""
        self.view = views.MealView()
        self.view.setup(self.default_request)

    @pytest.fixture
    def saved_recommendation(self, recommendation):
        recommendation.save()
        return recommendation

    # TODO: Tests
    #   - progress min 100 (later)
    #   - progress round (later)
    #   - context keys

    # TODO: For now intakes are randomly generated. Finish the tests
    #   when the intakes are retrieved from meals.
    # def test_meal_view_over_limit_true(self):
    #     """
    #     Meal view correctly determines when an intake is higher than the
    #     tolerable upper intake level.
    #     """
    #
    # def test_meal_view_over_limit_false(self):
    #     """
    #     Meal view correctly determines when an intake is below the
    #     tolerable upper intake level.
    #     """

    def test_progress_zero_amount(self, recommendation, nutrient_type, db):
        """
        Meal view determines the `progress` value to be None if the
        target amount is 0.
        """
        type_key = nutrient_type.name.replace(" ", "_")
        recommendation.amount_min = 0
        recommendation.save()

        context = self.view.get_context_data()

        progress = context["nutrients"][type_key]["nutrients"][0]["progress"]
        assert progress is None

    def test_progress_none_amount(self, recommendation, nutrient_type, db):
        """
        Meal view determines the `progress` value to be None if the
        target amount is None.
        """
        type_key = nutrient_type.name.replace(" ", "_")
        recommendation.amount_min = None
        recommendation.save()

        context = self.view.get_context_data()

        progress = context["nutrients"][type_key]["nutrients"][0]["progress"]
        assert progress is None

    def test_nutrient_key_in_snake_case(self, saved_recommendation, nutrient_type, db):
        """
        Meal view `nutrients` context dict keys are nutrient_types
        converted to snake_case.
        """
        snake_case_type = nutrient_type.name.replace(" ", "_")

        context = self.view.get_context_data()

        assert snake_case_type in context["nutrients"]
        assert nutrient_type.name not in context["nutrients"]

    def test_nutrient_name_uses_displayed_name(
        self, saved_recommendation, nutrient_type, db
    ):
        """
        Meal view sets each type's in `nutrients` name value to the value
        of the NutrientType's displayed name.
        """
        type_key = nutrient_type.name.replace(" ", "_")

        name = self.view.get_context_data()["nutrients"][type_key]["name"]

        assert name == "Displayed name"

    def test_nutrient_name_uses_name_when_no_displayed_name(
        self, nutrient_1, saved_recommendation, db, nutrient_type
    ):
        """
        Meal view sets each type's in `nutrients` name value to the
        value of the NutrientType's `name` field if `displayed_name` is
        `None`.
        """
        nutrient_type.displayed_name = None
        nutrient_type.save()
        type_key = nutrient_type.name.replace(" ", "_")

        name = self.view.get_context_data()["nutrients"][type_key]["name"]

        assert name == "Test type"

    def test_displayed_nutrients_keys_in_snake_case(self, db):
        """
        Meal view `displayed_nutrient` keys are `display_order` elements
        converted to snake case.
        """
        self.view.display_order = ("Test type",)

        context = self.view.get_context_data()

        expected = ("Test_type",)
        result = tuple(context["displayed_nutrients"].keys())
        assert result == expected

    def test_displayed_nutrients_preserves_order(self, db):
        """
        Meal view `displayed_nutrient` preserves the order of elements
        in `display_order`.
        """

        self.view.display_order = ("Test type", "Test type 2")

        context = self.view.get_context_data()

        expected = ("Test_type", "Test_type_2")
        result = tuple(context["displayed_nutrients"].keys())
        assert result == expected

    def test_context_keys(self, db):
        """Meal view context has the correct keys."""
        context = self.view.get_context_data()

        assert "nutrients" in context
        assert "displayed_nutrients" in context

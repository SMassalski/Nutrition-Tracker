"""Tests of main app's regular (non-api) views."""
import pytest
from django.test import RequestFactory
from django.urls import reverse
from main import models
from main.views import main as views


def test_profile_post_request_creates_a_profile_record(db, user, logged_in_client):
    """
    A correct POST request to profile_view creates a new profile
    record for a logged-in user.
    """
    url = reverse("profile")
    logged_in_client.post(
        url,
        data={
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
            "weight": 75,
        },
    )
    assert hasattr(user, "profile")


def test_profile_post_request_updates_a_profile_record(db, user, logged_in_client):
    """
    A correct POST request to profile_view updates user's profile
    record for a logged-in user.
    """
    profile = models.Profile(
        age=20, sex="M", activity_level="VA", height=178, user=user, weight=75
    )
    profile.save()
    url = reverse("profile")
    logged_in_client.post(
        url,
        data={
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
            "weight": 75,
        },
    )
    profile.refresh_from_db()
    assert profile.activity_level == "A"


def test_profile_get_detects_redirect_from_registration(logged_in_client, db):
    """
    Profile view passes to context a boolean indicating the url
    contained the query param 'from' set to 'registration'.
    """
    url = f"{reverse('profile')}?from=registration"
    response = logged_in_client.get(url)

    assert response.context.get("from_registration") is True


def test_profile_view_invalid_post_request(logged_in_client, db, user):
    """
    Profile view post request with invalid data does not save the user's
    profile.
    """
    url = reverse("profile")
    logged_in_client.post(
        url,
        data={
            "age": 20,
            "sex": 4,
            "activity_level": "A",
            "height": 178,
        },
    )
    user.refresh_from_db()
    assert not hasattr(user, "profile")


@pytest.fixture(scope="class")
def nutrient_type(django_db_blocker, nutrient_1):
    """A sample NutrientType record"""
    with django_db_blocker.unblock():
        instance = models.NutrientType.objects.create(
            name="Test type", displayed_name="Displayed name"
        )
        nutrient_1.types.add(instance)
    return instance


class TestMealView:
    """Tests of the meal view."""

    url = reverse("create-meal")
    default_request = RequestFactory().get(url)

    @pytest.fixture(autouse=True, scope="class")
    def _setup(self, user, django_db_blocker):
        """Set up a client and user profile."""
        self.default_request.user = user
        self.user = user
        with django_db_blocker.unblock():
            self.profile = models.Profile.objects.create(
                user=user, age=20, height=180, activity_level="A", sex="M", weight=80
            )
        yield
        with django_db_blocker.unblock():
            self.profile.delete()

    @pytest.fixture
    def default_view(self):
        """Meal view setup with the default request"""
        view = views.MealView()
        view.setup(self.default_request)
        return view

    @pytest.fixture
    def recommendation(self, nutrient_1, db):
        """A sample saved IntakeRecommendation instance."""

        return models.IntakeRecommendation.objects.create(
            nutrient=nutrient_1,
            age_min=0,
            sex="B",
            dri_type=models.IntakeRecommendation.RDA,
            amount_min=0,
        )

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

    def test_meal_view_progress_zero_amount(
        self, recommendation, nutrient_type, db, default_view
    ):
        """
        Meal view determines the `progress` value to be None if the
        target amount is 0.
        """
        type_key = nutrient_type.name.replace(" ", "_")
        recommendation.amount_min = 0
        recommendation.save()

        context = default_view.get_context_data()

        progress = context["nutrients"][type_key]["nutrients"][0]["progress"]
        assert progress is None

    def test_meal_view_progress_none_amount(
        self, recommendation, nutrient_type, db, default_view
    ):
        """
        Meal view determines the `progress` value to be None if the
        target amount is None.
        """
        type_key = nutrient_type.name.replace(" ", "_")
        recommendation.amount_min = None
        recommendation.save()

        context = default_view.get_context_data()

        progress = context["nutrients"][type_key]["nutrients"][0]["progress"]
        assert progress is None

    def test_meal_view_nutrient_key_in_snake_case(
        self, recommendation, nutrient_type, db, default_view
    ):
        """
        Meal view nutrients context dict keys are nutrient_types
        converted to snake_case.
        """
        snake_case_type = nutrient_type.name.replace(" ", "_")
        context = default_view.get_context_data()
        assert snake_case_type in context["nutrients"]
        assert nutrient_type.name not in context["nutrients"]

    def test_meal_view_nutrient_name_uses_displayed_name(
        self, recommendation, nutrient_type, db, default_view
    ):
        """
        Meal view sets each type's in nutrients name value to the value
        of the NutrientType's displayed name.
        """
        type_key = nutrient_type.name.replace(" ", "_")

        name = default_view.get_context_data()["nutrients"][type_key]["name"]

        assert name == "Displayed name"

    def test_meal_view_nutrient_name_uses_name_when_no_displayed_name(
        self, nutrient_1, recommendation, db, default_view
    ):
        """
        Meal view sets each type's in nutrients name value to the value
        of the NutrientType's display name.
        """
        # nutrient_type = models.NutrientType.objects.create(name="Test type 2")
        nutrient_type = nutrient_1.types.create(name="Test type 2")
        type_key = nutrient_type.name.replace(" ", "_")

        name = default_view.get_context_data()["nutrients"][type_key]["name"]

        assert name == "Test type 2"

    def test_meal_view_displayed_nutrients_keys_in_snake_case(self, db, default_view):
        """
        Meal view `displayed_nutrient` keys are `display_order` elements
        converted to snake case.
        """
        expected = ("Test_type",)

        default_view.display_order = ("Test type",)

        context = default_view.get_context_data()
        assert tuple(context["displayed_nutrients"].keys()) == expected

    def test_meal_view_displayed_nutrients_preserves_order(self, db, default_view):
        """
        Meal view `displayed_nutrient` preserves the order of elements
        in `display_order`.
        """
        expected = ("Test_type", "Test_type_2")

        default_view.display_order = ("Test type", "Test type 2")

        context = default_view.get_context_data()
        assert tuple(context["displayed_nutrients"].keys()) == expected

    def test_meal_view_context_keys(self, db, default_view):
        """Meal view context has the correct keys."""
        context = default_view.get_context_data()

        assert "nutrients" in context
        assert "displayed_nutrients" in context

import pytest
from authentication.models import User
from core.admin import MealAdmin, RecipeAdmin, WeightMeasurementAdmin
from core.models import Meal, Recipe, WeightMeasurement
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from rest_framework.status import is_success


@pytest.fixture
def admin_user(db):
    """User instance with admin permissions.

    username: admin
    """
    return User.objects.create_superuser("admin")


@pytest.fixture
def admin_client(client, admin_user):
    """Client with the admin user logged in."""
    client.force_login(admin_user)
    return client


class TestMealAdmin:
    @pytest.fixture
    def admin(self):
        """A MealAdmin instance."""
        return MealAdmin(model=Meal, admin_site=AdminSite())

    def test_user_display_returns_username(self, meal, admin, admin_user):
        expected = "test_user"  # username of the user fixture

        actual = admin.user(meal)

        assert actual == expected

    def test_clear_empty_meals_view_endpoint_ok(self, admin_client):
        url = reverse("admin:empty-meals")

        response = admin_client.delete(url)

        assert is_success(response.status_code)

    def test_clear_empty_meals_view_requires_admin_permissions(self, rf, user, admin):
        request = rf.delete("")
        request.user = user
        permission = Permission.objects.get(codename="delete_meal")

        with pytest.raises(PermissionDenied):
            admin.clear_empty_meals(request)

        user.user_permissions.add(permission)

        # New instance is needed because of permission caching
        user = User.objects.get(id=user.id)

        request = rf.delete("")
        request.user = user

        try:
            admin.clear_empty_meals(request)
        except PermissionDenied:
            pytest.fail()

    def test_clear_empty_meals_view_deletes_empty_meals(
        self, rf, admin_user, admin, meal
    ):
        request = rf.delete("")
        request.user = admin_user

        admin.clear_empty_meals(request)

        assert not Meal.objects.all().exists()

    def test_clear_empty_meals_view_has_refresh_header(
        self, rf, admin_user, admin, meal
    ):
        request = rf.delete("")
        request.user = admin_user

        response = admin.clear_empty_meals(request)

        assert response.headers.get("HX-Refresh") == "true"


class TestRecipeAdmin:
    def test_user_display_returns_username(self, recipe):
        admin = RecipeAdmin(model=Recipe, admin_site=AdminSite())
        expected = "test_user"  # username of the user fixture

        actual = admin.user(recipe)

        assert actual == expected


class TestWeightMeasurementAdmin:
    def test_user_display_returns_username(self, weight_measurement):
        admin = WeightMeasurementAdmin(model=WeightMeasurement, admin_site=AdminSite())
        expected = "test_user"  # username of the user fixture

        actual = admin.user(weight_measurement)

        assert actual == expected

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client_with_meal(logged_in_client, meal):
    """
    A logged-in client with a current meal date set in its session.

    The date is the date of the meal from the meal fixture (2020-06-15).
    """
    session = logged_in_client.session
    session["meal_id"] = meal.id
    session.save()

    return logged_in_client


@pytest.fixture
def logged_in_api_client(user):
    """An APIClient authenticated with the user fixture."""
    client = APIClient()
    client.force_login(user)
    return client

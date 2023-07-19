import pytest


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

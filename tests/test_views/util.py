"""Utility functions for view tests."""
from django.contrib.sessions.middleware import SessionMiddleware


def add_session(request):
    """Add a session to a request.

    This function is specifically for RequestFactory requests.

    Parameters
    ----------
    request: django.http.request.HttpRequest
        The request the session will be added to.

    Returns
    -------
    django.http.request.HttpRequest
    """
    middleware = SessionMiddleware(lambda x: None)  # __init__ requires a callback
    middleware.process_request(request)
    return request


def add_session_and_meal(request, meal):
    """Add a session and `current_meal_date` session arg to a request.

    This function is specifically for RequestFactory requests.

    Parameters
    ----------
    request: django.http.request.HttpRequest
        The request the session will be added to.
    meal: main.models.Meal
        The meal of which the date will be used as the
        `current_meal_date`.

    Returns
    -------
    django.http.request.HttpRequest
    """
    add_session(request)
    session = request.session
    session["meal_id"] = meal.id
    session.save()

    return request

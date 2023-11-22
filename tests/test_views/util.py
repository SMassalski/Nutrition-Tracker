"""Utility functions for view tests."""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from rest_framework.test import APIRequestFactory, force_authenticate


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


def create_api_request(
    method, user=None, data=None, format=None, use_session=False, query_params=None
):
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
    query_params: dict
        Additional query parameters to include in the request.

    Returns
    -------
    django.core.handlers.wsgi.WSGIRequest
    """
    params = {}
    params.update(query_params or {})
    if format:
        params["format"] = format
    path = f"?{urlencode(params)}" if params else ""

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


def is_pagination_on() -> bool:
    """Check if DRF pagination is enabled globally."""
    return (
        settings.REST_FRAMEWORK.get("PAGE_SIZE") is None
        or settings.REST_FRAMEWORK.get("DEFAULT_PAGINATION_CLASS") is None
    )

"""Helper functions for session-related features."""
from datetime import datetime, timedelta

from django.conf import settings
from django.http import Http404
from django.utils import timezone

LAST_INTERACT_KEY = "last_meal_interact"


def is_meal_expired(request):
    """Check if the session's current meal is expired.

    This function doesn't raise an exception if the request doesn't have
    a session.

    Parameters
    ----------
    request
    The request to be checked.

    Returns
    -------
    bool
        `True` if the meal is expired. `False` if either the meal has
        not yet expired or the request doesn't have a session.
    """
    if not hasattr(request, "session"):
        return False

    exp_time = settings.MEAL_EXPIRY_TIME
    last_modified_str = request.session.get(LAST_INTERACT_KEY)

    # Meal expiration is turned off.
    if exp_time is None:
        return False

    # No current meal
    if last_modified_str is None:
        return False

    last_modified = datetime.fromisoformat(last_modified_str)
    return last_modified + timedelta(seconds=exp_time) < timezone.now()


def ping_meal_interact(request):
    """Update the last meal interaction time to now."""
    if not hasattr(request, "session"):
        return

    request.session[LAST_INTERACT_KEY] = str(timezone.now())


def get_current_meal_id(request, raise_404=False):
    """Get the id of the session's current meal.

    Parameters
    ----------
    request: HttpRequest
        The request for which the id will be retrieved.
    raise_404: bool
        Raise Http404 if the `request`'s session does not have a set
        meal.

    Returns
    -------
    int
    """
    if not hasattr(request, "session"):
        raise NoSessionException("Request doesn't have a session.")

    meal_id = request.session.get("meal_id")
    if meal_id is None:
        if raise_404:
            raise Http404("No current meal set.")
        raise NoCurrentMealException("Request's session does not have a set meal.")

    return meal_id


class NoSessionException(AttributeError):
    """
    Raised when a request with a session is required but the request
    doesn't have one.
    """


class NoCurrentMealException(AttributeError):
    """Raised when the request's session doesn't have a set meal."""

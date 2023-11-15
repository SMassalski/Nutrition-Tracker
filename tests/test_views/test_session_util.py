"""Tests of the session utility functions."""
from datetime import datetime, timedelta

import pytest
from django.http import Http404
from django.utils import timezone
from main.views.session_util import (
    LAST_INTERACT_KEY,
    NoCurrentMealException,
    NoSessionException,
    get_current_meal_id,
    is_meal_expired,
    ping_meal_interact,
)

from .util import add_session, add_session_and_meal


@pytest.fixture
def _request(rf):
    """Simple GET WSGIRequest."""
    return rf.get("")


@pytest.fixture
def request_with_session(_request):
    """Simple GET WSGIRequest with a session."""
    add_session(_request)
    return _request


class TestIsMealExpired:
    def test_request_without_session_always_false(self, _request):
        assert not is_meal_expired(_request)

    def test_none_expiry_time_always_false(self, request_with_session, settings):
        request_with_session.session[LAST_INTERACT_KEY] = str(timezone.now())
        settings.MEAL_EXPIRY_TIME = None

        assert not is_meal_expired(request_with_session)

    def test_no_meal_interact_always_false(self, request_with_session):
        assert not is_meal_expired(_request)

    def test_meal_expired(self, request_with_session, settings):
        request_with_session.session[LAST_INTERACT_KEY] = str(timezone.now())
        settings.MEAL_EXPIRY_TIME = 0

        assert is_meal_expired(request_with_session)


class TestPingMealInteract:
    def test_updates_last_interact(self, request_with_session):
        old_interact_time = timezone.now() - timedelta(hours=1)
        request_with_session.session[LAST_INTERACT_KEY] = str(old_interact_time)

        ping_meal_interact(request_with_session)

        new_time = timezone.now()
        session_new_time = datetime.fromisoformat(
            request_with_session.session[LAST_INTERACT_KEY]
        )
        assert abs(new_time - session_new_time) < timedelta(seconds=1)

    def test_request_without_session_no_error(self, _request):

        try:
            ping_meal_interact(_request)
        except AttributeError:
            pytest.fail(
                "ping_meal_interact raised an AttributeError while processing a request"
                " without a session."
            )


class TestGetCurrentMealId:
    def test_request_without_session_raises_error(self, _request):

        with pytest.raises(NoSessionException):
            get_current_meal_id(_request)

    def test_request_without_current_meal_raises_error(self, request_with_session):

        with pytest.raises(NoCurrentMealException):
            get_current_meal_id(request_with_session)

    def test_request_without_current_meal_raise404_true(self, request_with_session):

        with pytest.raises(Http404):
            get_current_meal_id(request_with_session, raise_404=True)

    def test_retrieves_id(self, _request, meal):
        add_session_and_meal(_request, meal)

        meal_id = get_current_meal_id(_request)

        assert meal_id == meal.id

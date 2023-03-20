"""Tests of main app's regular (non-api) views."""
from django.urls import reverse
from main.models import Profile


def test_profile_post_request_creates_a_profile_record(db, user, client):
    """
    A correct POST request to profile_view creates a new profile
    record for a logged-in user.
    """
    url = reverse("profile")
    client.force_login(user)
    client.post(
        url,
        data={
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
        },
    )
    assert hasattr(user, "profile")


def test_profile_post_request_updates_a_profile_record(db, user, client):
    """
    A correct POST request to profile_view updates user's profile
    record for a logged-in user.
    """
    profile = Profile(age=20, sex="M", activity_level="VA", height=178, user=user)
    profile.save()
    url = reverse("profile")
    client.force_login(user)
    client.post(
        url,
        data={
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
        },
    )
    profile.refresh_from_db()
    assert profile.activity_level == "A"


def test_profile_get_detects_redirect_from_registration(client, user, db):
    """
    Profile view passes to context a boolean indicating the url
    contained the query param 'from' set to 'registration'.
    """
    client.force_login(user)
    url = f"{reverse('profile')}?from=registration"
    response = client.get(url)

    assert response.context.get("from_registration") is True


def test_profile_view_invalid_post_request(client, db, user):
    """
    Profile view post request with invalid data does not save the user's
    profile.
    """
    client.force_login(user)
    url = reverse("profile")
    client.post(
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

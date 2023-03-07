"""Tests of authentication views."""
from authentication.views import register_user
from django.contrib.auth.models import AnonymousUser
from main.models import User
from rest_framework import status
from rest_framework.reverse import reverse


def test_registration_view_get_status_code(rf):
    """Registration view get returns a response with 200 status code."""
    url = reverse("registration")
    request = rf.get(url)
    request.user = AnonymousUser()
    response = register_user(request)
    assert response.status_code == status.HTTP_200_OK


def test_registration_view_redirects_logged_in_users(rf, user):
    """Registration view redirects logged-in user."""
    url = reverse("registration")
    request = rf.get(url)
    request.user = user
    response = register_user(request)
    assert response.status_code == status.HTTP_302_FOUND


def test_registration_view_post_creates_a_user(db, client):
    """Successful registration post request creates a user."""
    url = reverse("registration")
    client.post(
        url,
        data={
            "username": "new_test_username",
            "password1": "tZxvsp7xpCUmJ4f",
            "password2": "tZxvsp7xpCUmJ4f",
            "email": "email@test.com",
        },
    )
    assert User.objects.filter(username="new_test_username").exists()


def test_registration_view_successful_post_request_redirect(db, client):
    """Successful registration post request returns a redirect."""
    url = reverse("registration")
    response = client.post(
        url,
        data={
            "username": "new_test_username",
            "password1": "tZxvsp7xpCUmJ4f",
            "password2": "tZxvsp7xpCUmJ4f",
            "email": "email@test.com",
        },
    )
    assert response.status_code == status.HTTP_302_FOUND


def test_registration_view_invalid_post_data_request_status_code(db, client):
    """
    Registration post request returns a with status code 200 if the post
    data is invalid.
    """
    url = reverse("registration")
    response = client.post(
        url,
        data={
            "username": "new_test_username",
            "password1": "1234",
            "password2": "1",
            "email": "email",
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_registration_view_successful_post_request_login(db, client):
    """Successful registration post request logs in the user."""
    url = reverse("registration")
    response = client.post(
        url,
        data={
            "username": "new_test_username",
            "password1": "tZxvsp7xpCUmJ4f",
            "password2": "tZxvsp7xpCUmJ4f",
            "email": "email@test.com",
        },
        follow=True,
    )
    user = response.context["user"]
    assert isinstance(user, User)
    assert user.username == "new_test_username"

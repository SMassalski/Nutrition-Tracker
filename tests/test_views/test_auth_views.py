"""Tests of authentication views."""
import pytest
from authentication.models import User
from authentication.views import register_user
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.reverse import reverse


class TestRegistrationView:
    """Tests of the registration view."""

    url = reverse("registration")
    default_data = {
        "username": "new_test_username",
        "password1": "tZxvsp7xpCUmJ4f",
        "password2": "tZxvsp7xpCUmJ4f",
        "email": "email@test.com",
    }

    @pytest.fixture
    def request_get(self, rf):
        """A GET request to the registration view."""
        request = rf.get(self.url)
        return request

    def test_registration_view_get_status_code(self, request_get):
        """Registration view get returns a response with 200 status code."""
        request_get.user = AnonymousUser()

        response = register_user(request_get)

        assert response.status_code == status.HTTP_200_OK

    def test_registration_view_redirects_logged_in_users(self, request_get, user):
        """Registration view redirects logged-in user."""
        request_get.user = user

        response = register_user(request_get)

        assert response.status_code == status.HTTP_302_FOUND

    def test_registration_view_post_creates_a_user(self, db, client):
        """Successful registration post request creates a user."""
        client.post(self.url, data=self.default_data)

        assert User.objects.filter(username="new_test_username").exists()

    def test_registration_view_successful_post_request_redirect(self, db, client):
        """Successful registration post request returns a redirect."""
        response = client.post(self.url, data=self.default_data)

        assert response.status_code == status.HTTP_302_FOUND

    def test_registration_view_redirect_to_correct_url(self, db, client):
        """Successful registration post request returns a redirect."""
        response = client.post(self.url, data=self.default_data)

        assert response.url == "/profile_information/?next=/"

    def test_registration_view_invalid_post_data_request_status_code(self, db, client):
        """
        Registration `POST` request returns a with status code 200 if
        the data is invalid.
        """
        response = client.post(
            self.url,
            data={
                "username": "new_test_username",
                "password1": "1234",
                "password2": "1",
                "email": "email",
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_registration_view_successful_post_request_login(self, db, client):
        """Successful registration view `POST` request logs in the user."""
        response = client.post(self.url, data=self.default_data, follow=True)

        user = response.context["user"]
        assert isinstance(user, User)
        assert user.username == "new_test_username"

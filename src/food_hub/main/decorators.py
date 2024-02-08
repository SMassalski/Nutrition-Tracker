"""View decorators for main app's functionality."""
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from main.models import Profile


def profile_required(
    function,
    redirect_url="profile-information",
    redirect_field_name=REDIRECT_FIELD_NAME,
):
    """
    Decorator for views that checks that the user has created
    a profile, redirecting to the profile creation page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: Profile.objects.filter(user=u).exists(),
        login_url=redirect_url,
        redirect_field_name=redirect_field_name,
    )

    return actual_decorator(function)

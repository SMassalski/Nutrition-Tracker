"""Authentication app forms."""
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


# This is needed because a custom user model is used
class CustomUserCreationForm(UserCreationForm):
    """UserCreationForm modified to use the custom user model."""

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = UserCreationForm.Meta.fields + ("email",)

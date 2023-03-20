"""Main app forms."""
from django import forms
from main.models import Profile


class ProfileForm(forms.ModelForm):
    """Form for creating and editing user profiles."""

    class Meta:
        model = Profile
        fields = [
            "age",
            "height",
            "sex",
            "activity_level",
        ]

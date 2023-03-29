"""Main app forms."""
from django import forms
from main.models import Profile

# TODO: Unit selection and conversion for weight and height


class ProfileForm(forms.ModelForm):
    """Form for creating and editing user profiles."""

    class Meta:
        model = Profile
        fields = [
            "age",
            "height",
            "weight",
            "sex",
            "activity_level",
        ]

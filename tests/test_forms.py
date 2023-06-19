"""Tests of main app's forms and form utility functions."""
import pytest
from main import forms
from main.models import Profile


class TestProfileForm:
    """Tests of the profile form."""

    @pytest.fixture
    def form(self):
        """A ProfileForm instance with data.

        age: 20
        sex: M
        activity_level: A
        height: 178
        weight: 176
        weight_unit: Kilograms
        """
        return forms.ProfileForm(
            {
                "age": 20,
                "sex": "M",
                "activity_level": "A",
                "height": 178,
                "weight": 176,
                "weight_unit": forms.ProfileForm.KILOGRAMS,
            }
        )

    def test_initial_height_unit_conversion(self):
        """
        ProfileForm converts height value to both cm and ft/in after
        instantiation.
        """
        profile = Profile(height=180)

        form = forms.ProfileForm(instance=profile)

        assert form["height"].value() == 180
        assert form["feet"].value() == 5
        assert form["inches"].value() == 11

    def test_cleaning_weight_unit_conversion(self, form):
        """
        ProfileForm converts weight value to kilograms during data
        cleaning if 'weight_unit' was set to pounds.
        """
        form.data["weight_unit"] = forms.ProfileForm.POUNDS

        form.is_valid()

        assert form.cleaned_data["weight"] == 80

    def test_cleaning_no_weight_unit_conversion_when_kg_used(self, form):
        """
        ProfileForm doesn't convert weight value if 'weight_unit' was
        set to kilograms.
        """
        form.data["weight_unit"] = forms.ProfileForm.KILOGRAMS

        form.is_valid()

        assert form.cleaned_data["weight"] == 176


def test_pounds_to_kilograms():
    """
    pounds_to_kilograms() correctly converts a weight in pounds to a
    weight in kilograms (with rounding).
    """
    assert forms.pounds_to_kilograms(2) == 1
    assert forms.pounds_to_kilograms(3) == 1


def test_centimeters_to_feet_and_inches():
    """
    centimeters_to_feet_and_inches() correctly converts a height in
    centimeters to a height in feet and inches (with rounding).
    """
    assert forms.centimeters_to_feet_and_inches(33) == (1, 1)

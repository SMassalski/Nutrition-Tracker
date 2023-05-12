"""Tests of main app's forms and form utility functions."""
from main import forms
from main.models.user import Profile


def test_profile_form_initial_height_unit_conversion():
    """
    ProfileForm converts height value to both cm and ft/in after
    instantiation.
    """
    profile = Profile(height=180)
    form = forms.ProfileForm(instance=profile)
    assert form["height"].value() == 180
    assert form["feet"].value() == 5
    assert form["inches"].value() == 11


def test_profile_form_weight_cleaning_unit_conversion():
    """
    ProfileForm converts weight value to kilograms during data cleaning
    if 'weight_unit' was set to pounds.
    """
    form = forms.ProfileForm(
        {
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
            "weight": 176,
            "weight_unit": forms.ProfileForm.POUNDS,
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["weight"] == 80
    profile = form.save(commit=False)
    assert profile.weight == 80


def test_profile_form_weight_cleaning_no_unit_conversion_when_kg_used():
    """
    ProfileForm doesn't convert weight value if 'weight_unit' was set to
    kilograms.
    """
    form = forms.ProfileForm(
        {
            "age": 20,
            "sex": "M",
            "activity_level": "A",
            "height": 178,
            "weight": 80,
            "weight_unit": forms.ProfileForm.KILOGRAMS,
        }
    )
    form.is_valid()
    assert form.cleaned_data["weight"] == 80


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

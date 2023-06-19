"""Main app forms."""
from typing import Tuple

from crispy_forms import bootstrap, layout
from crispy_forms.helper import FormHelper
from django import forms
from main.models import Profile


class ProfileForm(forms.ModelForm):
    """Form for creating and editing user profiles."""

    # Weight fields
    POUNDS = 1
    KILOGRAMS = 2
    weight_unit_choices = [(POUNDS, "lbs"), (KILOGRAMS, "kg")]
    weight = forms.IntegerField(label="")
    weight_unit = forms.ChoiceField(
        choices=weight_unit_choices, label="", initial=KILOGRAMS, required=False
    )

    # Height fields
    # Only the `height` field is considered when saving the profile.
    # Unit conversions between cm and ft/in are performed client-side
    # (js script is in the profile.html template).
    height = forms.IntegerField(label="")
    feet = forms.IntegerField(label="", required=False)
    inches = forms.IntegerField(label="", required=False)

    class Meta:
        model = Profile
        fields = [
            "age",
            "height",
            "feet",
            "inches",
            "weight",
            "weight_unit",
            "sex",
            "activity_level",
        ]

    def __init__(self, *args, **kwargs):
        """ProfileForm constructor.

        Defines layout using crispy-forms and includes initial unit
        conversion for height (Stored in the database in cm, displayed
        in both cm and ft/in).
        See ModelForm documentation for additional information.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = self._get_layout()

        # Initial height unit conversion
        feet, inches = centimeters_to_feet_and_inches(self.instance.height or 0)
        self["feet"].initial, self["inches"].initial = feet, inches

    def clean(self):
        """Clean weight data by converting the value to kilograms."""
        cleaned_data = super().clean()
        weight = cleaned_data.get("weight")
        # cleaned_data.get() returns '' if field was not provided.
        weight_unit = cleaned_data.get("weight_unit") or ProfileForm.KILOGRAMS

        if int(weight_unit) == ProfileForm.POUNDS:
            cleaned_data["weight"] = pounds_to_kilograms(weight)

        return cleaned_data

    @staticmethod
    def _get_layout():
        _layout = layout.Layout(
            "age",
            # Height fields
            layout.Div(
                layout.HTML(
                    '<label class="requiredField" for="id_height">Height'
                    '<span class="asteriskField">*</span></label>'
                ),
                # NOTE: Having two different fieldsets for different
                #  units requires JS code for automatic conversions
                #  for adequate user experience.
                layout.Row(
                    layout.Column(bootstrap.AppendedText("height", "cm")),
                    layout.Column(
                        layout.HTML(
                            '<span class="d-flex align-items-center form-group">'
                            "or"
                            "</span>"
                        ),
                        css_class="col-1 d-flex justify-content-center",
                    ),
                    layout.Column(bootstrap.AppendedText("feet", "ft")),
                    layout.Column(bootstrap.AppendedText("inches", "in")),
                ),
                css_class="form-group mb-0",
            ),
            # Weight fields
            layout.Div(
                layout.HTML(
                    '<label class="requiredField" for="id_weight">Weight'
                    '<span class="asteriskField">*</span></label>'
                ),
                layout.Row(
                    layout.Column("weight"),
                    layout.Column("weight_unit", css_class="col-2"),
                ),
                css_class="form-group mb-0",
            ),
            "sex",
            "activity_level",
            layout.Submit("submit", "Save", style="width: 100%"),
        )

        return _layout


def pounds_to_kilograms(weight: int) -> int:
    """Convert the given weight in pounds to kilograms."""
    return round(weight * 0.454)


def centimeters_to_feet_and_inches(centimeters: int) -> Tuple[int, int]:
    """Convert the given length in feet and inches to centimeters."""
    feet = int(centimeters // 30.48)
    inches = round((centimeters / 30.48 - feet) * 12)
    return feet, inches

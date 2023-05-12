"""Models related to user and profile functionality."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for future modification."""

    models.EmailField(
        blank=True, max_length=254, verbose_name="email address", unique=True
    ),


# A profile should not be required to use the app. Recommended intake
# calculations can use assumptions and averages when relevant
# information is not provided.
class Profile(models.Model):
    """
    Represents user information used for calculating intake
    recommendations.
    """

    # TODO: Additional age functionality
    #  * Column for age unit (months / years)
    #  * Column for tracking age (last time age was edited)
    #  * Energy calculations for ages < 3yo
    # Estimated Energy Requirement equation constants and coefficients
    # dependant on age and sex. The physical activity coefficient is
    # additionally dependant on activity level
    _EER_COEFFS = {
        "infant": dict(
            start_const=0.0,
            age_c=0.0,
            weight_c=89.0,
            height_c=0.0,
            pa_coeffs={"S": 1.0, "LA": 1.0, "A": 1.0, "VA": 1.0},
        ),
        "non-adult_M": dict(
            start_const=88.5,
            age_c=61.9,
            weight_c=26.7,
            height_c=903,
            pa_coeffs={"S": 1.0, "LA": 1.13, "A": 1.26, "VA": 1.42},
        ),
        "non-adult_F": dict(
            start_const=135.3,
            age_c=30.8,
            weight_c=10.0,
            height_c=934,
            pa_coeffs={"S": 1.0, "LA": 1.16, "A": 1.31, "VA": 1.56},
        ),
        "adult_M": dict(
            start_const=662.0,
            age_c=9.53,
            weight_c=15.91,
            height_c=539.6,
            pa_coeffs={"S": 1.0, "LA": 1.11, "A": 1.25, "VA": 1.48},
        ),
        "adult_F": dict(
            start_const=354,
            age_c=6.91,
            weight_c=9.36,
            height_c=726,
            pa_coeffs={"S": 1.0, "LA": 1.12, "A": 1.27, "VA": 1.45},
        ),
    }
    activity_choices = [
        ("S", "Sedentary"),
        ("LA", "Low Active"),
        ("A", "Active"),
        ("VA", "Very Active"),
    ]
    sex_choices = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    age = models.PositiveIntegerField()
    height = models.PositiveIntegerField()  # In centimeters
    weight = models.PositiveIntegerField()  # In kilograms
    activity_level = models.CharField(max_length=2, choices=activity_choices)
    sex = models.CharField(max_length=1, choices=sex_choices)
    energy_requirement = models.PositiveIntegerField()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}'s profile"

    def save(self, *args, **kwargs):
        """
        Overriden save method that calculates and updates the energy
        requirement field.
        """
        self.energy_requirement = self.calculate_energy()
        super().save(*args, **kwargs)

    def calculate_energy(self):
        """
        Calculate the Estimated Energy Requirement for the profile.

        The final result is rounded to the closest integer and is given
        in kcal/day.
        """
        # Coefficients and constants
        # Non-adults
        if self.age < 19:
            # Young children and infants (less than 3yrs old)
            if self.age < 3:
                coeffs = Profile._EER_COEFFS["infant"]
                # This is more granular - in ages [0, 3) the end
                # constant values change every 6 months
                if self.age < 1:
                    coeffs["end_const"] = -100 + 22
                else:
                    coeffs["end_const"] = -100 + 20
            # 3 - 18 yrs old
            else:
                # Boys
                if self.sex == "M":
                    coeffs = Profile._EER_COEFFS["non-adult_M"]
                # Girls
                else:
                    coeffs = Profile._EER_COEFFS["non-adult_F"]

                if self.age < 9:
                    coeffs["end_const"] = 20
                else:
                    coeffs["end_const"] = 25
        # Adults
        else:
            # Men
            if self.sex == "M":
                coeffs = Profile._EER_COEFFS["adult_M"]
            # Women
            else:
                coeffs = Profile._EER_COEFFS["adult_F"]

        start_const = coeffs.get("start_const", 0.0)
        end_const = coeffs.get("end_const", 0.0)
        age_c = coeffs.get("age_c", 0.0)
        weight_c = coeffs.get("weight_c", 0.0)
        height_c = coeffs.get("height_c", 0.0)
        PA = coeffs["pa_coeffs"][self.activity_level]

        # Equation
        result = (
            start_const
            - (age_c * self.age)
            + PA * (weight_c * self.weight + height_c * self.height / 100)
            + end_const
        )

        return round(result)

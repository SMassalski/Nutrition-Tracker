"""Tests of profile related features."""
import pytest
from main import models


class TestProfile:
    """Tests of the Profile model."""

    @pytest.mark.parametrize(
        ("age", "weight", "height", "sex", "expected"),
        [
            (35, 80, 180, "M", 2819),  # Adult male
            (35, 80, 180, "F", 2414),  # Adult female
            (15, 50, 170, "M", 2428),  # Non-adult male
            (15, 50, 170, "F", 2120),  # Non-adult female
            (2, 12, 80, "M", 988),  # 2 years old
            (0, 9, 80, "F", 723),  # less than 1 year old
        ],
    )
    def test_energy_calculation(self, age, weight, height, sex, expected):
        """
        Profile's calculate energy method correctly calculates the EER.
        """
        profile = models.Profile(
            age=age,
            weight=weight,
            height=height,
            sex=sex,
            activity_level="LA",
        )

        assert profile.calculate_energy() == expected

    def test_profile_create_calculates_energy(self, db, user):
        """Saving a new profile record automatically calculates the EER."""
        profile = models.Profile(
            age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
        )
        profile.save()
        profile.refresh_from_db()
        assert profile.energy_requirement is not None

    def test_profile_update_calculates_energy(self, db, saved_profile):
        """Updating a profile record automatically calculates the EER."""
        saved_profile.weight = 70
        saved_profile.save()

        saved_profile.refresh_from_db()
        assert saved_profile.energy_requirement == 2206

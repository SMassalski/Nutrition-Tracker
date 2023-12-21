"""Tests of profile related features."""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
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

    def test_save_creating_entry_creates_a_weight_measurement_entry(
        self, profile, user
    ):
        profile.user = user
        profile.save()

        assert profile.weight_measurements.count() == 1

    def test_save_updating_add_measurement_true(self, saved_profile):
        saved_profile.weight = 70
        saved_profile.save(add_measurement=True)

        assert saved_profile.weight_measurements.count() == 2

    def test_save_updating_add_measurement_false(self, saved_profile):
        saved_profile.weight = 70
        saved_profile.save(add_measurement=False)

        assert saved_profile.weight_measurements.count() == 1

    def test_save_recalculate_weight_true_sets_weight_based_on_measurements(
        self, saved_profile
    ):
        saved_profile.weight_measurements.create(value=60)
        saved_profile.weight = 90

        saved_profile.save(recalculate_weight=True)

        assert saved_profile.weight == 70

    def test_save_recalculate_weight_true_add_measurement_true_includes_new_measurement(
        self, saved_profile
    ):
        saved_profile.weight = 90

        saved_profile.save(add_measurement=True, recalculate_weight=True)

        assert saved_profile.weight == 85

    def test_save_recalculate_weight_false_keeps_weight_set_on_instance(
        self, saved_profile
    ):
        saved_profile.weight_measurements.create(value=60)
        saved_profile.weight = 90

        saved_profile.save(recalculate_weight=False)

        assert saved_profile.weight == 90

    def test_current_weight_is_the_average_of_measurements_within_week_before_last(
        self, profile, user
    ):
        profile.user = user
        profile.save()
        last = profile.weight_measurements.first().time
        models.WeightMeasurement.objects.bulk_create(
            [
                models.WeightMeasurement(
                    profile=profile, time=last - timedelta(days=1), value=81
                ),
                models.WeightMeasurement(
                    profile=profile, time=last - timedelta(days=7), value=82
                ),
                models.WeightMeasurement(
                    profile=profile, time=last - timedelta(days=8), value=90
                ),  # This one is not included
            ]
        )
        # Average includes the measurement created when saving the
        # profile (value=80)
        assert profile.current_weight == 81

    def test_update_weight_sets_weight_to_current_weight(self, saved_profile):
        saved_profile.weight_measurements.create(value=90)
        saved_profile.update_weight()

        assert saved_profile.weight == 85


class TestWeightMeasurement:
    """Tests of the `WeightMeasurement` model."""

    def test_has_min_value_1_validation(self, saved_profile):
        instance = models.WeightMeasurement(profile=saved_profile, value=0)

        with pytest.raises(ValidationError):
            instance.full_clean()

    def test_has_profile_time_unique_constraint(self, saved_profile):
        time = timezone.now()
        models.WeightMeasurement.objects.create(
            profile=saved_profile, value=1, time=time
        )

        with pytest.raises(IntegrityError):
            models.WeightMeasurement.objects.create(
                profile=saved_profile, value=2, time=time
            )

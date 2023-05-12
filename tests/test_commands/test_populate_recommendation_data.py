"""Tests of the 'populaterecommendationdata' command."""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from main.models import Nutrient


def test_populate_recommendation_data_no_nutrients_raises_error(db):
    """
    The 'populaterecommendationdata' command raises an exception if none
    of the nutrients referred to by the recommendation data in the
    database.
    """
    with pytest.raises(CommandError):
        call_command("populaterecommendationdata")


def test_populate_recommendation_data_completes_when_nutrients_are_available(db):
    """
    The 'populaterecommendationdata' command completes without error if
    some of the nutrients referred to by the recommendation data in the
    database.
    """
    Nutrient.objects.create(name="Protein", unit="G")
    call_command("populaterecommendationdata")

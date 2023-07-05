"""Tests of the load_fdc_data command helper functions."""
import pytest
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.management.commands._fdc_helpers import (
    create_compound_nutrient_amounts,
    get_fdc_data_source,
    handle_nonstandard,
)

# NOTE: Nonstandard nutrient is a nutrient that needs to be handled
#  differently based on the differences in the way they are stored
#  in the FDC data and the app's database.

# FDC ids of nutrients that need to be handled differently
CYSTEINE = 1232
CYSTINE = 1216
VIT_A_RAE = 1106
VIT_A_IU = 1104
VIT_D = 1114
VIT_D_IU = 1110
FOLATE = 1177
FOLATE_DFE = 1190
VIT_K_M = 1183
VIT_K_DHP = 1184
VIT_K_P = 1185


# TODO: No ability to input nutrient preferences seems bad
class TestHandleNonstandard:
    """Tests of the handle_nonstandard() function."""

    def test_sums_vitamin_k(self, ingredient_1, nutrient_1):
        """handle_nonstandard() sums the amounts for vitamin K."""
        result = {}

        handle_nonstandard(ingredient_1, nutrient_1, VIT_K_M, result, 1.0, [])
        handle_nonstandard(ingredient_1, nutrient_1, VIT_K_DHP, result, 2.0, [])
        handle_nonstandard(ingredient_1, nutrient_1, VIT_K_P, result, 3.0, [])

        assert result[ingredient_1][nutrient_1] == 6.0

    def test_creates_not_encountered(self, ingredient_1, nutrient_1):
        """
        handle_nonstandard() creates dict entries for nutrients that were
        not encountered previously.
        """
        result = {}

        handle_nonstandard(ingredient_1, nutrient_1, VIT_K_M, result, 2.0, [])

        assert ingredient_1 in result
        assert nutrient_1 in result[ingredient_1]

    def test_creates_not_encountered_with_amount(self, ingredient_1, nutrient_1):
        """
        handle_nonstandard() creates dict entries for nutrients that were
        not encountered previously with the provided amount.
        """
        result = {}

        handle_nonstandard(ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0, [])

        assert result[ingredient_1][nutrient_1] == 2.0

    def test_replaces_amount_with_preferred_nutrient(self, ingredient_1, nutrient_1):
        """
        handle_nonstandard() replaces the old amount if a preferred nutrient
        was encountered.
        """
        result = {}

        # Vitamin A, RAE is preferred over Vitamin A, IU
        handle_nonstandard(ingredient_1, nutrient_1, VIT_A_IU, result, 1.0, [VIT_A_RAE])
        handle_nonstandard(
            ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0, [VIT_A_RAE]
        )

        assert result[ingredient_1][nutrient_1] == 2.0

    def test_keeps_amount_with_preferred_nutrient(self, ingredient_1, nutrient_1):
        """
        handle_nonstandard() keeps the old amount if a nutrient that is not
        preferred was encountered.
        """
        result = {}
        # Vitamin A, RAE is preferred over Vitamin A, IU
        handle_nonstandard(
            ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0, [VIT_A_RAE]
        )
        handle_nonstandard(ingredient_1, nutrient_1, VIT_A_IU, result, 1.0, [VIT_A_RAE])

        assert result[ingredient_1][nutrient_1] == 2.0


class TestGetFdcDataSource:
    """Tests of the get_fdc_data_source() function."""

    def test_creates_record(self, db):
        """get_fdc_data_source saves an FDC FoodDataSource record."""
        get_fdc_data_source()

        assert models.FoodDataSource.objects.filter(name="FDC").exists()

    def test_source_already_exists(self, db):
        """
        get_fdc_data_source doesn't raise an exception if an FDC record
        already exists.
        """
        models.FoodDataSource.objects.create(name="FDC")

        try:
            get_fdc_data_source()
        except IntegrityError as e:
            pytest.fail(f"create_fdc_data_source() violated a constraint - {e}")

    def test_returns_food_data_source_instance(self, db):
        """
        get_fdc_data_source only returns the FDC FoodDataSource
        instance.
        """
        result = get_fdc_data_source()

        assert isinstance(result, models.FoodDataSource)


def test_create_compound_nutrient_amounts(db, compound_nutrient):
    """
    create_compound_nutrient_amounts() creates IngredientNutrient
    records for compound nutrients.
    """
    create_compound_nutrient_amounts()

    assert models.IngredientNutrient.objects.filter(nutrient=compound_nutrient).exists()

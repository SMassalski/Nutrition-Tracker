"""Tests of the populate_fdc_data command helper functions."""
import io

import pytest
from django.conf import settings
from django.db import connection
from main import models
from main.management.commands._populatefdcdata import (
    NoNutrientException,
    create_fdc_data_source,
    handle_nonstandard,
    parse_food_csv,
    parse_food_nutrient_csv,
    parse_nutrient_csv,
)

# NOTE: Nonstandard nutrient is a nutrient that needs o be handled
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


# handle_nonstandard tests
def test_handle_nonstandard_sums_vitamin_k(ingredient_1, nutrient_1):
    """handle_nonstandard() sums the amounts for vitamin K."""
    result = {}

    handle_nonstandard(ingredient_1, nutrient_1, VIT_K_M, result, 1.0)
    handle_nonstandard(ingredient_1, nutrient_1, VIT_K_DHP, result, 2.0)
    handle_nonstandard(ingredient_1, nutrient_1, VIT_K_P, result, 3.0)

    assert result[ingredient_1][nutrient_1] == 6.0


def test_handle_nonstandard_creates_not_encountered(ingredient_1, nutrient_1):
    """
    handle_nonstandard() creates dict entries for nutrients that were
    not encountered previously.
    """
    result = {}

    handle_nonstandard(ingredient_1, nutrient_1, VIT_K_M, result, 2.0)

    assert ingredient_1 in result
    assert nutrient_1 in result[ingredient_1]


def test_handle_nonstandard_creates_not_encountered_with_amount(
    ingredient_1, nutrient_1
):
    """
    handle_nonstandard() creates dict entries for nutrients that were
    not encountered previously with the provided amount.
    """
    result = {}
    handle_nonstandard(ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0)

    assert result[ingredient_1][nutrient_1] == 2.0


def test_handle_nonstandard_replaces_amount_with_preferred_nutrient(
    ingredient_1, nutrient_1
):
    """
    handle_nonstandard() replaces the old amount if a preferred nutrient
    was encountered.
    """
    result = {}
    # Vitamin A, RAE is preferred over Vitamin A, IU
    handle_nonstandard(ingredient_1, nutrient_1, VIT_A_IU, result, 1.0)
    handle_nonstandard(ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0)

    assert result[ingredient_1][nutrient_1] == 2.0


def test_handle_nonstandard_keeps_amount_with_preferred_nutrient(
    ingredient_1, nutrient_1
):
    """
    handle_nonstandard() keeps the old amount if a nutrient that is not
    preferred was encountered.
    """
    result = {}
    # Vitamin A, RAE is preferred over Vitamin A, IU
    handle_nonstandard(ingredient_1, nutrient_1, VIT_A_RAE, result, 2.0)
    handle_nonstandard(ingredient_1, nutrient_1, VIT_A_IU, result, 1.0)

    assert result[ingredient_1][nutrient_1] == 2.0


# create_fdc_data_source() tests
def test_create_fdc_data_source(db):
    """create_fdc_data_source saves an FDC FoodDataSource record."""
    create_fdc_data_source()
    assert models.FoodDataSource.objects.filter(name="FDC").exists()


def test_create_fdc_data_source_already_exists(db):
    """
    create_fdc_data_source doesn't raise an exception if an FDC record
    already exists.
    """
    models.FoodDataSource.objects.create(name="FDC")
    create_fdc_data_source()


# FDC data csv parser tests


def append_file(file: io.IOBase, data: str):
    """Append text data to the end of a file."""
    file.seek(0, io.SEEK_END)
    file.write(data)
    file.seek(0)


# FILE: food.csv
@pytest.fixture
def food_csv():
    """
    A sample food.csv file with the same headers as a real FDC file.
    """
    file = io.StringIO(
        '"fdc_id","data_type","description","food_category_id","publication_date"\n'
        '"1","survey_fndds_food","test_ingredient_1","","2020-11-13"\n'
        '"2","sr_legacy_food","test_ingredient_2","","2019-04-01"\n'
    )
    yield file

    file.close()


@pytest.fixture(scope="module")
def fdc_data_source(django_db_blocker, django_db_setup):
    """A FoodDataSource record for FDC"""
    with django_db_blocker.unblock():
        instance = models.FoodDataSource.objects.create(name="FDC")
    yield instance
    with django_db_blocker.unblock():
        instance.delete()


def test_parse_food_csv_reads_data(db, fdc_data_source, food_csv):
    """
    parse_food_csv() correctly creates Ingredient instances according
    to the data.
    """
    result = parse_food_csv(food_csv)

    assert len(result) == 2

    result = result[0]
    assert result.name == "test_ingredient_1"
    assert result.external_id == 1
    assert result.dataset == "survey_fndds_food"
    assert result.data_source == fdc_data_source


def test_parse_food_csv_source_filter(db, fdc_data_source, food_csv):
    """
    parse_food_csv() creates Ingredient instances only from datasets
    specified in `dataset_filter`.
    """
    result = parse_food_csv(food_csv, dataset_filter=["sr_legacy_food"])

    assert len(result) == 1
    result = result[0]

    assert result.dataset == "sr_legacy_food"


# FILE: nutrient.csv
@pytest.fixture
def nutrient_csv():
    """
    A sample nutrient.csv file with the same headers as a real FDC file.
    """
    file = io.StringIO(
        '"id","name","unit_name","nutrient_nbr","rank"\n'
        '"1","nutrient_1","UG","201","200.0"\n'
        '"2","nutrient_2","MG","202","200.0"\n'
        '"3","nutrient_3","G","203","200.0"\n'
    )
    yield file
    file.close()


@pytest.fixture
def debug_mode():
    """Set 'settings.DEBUG' to True for the duration of the test."""
    settings.DEBUG = True
    yield
    settings.DEBUG = False


class TestParseNutrient:
    """Tests of the parse_nutrient_csv() function."""

    def test_parse_nutrient_units(self, nutrient_csv):
        """
        parse_nutrient_csv() correctly extracts information about a
        nutrient's unit from FDC's nutrient.csv.
        """
        expected = {
            1: "UG",
            2: "MG",
            3: "G",
        }
        result, _ = parse_nutrient_csv(nutrient_csv)
        assert result == expected

    def test_parse_nutrient_nbr(self, nutrient_csv):
        """
        parse_nutrient_csv() correctly creates a mapping for nutrient's
        nbr to their FDC ids.
        """
        expected = {"201": 1, "202": 2, "203": 3}
        _, result = parse_nutrient_csv(nutrient_csv)
        assert result == expected

    def test_get_nutrient_units_nonstandard_unit(self, nutrient_csv):
        """
        parse_nutrient_csv() translates nonstandard units (like MCG_RE)
        to their respective standard counterparts.
        """
        append_file(
            nutrient_csv,
            '"4","nutrient_4","MCG_RE","201","200.0"\n'
            '"5","nutrient_5","MG_GAE","201","200.0"\n'
            '"6","nutrient_6","MG_ATE","201","200.0"\n',
        )

        result, _ = parse_nutrient_csv(nutrient_csv)
        assert result[4] == "UG"
        assert result[5] == "MG"
        assert result[6] == "MG"


# FILE: food_nutrient.csv
@pytest.fixture
def food_nutrient_csv():
    """
    A sample food_nutrient.csv file with the same headers as a real FDC
    file.
    """
    file = io.StringIO(
        '"id","fdc_id","nutrient_id","amount","data_points","derivation_id","min",'
        '"max","median","loq","footnote","min_year_acquired"\n'
        '"13706913","3","1003","0.0","","71","","","","","",""\n'  # Protein
        '"13706914","4","1089","93.33","","71","","","","","",""\n'  # Iron
    )
    yield file
    file.close()


@pytest.fixture
def real_nutrient_csv(nutrient_csv):
    """
    Nutrient file with real records needed for the functioning of
    parse_food_nutrient_csv().
    """
    append_file(
        nutrient_csv,
        '"1003","Protein","MCG_RE","201","200.0"\n'
        '"1089","Iron","MG_GAE","201","200.0"\n'
        #'"1104","Vitamin A","MG_ATE","201","200.0"\n'
        #'"1110","Vitamin D","MCG_RE","201","200.0"\n'
        #'"1175","Folate","MG_GAE","201","200.0"\n'
        #'"1183","Vitamin K","MG_ATE","201","200.0"\n'
        #'"1216","Cysteine","MCG_RE","201","200.0"\n'
    )
    return nutrient_csv


@pytest.fixture(scope="class")
def ingredient_and_nutrient_data(django_db_blocker, django_db_setup, fdc_data_source):
    """
    Multiple Ingredient and Nutrient records saved to the database.
    """
    with django_db_blocker.unblock():
        nutrients = models.Nutrient.objects.bulk_create(
            [
                models.Nutrient(name="Protein", unit="G"),
                models.Nutrient(name="Iron", unit="MG"),
                models.Nutrient(name="Vitamin A", unit="UG"),
                models.Nutrient(name="Vitamin D", unit="UG"),
                models.Nutrient(name="Vitamin B9", unit="UG"),
                models.Nutrient(name="Vitamin K", unit="UG"),
                models.Nutrient(name="Cysteine", unit="MG"),
            ]
        )

        ingredients = models.Ingredient.objects.bulk_create(
            [
                #  external_id 1 and 2 are taken by ingredient_1
                #  and ingredient_2 fixtures. This won't be a problem
                #  after the unique constraint is fixed.
                models.Ingredient(
                    name="ingredient_3",
                    external_id=3,
                    dataset="x",
                    data_source=fdc_data_source,
                ),
                models.Ingredient(
                    name="ingredient_4",
                    external_id=4,
                    dataset="x",
                    data_source=fdc_data_source,
                ),
                models.Ingredient(
                    name="ingredient_5",
                    external_id=5,
                    dataset="x",
                    data_source=fdc_data_source,
                ),
            ]
        )

    yield nutrients, ingredients

    with django_db_blocker.unblock():
        models.Nutrient.objects.filter(pk__in=[n.pk for n in nutrients]).delete()
        models.Ingredient.objects.filter(pk__in=[i.pk for i in ingredients]).delete()


class TestParseFoodNutrient:
    """Tests of the parse_food_nutrient_csv() function."""

    def test_parse_food_nutrient(
        self, db, food_nutrient_csv, real_nutrient_csv, ingredient_and_nutrient_data
    ):
        """
        parse_food_nutrient() correctly saves standard IngredientNutrient
        records according to the data in food_nutrient.csv
        """
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv)

        in_1 = models.IngredientNutrient.objects.get(ingredient__external_id=3)
        assert in_1.nutrient.name == "Protein"
        assert in_1.amount == 0

    def test_parse_food_nutrient_ingredient_not_in_db(
        self, db, food_nutrient_csv, real_nutrient_csv, ingredient_and_nutrient_data
    ):
        """
        parse_food_nutrient_csv() skips the IngredientNutrient record if
        the referenced ingredient is not in the database.
        """
        append_file(
            food_nutrient_csv,
            '"13706915","10","1089","93.33","","71","","","","","",""\n',
        )
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv)

        assert not models.IngredientNutrient.objects.filter(
            ingredient__external_id=10
        ).exists()

    def test_parse_food_nutrient_nutrient_not_in_db(
        self, db, food_nutrient_csv, real_nutrient_csv, ingredient_and_nutrient_data
    ):
        """
        parse_food_nutrient_csv() skips the IngredientNutrient record if
        the referenced nutrient is not in the database.
        """
        append_file(
            food_nutrient_csv,
            '"13706915","5","9999","93.33","","71","","","","","",""\n',
        )
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv)

        assert not models.IngredientNutrient.objects.filter(
            ingredient__external_id=10
        ).exists()

    # TODO: This might be better done through mocking
    def test_parse_food_nutrient_exceptions(
        self, db, food_nutrient_csv, real_nutrient_csv, ingredient_and_nutrient_data
    ):
        """
        parse_food_nutrient_csv() correctly handles nutrients that have
        to be treated differently than regular ones.
        """
        append_file(
            food_nutrient_csv,
            # preferred vit. A RAE over IU
            '"13706915","4","1104","2","","71","","","","","",""\n'
            '"13706915","4","1106","1","","71","","","","","",""\n'
            # vit D uses IU if not available in micrograms
            '"13706915","4","1110","40","","71","","","","","",""\n'
            # prefers folate,total over DFE
            '"13706915","4","1177","1","","71","","","","","",""\n'
            '"13706915","4","1190","2","","71","","","","","",""\n'
            # sums up vit. K
            '"13706915","4","1183","1","","71","","","","","",""\n'
            '"13706915","4","1184","2","","71","","","","","",""\n'
            '"13706915","4","1185","3","","71","","","","","",""\n'
            # Cystine if cysteine is not available
            '"13706915","4","1216","0.001","","71","","","","","",""\n',
        )

        append_file(
            real_nutrient_csv,
            '"1104","Vitamin A, IU","IU","201","200.0"\n'
            '"1106","Vitamin A, RAE","UG","202","200.0"\n'
            '"1110","Vitamin D, IU","IU","203","200.0"\n'
            '"1114","Vitamin D","UG","204","200.0"\n'
            '"1177","Folate, total","UG","205","200.0"\n'
            '"1190","Folate, DFE","UG","206","200.0"\n'
            '"1183","Vitamin K (Menaquinone-4)","UG","201","200.0"\n'
            '"1184","Vitamin K (Dihydrophylloquinone)","UG","202","200.0"\n'
            '"1185","Vitamin K (phylloquinone)","UG","203","200.0"\n'
            '"1232","Cysteine","G","204","200.0"\n'
            '"1216","Cystine","G","205","200.0"\n',
        )
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv)

        ing = models.Ingredient.objects.get(external_id=4)

        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin A").amount == 1

        # Vitamin D IU nutrient conversion (40 IU in food_nutrient_csv to 1 mcg)
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin D").amount == 1
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin B9").amount == 1
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin K").amount == 6

        # Cysteine has unit conversion from g to mg
        assert ing.ingredientnutrient_set.get(nutrient__name="Cysteine").amount == 1

    def test_parse_food_nutrient_batch_size(
        self,
        db,
        food_nutrient_csv,
        real_nutrient_csv,
        ingredient_and_nutrient_data,
        debug_mode,
    ):
        """
        parse_food_nutrient_csv() separates creating IngredientNutrient
        records to batches of the specified size.
        """
        start_conn_nbr = len(connection.queries)
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv, batch_size=1)
        assert len(connection.queries) - start_conn_nbr == 5

    def test_parse_food_nutrient_batch_size_nonstandard(
        self,
        db,
        food_nutrient_csv,
        real_nutrient_csv,
        ingredient_and_nutrient_data,
        debug_mode,
    ):
        """
        parse_food_nutrient_csv() separates creating IngredientNutrient
        records to batches of the specified size when handling
        nonstandard nutrients.
        """
        append_file(
            food_nutrient_csv, '"13706915","4","1104","2","","71","","","","","",""\n'
        )

        append_file(real_nutrient_csv, '"1104","Vitamin A, IU","IU","201","200.0"\n')
        start_conn_nbr = len(connection.queries)
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv, batch_size=1)
        assert len(connection.queries) - start_conn_nbr == 6


# Separate to avoid ingredient_and_nutrient_data_fixture
def test_parse_food_nutrient_no_nutrients_in_db(
    db, food_nutrient_csv, real_nutrient_csv, nutrient_1
):
    """
    parse_food_nutrient_csv() raises a NoNutrientException if none of
    the required nutrients (those that would have their counterparts in
    the FDC data and are needed for the applications functioning) are in
    the database.
    """
    # nutrient_1 is not a required nutrient

    with pytest.raises(NoNutrientException):
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv)

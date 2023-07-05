"""Tests of parsing functions used by the load_fdc_data command."""
import io

import pytest
from main import models

# noinspection PyProtectedMember
from main.management.commands._fdc_helpers import NoNutrientException

# noinspection PyProtectedMember
from main.management.commands._fdc_parsers import (
    FDC_DATASETS,
    parse_food_csv,
    parse_food_nutrient_csv,
    parse_nutrient_csv,
)


@pytest.fixture
def fdc_data_source(db):
    """A FoodDataSource record for FDC."""
    return models.FoodDataSource.objects.create(name="FDC")


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
        '"1089","Iron","MG_GAE","201","200.0"\n',
    )
    return nutrient_csv


class TestParseFoodCsv:
    """Tests of the parse_food_csv() function."""

    @pytest.fixture
    def food_csv(self):
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

    def test_correctly_reads_data(self, db, fdc_data_source, food_csv):
        """
        parse_food_csv() correctly creates Ingredient instances
        according to the data.
        """
        instances = parse_food_csv(
            food_csv, dataset_filter=FDC_DATASETS, data_source=fdc_data_source
        )

        expected = {
            "name": "test_ingredient_1",
            "external_id": 1,
            "dataset": "survey_fndds_food",
            "data_source_id": fdc_data_source.id,
        }

        result = {k: vars(instances[0])[k] for k in expected}
        assert len(instances) == 2
        assert result == expected

    def test_source_filter(self, db, fdc_data_source, food_csv):
        """
        parse_food_csv() creates Ingredient instances only from datasets
        specified in `dataset_filter`.
        """
        result = parse_food_csv(
            food_csv, dataset_filter=["sr_legacy_food"], data_source=fdc_data_source
        )

        assert result[0].dataset == "sr_legacy_food"

    def test_invalid_source_filter(self, fdc_data_source, food_csv):
        """
        parse_food_csv() raises a ValueError if `dataset_filter`
        includes an invalid dataset name.
        """
        datasets = ["sr_legacy_food", "invalid_dataset"]

        with pytest.raises(ValueError):
            parse_food_csv(
                food_csv, dataset_filter=datasets, data_source=fdc_data_source
            )


class TestParseNutrient:
    """Tests of the parse_nutrient_csv() function."""

    def test_unit_info(self, nutrient_csv):
        """
        parse_nutrient_csv() correctly extracts information about a
        nutrient's unit from FDC's nutrient.csv.
        """
        result, _ = parse_nutrient_csv(nutrient_csv)

        expected = {
            1: "UG",
            2: "MG",
            3: "G",
        }
        assert result == expected

    def test_nbr_info(self, nutrient_csv):
        """
        parse_nutrient_csv() correctly creates a mapping for nutrient's
        nbr to their FDC ids.
        """
        _, result = parse_nutrient_csv(nutrient_csv)

        expected = {"201": 1, "202": 2, "203": 3}
        assert result == expected

    def test_nonstandard_unit(self, nutrient_csv):
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

        units, _ = parse_nutrient_csv(nutrient_csv)

        result = tuple(units[i] for i in range(4, 7))
        expected = ("UG", "MG", "MG")
        assert result == expected


class TestParseFoodNutrient:
    """Tests of the parse_food_nutrient_csv() function."""

    @pytest.fixture
    def ingredient_and_nutrient_data(self, db, fdc_data_source):
        """
        Multiple Ingredient and Nutrient records saved to the database.
        """

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

        return nutrients, ingredients

    def test_saves_records(
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

    def test_ingredient_not_in_db(
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

    def test_nutrient_not_in_db(
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
            ingredient__external_id=5
        ).exists()

    # TODO: This needs some rework
    # TODO: This might be better done through mocking
    #   or at least separate
    def test_nonstandard(
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
            # prefers folate, total over DFE
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
        preferred = {
            1232,  # Cysteine
            1106,  # Vitamin A, RAE
            1114,  # Vitamin D (D2 + D3)
            1177,  # Folate, total
        }
        parse_food_nutrient_csv(
            food_nutrient_csv, real_nutrient_csv, preferred_nutrients=preferred
        )

        ing = models.Ingredient.objects.get(external_id=4)

        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin A").amount == 1

        # Vitamin D IU nutrient conversion (40 IU in food_nutrient_csv to 1 mcg)
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin D").amount == 1
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin B9").amount == 1
        assert ing.ingredientnutrient_set.get(nutrient__name="Vitamin K").amount == 6

        # Cysteine has unit conversion from g to mg
        assert ing.ingredientnutrient_set.get(nutrient__name="Cysteine").amount == 1

    # TODO: This needs some rework
    def test_batch_size(
        self,
        db,
        food_nutrient_csv,
        real_nutrient_csv,
        ingredient_and_nutrient_data,
    ):
        """
        Batched parse_food_nutrient_csv() finishes without error for
        regular nutrients.
        """
        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv, batch_size=1)

    # TODO: This needs some rework
    def test_batch_size_nonstandard(
        self,
        db,
        food_nutrient_csv,
        real_nutrient_csv,
        ingredient_and_nutrient_data,
    ):
        """
        Batched parse_food_nutrient_csv() finishes without error for
        nonstandard nutrients.
        """
        append_file(
            food_nutrient_csv, '"13706915","4","1104","2","","71","","","","","",""\n'
        )
        append_file(real_nutrient_csv, '"1104","Vitamin A, IU","IU","201","200.0"\n')

        parse_food_nutrient_csv(food_nutrient_csv, real_nutrient_csv, batch_size=1)

    def test_no_nutrients_in_db(
        self, db, food_nutrient_csv, real_nutrient_csv, nutrient_1
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


def append_file(file: io.IOBase, data: str):
    """Append text data to the end of a file."""
    file.seek(0, io.SEEK_END)
    file.write(data)
    file.seek(0)

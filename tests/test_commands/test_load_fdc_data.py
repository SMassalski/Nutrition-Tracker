"""Tests of the loadfdcdata command."""
import os
from tempfile import mkstemp

import pytest
from django.core.management import CommandError, call_command
from main.management.commands.loadfdcdata import Command
from main.models import Ingredient, IngredientNutrient, Nutrient


class TestLoadFdcDataCommand:
    """Tests of the loadfdcdata command."""

    @pytest.fixture(scope="class")
    def fdc_data_file_paths(self):
        """Dummy FDC data files."""
        fd, food_path = mkstemp(text=True)
        os.write(
            fd,
            b'"fdc_id","data_type","description","food_category_id","publication_date"\n'
            b'"3","survey_fndds_food","test_ingredient_3","","2020-11-13"\n'
            b'"4","sr_legacy_food","test_ingredient_4","","2019-04-01"\n',
        )
        os.close(fd)

        fd, nutrient_path = mkstemp(text=True)
        os.write(
            fd,
            b'"id","name","unit_name","nutrient_nbr","rank"\n'
            b'"1003","Protein","G","201","200.0"\n'
            b'"1089","Iron","UG","201","200.0"\n',
        )
        os.close(fd)

        fd, food_nutrient_path = mkstemp(text=True)
        os.write(
            fd,
            b'"id","fdc_id","nutrient_id","amount","data_points","derivation_id","min",'
            b'"max","median","loq","footnote","min_year_acquired"\n'
            b'"13706913","3","1003","0.0","","71","","","","","",""\n'  # Protein
            b'"13706914","4","1089","93.33","","71","","","","","",""\n',  # Iron
        )
        os.close(fd)

        files = {
            "food_file": food_path,
            "nutrient_file": nutrient_path,
            "food_nutrient_file": food_nutrient_path,
        }

        yield files

        for path in food_path, nutrient_path, food_nutrient_path:
            os.remove(path)

    @pytest.fixture
    def fdc_files_w_nonstandard(self, fdc_data_file_paths):
        """Dummy FDC data files with nonstandard nutrients."""
        with open(fdc_data_file_paths["nutrient_file"], "a") as f:
            nutrient_position = f.tell()
            lines = (
                '"1104","Vitamin A","MG","201","200.0"\n'
                '"1106","Vitamin A, RAE","MG","201","200.0"\n'
            )
            f.write(lines)

        with open(fdc_data_file_paths["food_nutrient_file"], "a") as f:
            food_nutrient_position = f.tell()
            lines = (
                '"13706915","4","1106","600","","71","","","","","",""\n'
                '"13706916","4","1104","400","","71","","","","","",""\n'
            )
            f.write(lines)

        yield fdc_data_file_paths

        with open(fdc_data_file_paths["nutrient_file"], "a") as f:
            f.truncate(nutrient_position)

        with open(fdc_data_file_paths["food_nutrient_file"], "a") as f:
            f.truncate(food_nutrient_position)

    @pytest.fixture
    def nutrients(self, db):
        """Create nutrient records.

        name: Protein
        unit: G

        name: Iron
        unit: MG
        """
        Nutrient.objects.bulk_create(
            [Nutrient(name="Protein", unit="G"), Nutrient(name="Iron", unit="MG")]
        )

    @pytest.fixture
    def nutrients_w_nonstandard(self, nutrients):
        Nutrient.objects.create(name="Vitamin A", unit="MG")

    def test_command_error_when_no_file_path_were_provided(self):
        """
        The loadfdcdata command raises an exception if no file paths
        are available.

        (The DATA_DIR setting is disabled for the tests).
        """
        with pytest.raises(CommandError):
            call_command("loadfdcdata")

    @pytest.mark.parametrize(
        "files",
        (
            ("food_file", "nutrient_file"),
            ("food_file", "food_nutrient_file"),
            ("food_nutrient_file", "nutrient_file"),
        ),
    )
    def test_command_error_when_a_path_is_missing(self, files):
        """
        The loadfdcdata command raises an exception if a file path
        is missing and `data_dir` was not provided.
        """
        with pytest.raises(CommandError):
            call_command("loadfdcdata", **{file: "tst.csv" for file in files})

    def test_command_path_overrides(self):
        """
        The loadfdcdata command file path arguments override file
        discovery when a `data_dir` was provided.
        """
        try:
            call_command("loadfdcdata", food_file="tst.csv", data_dir="tst/")

        except CommandError as e:
            # The error message when checking if the file exists
            # contains the names of the checked files, so the override
            # will be visible there
            assert "tst.csv" in str(e)
        else:
            assert False  # There should be an exception

    @pytest.mark.parametrize(
        "file", ("food_file", "nutrient_file", "food_nutrient_file")
    )
    def test_command_files_dont_exist(self, fdc_data_file_paths, file):
        """
        The loadfdcdata command raises an exception if a file does
        not exist.
        """
        files = fdc_data_file_paths.copy()
        files[file] = "tst.csv"

        with pytest.raises(CommandError):
            call_command("loadfdcdata", **files)

    def test_command_error_when_no_nutrients(self, db, fdc_data_file_paths):
        """
        The loadfdcdata command raises an exception if none of the
        required nutrients are in the database.
        """
        with pytest.raises(CommandError):
            call_command("loadfdcdata", **fdc_data_file_paths)

    def test_command_saves_data(self, db, fdc_data_file_paths, nutrients):
        """
        The loadfdcdata command saves data from files.
        """
        call_command("loadfdcdata", **fdc_data_file_paths)

        names = ["test_ingredient_3", "test_ingredient_4"]
        assert Ingredient.objects.filter(name__in=names).count() == 2

    def test_command_dataset_filter(self, db, fdc_data_file_paths, nutrients):
        """
        The loadfdcdata command with a dataset_filter saves data
        only for ingredients that pass the filter.
        """
        call_command(
            "loadfdcdata", dataset_filter=["sr_legacy_food"], **fdc_data_file_paths
        )

        assert not Ingredient.objects.filter(name="test_ingredient_3").exists()

    def test_command_preferred_nutrient_default(
        self, db, fdc_files_w_nonstandard, nutrients_w_nonstandard
    ):
        """
        The loadfdcdata command has a default `preferred_nutrients` set.
        """
        call_command("loadfdcdata", **fdc_files_w_nonstandard)

        # by default nutrient with fdc_id 1106 is preferred
        expected = 6
        ingredient_nutrient = IngredientNutrient.objects.get(
            nutrient__name="Vitamin A", ingredient__name="test_ingredient_4"
        )
        assert ingredient_nutrient.amount == expected

    def test_command_preferred_nutrient_set_in_init(
        self, db, fdc_files_w_nonstandard, nutrients_w_nonstandard
    ):
        """
        The loadfdcdata command allows setting preferred nutrients in
        the init method.
        """
        cmd = Command(preferred=(1104,))

        call_command(cmd, **fdc_files_w_nonstandard)

        expected = 4
        ingredient_nutrient = IngredientNutrient.objects.get(
            nutrient__name="Vitamin A", ingredient__name="test_ingredient_4"
        )
        assert ingredient_nutrient.amount == expected

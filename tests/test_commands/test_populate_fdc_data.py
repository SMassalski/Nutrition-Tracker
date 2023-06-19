"""Tests of the populatefdcdata command."""
import os
from tempfile import mkstemp

import pytest
from django.core.management import CommandError, call_command
from main.models import Ingredient, Nutrient


class TestPopulateFdcDataCommand:
    """Tests of the populatefdcdata command."""

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

    def test_command_error_when_no_file_path_were_provided(self):
        """
        The populatefdcdata command raises an exception if no file paths
        are available.

        (The DATA_DIR setting is disabled for the tests).
        """
        with pytest.raises(CommandError):
            call_command("populatefdcdata")

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
        The populatefdcdata command raises an exception if a file path
        is missing and `data_dir` was not provided.
        """
        with pytest.raises(CommandError):
            call_command("populatefdcdata", **{file: "tst.csv" for file in files})

    def test_command_path_overrides(self):
        """
        The populatefdcdata command file path arguments override file
        discovery when a `data_dir` was provided.
        """
        try:
            call_command("populatefdcdata", food_file="tst.csv", data_dir="tst/")

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
        The populatefdcdata command raises an exception if a file does
        not exist.
        """
        files = fdc_data_file_paths.copy()
        files[file] = "tst.csv"

        with pytest.raises(CommandError):
            call_command("populatefdcdata", **files)

    def test_command_error_when_no_nutrients(self, db, fdc_data_file_paths):
        """
        The populatefdcdata command raises an exception if none of the
        required nutrients are in the database.
        """
        with pytest.raises(CommandError):
            call_command("populatefdcdata", **fdc_data_file_paths)

    def test_command_saves_data(self, db, fdc_data_file_paths, nutrients):
        """
        The populatefdcdata command saves data from files.
        """
        call_command("populatefdcdata", **fdc_data_file_paths)

        names = ["test_ingredient_3", "test_ingredient_4"]
        assert Ingredient.objects.filter(name__in=names).count() == 2

    def test_command_dataset_filter(self, db, fdc_data_file_paths, nutrients):
        """
        The populatefdcdata command with a dataset_filter saves data
        only for ingredients that pass the filter.
        """
        call_command(
            "populatefdcdata", dataset_filter=["sr_legacy_food"], **fdc_data_file_paths
        )

        assert not Ingredient.objects.filter(name="test_ingredient_3").exists()

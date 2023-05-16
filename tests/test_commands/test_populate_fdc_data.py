"""Tests of the populatefdcdata command."""
import os
from io import StringIO
from tempfile import mkstemp

import pytest
from django.core.management import CommandError, call_command
from main.models import Ingredient, Nutrient


@pytest.fixture(scope="session")
def fdc_data_file_paths():
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

    yield food_path, nutrient_path, food_nutrient_path

    for path in food_path, nutrient_path, food_nutrient_path:
        os.remove(path)


def test_populatefdcdata_error_when_no_file_path_were_provided():
    """
    The populatefdcdata command raises an exception if no file paths
    are available.
    """
    with pytest.raises(CommandError):
        call_command("populatefdcdata")


def test_populatefdcdata_error_when_a_path_is_missing():
    """
    The populatefdcdata command raises an exception if a file path
    is missing and `data_dir` was not provided.
    """
    with pytest.raises(CommandError):
        call_command("populatefdcdata", food_file="tst.csv", nutrient_file="tst.csv")
    with pytest.raises(CommandError):
        call_command(
            "populatefdcdata", food_file="tst.csv", food_nutrient_file="tst.csv"
        )
    with pytest.raises(CommandError):
        call_command(
            "populatefdcdata", nutrient_file="tst.csv", food_nutrient_file="tst.csv"
        )


def test_populatefdcdata_path_overrides():
    """
    The populatefdcdata command file path arguments override file
    discovery when a `data_dir` was provided.
    """
    try:
        call_command("populatefdcdata", food_file="tst.csv", data_dir="tst/")
    except CommandError as e:
        # The error message when checking if the file exists contains
        # the names of the checked files, so the override will be
        # visible there
        assert "tst.csv" in str(e)
    else:
        assert False  # There should be an exception


def test_populatefdcdata_files_dont_exist():
    """
    The populatefdcdata command raises an exception if a file does not
    exist.
    """
    with pytest.raises(CommandError):
        call_command(
            "populatefdcdata",
            food_file="f.csv",
            nutrient_file="n.csv",
            food_nutrient_file="fn.csv",
        )


def test_populatefdcdata_error_when_no_nutrients(db, fdc_data_file_paths):
    """
    The populatefdcdata command raises an exception if none of the
    required nutrients are in the database.
    """
    food, nutrient, food_nutrient = fdc_data_file_paths
    with pytest.raises(CommandError):
        call_command(
            "populatefdcdata",
            food_file=food,
            nutrient_file=nutrient,
            food_nutrient_file=food_nutrient,
        )


def test_populatefdcdata(db, fdc_data_file_paths):
    """
    The populatefdcdata command saves data from files.
    """
    Nutrient.objects.bulk_create(
        [Nutrient(name="Protein", unit="G"), Nutrient(name="Iron", unit="MG")]
    )

    food, nutrient, food_nutrient = fdc_data_file_paths
    output = StringIO()
    call_command(
        "populatefdcdata",
        food_file=food,
        nutrient_file=nutrient,
        food_nutrient_file=food_nutrient,
        stdout=output,
    )
    names = ["test_ingredient_3", "test_ingredient_4"]
    assert Ingredient.objects.filter(name__in=names).count() == 2


def test_populatefdcdata_dataset_filter(db, fdc_data_file_paths):
    """
    The populatefdcdata command with a dataset_filter saves data only
    for ingredients that pass the filter.
    """
    Nutrient.objects.bulk_create(
        [Nutrient(name="Protein", unit="G"), Nutrient(name="Iron", unit="MG")]
    )

    food, nutrient, food_nutrient = fdc_data_file_paths
    output = StringIO()
    call_command(
        "populatefdcdata",
        food_file=food,
        nutrient_file=nutrient,
        food_nutrient_file=food_nutrient,
        dataset_filter=["sr_legacy_food"],
        stdout=output,
    )
    assert not Ingredient.objects.filter(name="test_ingredient_3").exists()

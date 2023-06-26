"""Tests of the populate_nutrient_data command."""
import pytest
from django.core.management import call_command
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.management.commands._data import (
    FULL_NUTRIENT_DATA,
    NUTRIENT_TYPE_DISPLAY_NAME,
)
from main.management.commands.populatenutrientdata import (
    Command,
    create_energy,
    create_nutrient_components,
    create_nutrient_types,
    create_nutrients,
    create_recommendations,
    get_nutrient_types,
)

NAMES = [nut["name"] for nut in FULL_NUTRIENT_DATA]


@pytest.fixture
def nutrient_data(nutrient_1):
    """Sample data list.

    first value: data
    second value: nutrient dict

    name: test_nutrient
    types: nutrient_type
    energy: 5
    recommendations:
        age_max: 3
        age_min: 1
        amount_max: 20.0
        amount_min: 5.0
        dri_type: AMDR
        sex: B
    """
    data = [
        {
            "name": "test_nutrient",
            "unit": models.Nutrient.GRAMS,
            "type": ["nutrient_type"],
            "recommendations": [
                {
                    "age_max": 3,
                    "age_min": 1,
                    "amount_max": 20.0,
                    "amount_min": 5.0,
                    "dri_type": models.IntakeRecommendation.AMDR,
                    "sex": "B",
                }
            ],
            "energy": 5,
        },
    ]
    return data


@pytest.fixture
def nutrient_1_data(nutrient_1, nutrient_data):
    """Sample data list and nutrient dict.

    first value: data
    second value: nutrient dict

    name: test_nutrient
    types: nutrient_type
    energy: 5
    recommendations:
        age_max: 3
        age_min: 1
        amount_max: 20.0
        amount_min: 5.0
        dri_type: AMDR
        sex: B
    """
    nutrient_data[0]["name"] = nutrient_1.name
    nutrient_dict = {nutrient_1.name: nutrient_1}
    return nutrient_data, nutrient_dict


@pytest.fixture
def type_data():
    """Sample nutrient type data.

    name: nutrient 1
    types: nutrient_type_1, nutrient_type_2

    name: nutrient 2
    types: nutrient_type_1, nutrient_type_3
    """
    data = [
        {
            "name": "nutrient 1",
            "type": ["nutrient_type_1", "nutrient_type_2"],
        },
        {
            "name": "nutrient 2",
            "type": ["nutrient_type_1", "nutrient_type_3"],
        },
    ]
    return data


class TestCreateNutrient:
    """Tests of the create_nutrients() function."""

    def test_save_nutrients(self, db, nutrient_data):
        """
        create_nutrients() saves to the database all specified nutrients.
        """
        create_nutrients(nutrient_data)

        nutrient = models.Nutrient.objects.first()
        assert nutrient.name == "test_nutrient"
        assert nutrient.unit == models.Nutrient.GRAMS

    def test_already_existing_nutrient(self, db, nutrient_1, nutrient_data):
        """
        create_nutrients() does not raise an exception if a nutrient that
        would be created by create_nutrients() already exists.
        """
        try:
            create_nutrients(nutrient_data)
        except IntegrityError as e:
            pytest.fail(f"create_nutrients() violated a constraint - {e}")


class TestCreateNutrientTypes:
    """Tests of the create_nutrient_types() function."""

    def test_saves_all(self, db, type_data):
        """
        create_nutrient_types() saves all the nutrient types in _data.
        """
        create_nutrient_types({}, data=type_data)

        result = {t.name for t in models.NutrientType.objects.all()}
        expected = {"nutrient_type_1", "nutrient_type_2", "nutrient_type_3"}
        assert result == expected

    def test_associates_types_with_nutrients(self, db, nutrient_1, nutrient_1_data):
        """
        create_nutrient_types() associates NutrientTypes with their
        respective Nutrients.
        """
        data, nutrient_dict = nutrient_1_data
        create_nutrient_types(nutrient_dict, data=data)

        assert nutrient_1.types.first().name == "nutrient_type"

    # TODO: The way the display names are handled needs to change
    def test_with_display_name(self, db):
        """
        create_nutrient_types() creates NutrientType records with their
        displayed names.
        """
        data = [
            {
                "name": "nutrient",
                "type": ["Fatty acid type"],
            },
        ]

        create_nutrient_types({}, data=data)

        displayed_name = models.NutrientType.objects.first().displayed_name
        expected = NUTRIENT_TYPE_DISPLAY_NAME["Fatty acid type"]
        assert displayed_name == expected

    def test_already_existing_nutrient_type(self, db, nutrient_1, nutrient_1_data):
        """
        create_nutrient_types() does not raise an exception if a nutrient
        type that would be created by create_nutrient_types() already
        exists.
        """
        data, nutrient_dict = nutrient_1_data
        models.NutrientType.objects.create(name="nutrient_type")

        try:
            create_nutrient_types(nutrient_dict, data=data)
        except IntegrityError as e:
            pytest.fail(f"create_nutrient_types() violated a constraint - {e}")


def test_create_recommendations(db, nutrient_1_data, nutrient_1):
    """
    create_recommendations() creates recommendations for nutrients
    in `nutrient_dict`, according to the information in the provided
    data.
    """
    data, nutrient_dict = nutrient_1_data

    create_recommendations(nutrient_dict, data=data)

    recommendation = nutrient_1.recommendations.first()
    data_dict = data[0]["recommendations"][0]
    assert is_from_data(data_dict, recommendation)


def test_create_energy(db, nutrient_1_data, nutrient_1):
    """
    create_energy() creates NutrientEnergy records for nutrients in
    `nutrient_dict`, according to the information in the provided
    data.
    """
    data, nutrient_dict = nutrient_1_data

    create_energy(nutrient_dict, data=data)

    assert nutrient_1.energy.amount == 5  # from fixture


class TestCreateNutrientCombinations:
    """Tests of the create_nutrient_combinations() function."""

    @pytest.fixture
    def data(self):
        """Sample compound data.

        name: compound
        unit: MG
        components: component1, component2

        name: component_1
        unit: MG

        name: component_2
        unit: MG
        """
        return [
            {
                "name": "compound",
                "unit": "MG",
                "components": ["component_1", "component_2"],
            },
            {
                "name": "component_1",
                "unit": "MG",
            },
            {
                "name": "component_2",
                "unit": "MG",
            },
        ]

    def test_creates_records(self, db, data):
        """
        create_nutrient_components() creates NutrientComponent records for
        nutrients in `nutrient_dict`, according to the information in
        the provided data.
        """

        nutrients = models.Nutrient.objects.bulk_create(
            [
                models.Nutrient(name="compound", unit="MG"),
                models.Nutrient(name="component_1", unit="MG"),
                models.Nutrient(name="component_2", unit="MG"),
            ]
        )
        instance = nutrients[0]

        create_nutrient_components(
            {nutrient.name: nutrient for nutrient in nutrients}, data=data
        )

        assert instance.components.filter(name="component_1").exists()
        assert instance.components.filter(name="component_2").exists()

    def test_missing_component_nutrient(self, db, data):
        """
        create_nutrient_components() finishes without error despite
        a component nutrient missing from the database.
        """

        nutrients = models.Nutrient.objects.bulk_create(
            [
                models.Nutrient(name="compound", unit="MG"),
                models.Nutrient(name="component_1", unit="MG"),
            ]
        )
        try:
            create_nutrient_components(
                {nutrient.name: nutrient for nutrient in nutrients}, data=data
            )
        except IntegrityError as e:
            pytest.fail(f"create_nutrient_components() violated a constraint - {e}")


class TestCommand:
    """Tests of the populate_nutrient_data command."""

    @pytest.fixture
    def cmd(self, nutrient_data):
        """
        An instance of the `populatenutrientdata` command with
        `nutrient_1_data`.
        """
        return Command(data=nutrient_data)

    def test_saves_nutrients(self, db, cmd):
        """
        The populate_nutrient_data command saves to the database
        nutrients specified in the data.
        """
        call_command(cmd)

        assert models.Nutrient.objects.filter(name="test_nutrient").exists()

    def test_saves_nutrient_types(self, db, cmd):
        """
        The populate_nutrient_data command saves to the database
        nutrient types specified in the data.
        """

        call_command(cmd)

        assert models.NutrientType.objects.first().name == "nutrient_type"

    def test_saves_intake_recommendations(self, db, cmd, nutrient_data):
        """
        The populate_nutrient_data command saves to the database
        intake recommendations specified in the data.
        """
        call_command(cmd)

        recommendation = models.IntakeRecommendation.objects.first()
        data_dict = nutrient_data[0]["recommendations"][0]
        assert is_from_data(data_dict, recommendation)

    def test_saves_nutrient_energy(self, db, cmd):
        """
        The populate_nutrient_data command saves to the database
        nutrient energies specified in the data.
        """
        call_command(cmd)

        assert models.NutrientEnergy.objects.first().amount == 5

    def test_saves_nutrient_components(self, db):
        """
        The populate_nutrient_data command saves to the database
        nutrient components specified in the data.
        """

        data = [
            {
                "name": "compound",
                "unit": models.Nutrient.GRAMS,
                "components": ["component"],
                "recommendations": [],
                "type": [],
            },
            {
                "name": "component",
                "unit": models.Nutrient.GRAMS,
                "recommendations": [],
                "type": [],
            },
        ]
        cmd = Command(data)

        call_command(cmd)

        instance = models.NutrientComponent.objects.first()

        assert instance.target.name == "compound"
        assert instance.component.name == "component"


def test_get_nutrient_types(type_data):
    """
    The get_nutrient_types() function retrieves nutrient type names
    from data in the format of FULL_NUTRIENT_DATA.
    """
    result = get_nutrient_types(type_data)

    expected = {"nutrient_type_1", "nutrient_type_2", "nutrient_type_3"}
    assert result == expected


def is_from_data(data_dict: dict, instance: object) -> bool:
    """Check if the `instance` holds the same data as the `data_dict`.

    The `instance` attribute names must match the `data_dict` keys.
    """
    instance_data = {k: vars(instance)[k] for k in data_dict.keys()}
    return instance_data == data_dict

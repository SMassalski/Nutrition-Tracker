"""Class dummies"""
from dataclasses import dataclass
from typing import List


class ModelDummyBase:
    """Base class for model dummies.

    Keeps saved instances in the class' `saved` attribute.
    """

    saved = None
    objects = None

    def save(self, *_args, **_kwargs) -> None:
        """Append instance to `saved`"""
        if self.saved is None:
            self.saved = []
        self.saved.append(self)

    @classmethod
    def clear_saved(cls):
        """Clear the saved list"""
        cls.saved = []
        if cls.objects is not None:
            cls.objects.saved = cls.saved


class DummyManager:
    """Dummy model manager class"""

    def __init__(self, saved):
        self.saved = saved

    def values_list(self, *fields: str) -> List[tuple]:
        """Retrieve the specified field values of saved instances.

        Parameters
        ----------
        fields
            Names of fields
        """
        result = []
        for model_instance in self.saved:
            result.append(tuple(getattr(model_instance, field) for field in fields))
        return result

    def bulk_create(self, objs: List):
        """Bulk save multiple instances"""
        self.saved += objs


@dataclass
class DummyNutrient(ModelDummyBase):
    """Dummy for nutrient model"""

    id: int = None
    fdc_id: int = None
    unit: str = None
    name: str = None

    saved = []
    objects = DummyManager(saved)


@dataclass
class DummyIngredient(ModelDummyBase):
    """Dummy for ingredient model"""

    id: int = None
    fdc_id: int = None
    dataset: str = None
    name: str = None

    saved = []
    objects = DummyManager(saved)


@dataclass
class DummyIngredientNutrient(ModelDummyBase):
    """Dummy for ingredient nutrient model"""

    id: int = None
    ingredient_id: int = None
    nutrient_id: int = None
    amount: int = 0

    saved = []
    objects = DummyManager(saved)

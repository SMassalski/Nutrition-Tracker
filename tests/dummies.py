"""Class dummies"""
from dataclasses import dataclass


class ModelDummyBase:
    """Base class for model dummies.

    Keeps saved instances in the class' `saved` attribute.
    """

    saved = None

    def save(self, *_args, **_kwargs) -> None:
        """Append instance to `saved`"""
        if self.saved is not None:
            self.saved.append(self)

    @classmethod
    def clear_saved(cls):
        """Clear the saved list"""
        if cls.saved is not None:
            cls.saved = []


@dataclass
class DummyNutrient(ModelDummyBase):
    """Dummy for nutrient model"""

    fdc_id: int = None
    unit: str = None
    name: str = None

    saved = []


@dataclass
class DummyIngredient(ModelDummyBase):
    """Dummy for ingredient model"""

    fdc_id: int = None
    dataset: str = None
    name: str = None

    saved = []

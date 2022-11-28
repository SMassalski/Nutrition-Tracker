"""Class dummies"""
from dataclasses import dataclass


@dataclass
class DummyNutrient:
    """Dummy for nutrient model"""
    fdc_id: int = None
    unit: str = None
    name: str = None
    
    saved = []
    
    def save(self, *_args, **_kwargs) -> None:
        """Append nutrient to `saved` if provided"""
        if self.saved is not None:
            self.saved.append(self)
            
    @classmethod
    def clear_saved(cls):
        """Clear the class' saved list"""
        cls.saved = []

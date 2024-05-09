"""Main app's signal receivers."""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import IngredientNutrient, NutrientComponent, WeightMeasurement
from .models.foods import update_compound_nutrients


@receiver(post_delete, sender=WeightMeasurement, dispatch_uid="weight_post_delete")
def weight_delete_handler(sender, instance, **_kwargs):
    """Update the profile's weight after a measurement is deleted."""
    instance.profile.save(recalculate_weight=True)


@receiver(post_delete, sender=NutrientComponent, dispatch_uid="nut_comp_post_delete")
def nutrient_component_delete_handler(sender, instance, **_kwargs):
    """Update the compound nutrient after a component is deleted."""

    # Update energy value
    if instance.target.is_compound:
        instance.target.update_compound_energy()
    else:
        instance.target.energy = 0
        instance.target.save()

    # Update Ingredient Nutrient amount
    update_compound_nutrients(instance.target, clear_old=True)


@receiver(post_delete, sender=IngredientNutrient, dispatch_uid="ing_nut_post_delete")
def ingredient_nutrient_delete_handler(sender, instance, **_kwargs):
    """Update the compound nutrient after a component is deleted."""

    for compound in instance.nutrient.compounds.all():
        update_compound_nutrients(compound, clear_old=True)

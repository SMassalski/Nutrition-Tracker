"""Main app's signal receivers."""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import NutrientComponent, WeightMeasurement


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

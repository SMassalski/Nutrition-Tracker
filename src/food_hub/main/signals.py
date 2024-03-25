"""Main app's signal receivers."""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import WeightMeasurement


@receiver(post_delete, sender=WeightMeasurement, dispatch_uid="weight_post_delete")
def weight_delete_handler(sender, instance, **_kwargs):
    """Update the profile's weight after a measurement is deleted."""
    instance.profile.save(recalculate_weight=True)

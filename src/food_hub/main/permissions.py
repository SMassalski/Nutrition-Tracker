"""Main app's DRF permissions."""
from main import models
from rest_framework.permissions import BasePermission


class IsMealOwnerPermission(BasePermission):
    """
    Permission allowing only the owner of a meal to view or modify
    the meal.
    """

    # docstr-coverage: inherited
    def has_permission(self, request, view):
        meal_id = view.kwargs.get(view.lookup_url_kwarg)

        return models.Profile.objects.filter(
            user=request.user, meal__id=meal_id
        ).exists()


class IsMealComponentOwnerPermission(BasePermission):
    """
    Object permission allowing only the owner of a meal related to the
    object to view or modify it.
    """

    # docstr-coverage: inherited
    def has_object_permission(self, request, view, obj):

        return models.Profile.objects.filter(
            user=request.user, meal__id=obj.meal_id
        ).exists()

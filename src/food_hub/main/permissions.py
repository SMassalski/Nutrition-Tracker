"""Main app's DRF permissions."""
from rest_framework.permissions import BasePermission


class IsCollectionOwnerPermission(BasePermission):
    """
    Permission allowing only the owner of a collection to view or modify
    the collection.
    """

    # docstr-coverage: inherited
    def has_permission(self, request, view):
        lookup_kwarg = (
            getattr(view, "lookup_url_kwarg", None)
            or view.through_collection_field_name()
        )
        collection_id = view.kwargs.get(lookup_kwarg)

        return view.collection_model._default_manager.filter(
            owner=request.user.profile, pk=collection_id
        ).exists()


class IsCollectionComponentOwnerPermission(BasePermission):
    """
    Object permission allowing only the owner of a collection
    the object belongs to, to view or modify it.
    """

    # docstr-coverage: inherited
    def has_object_permission(self, request, view, obj):

        instance = getattr(obj, view.through_collection_field_name())

        return instance.owner_id == request.user.profile.id


class IsOwnerPermission(BasePermission):
    """
    Object permission allowing only the owner of the object to view
    or modify it.
    """

    # docstr-coverage: inherited
    def has_object_permission(self, request, view, obj):
        obj_profile = getattr(obj, "owner_id", None) or getattr(obj, "profile_id", None)
        return obj_profile == request.user.profile.id


class CreateWithoutProfilePermission(BasePermission):
    """
    Allow POST method only if the user hasn't yet created a profile.
    """

    # docstr-coverage: inherited
    def has_permission(self, request, view):
        return request.method != "POST" or not hasattr(request.user, "profile")

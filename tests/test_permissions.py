"""Tests of main app's DRF permissions."""
from main.permissions import IsMealComponentOwnerPermission, IsMealOwnerPermission
from rest_framework.generics import GenericAPIView


class TestIsMealOwnerPermission:
    def test_has_permission_not_owner(self, rf, meal, new_user):
        """
        Permission is denied if the user does not own the meal
        indicated by the `meal_id` url kwarg.
        """
        request = rf.get("/")
        request.user = new_user
        view = GenericAPIView(lookup_url_kwarg="meal_id")
        view.setup(request, meal_id=meal.id)
        permission = IsMealOwnerPermission()

        assert not permission.has_permission(view.request, view)

    def test_owner_has_permission(self, rf, meal, user):
        """
        Permission is granted if the user is the owner of the meal
        indicated by the `meal_id` url kwarg.
        """
        request = rf.get("/")
        request.user = user
        view = GenericAPIView(lookup_url_kwarg="meal_id")
        view.setup(request, meal_id=meal.id)
        permission = IsMealOwnerPermission()

        assert permission.has_permission(view.request, view)

    def test_has_permission_num_queries(
        self, rf, django_assert_num_queries, meal, user
    ):
        """The permission check makes only a single database query."""
        request = rf.get("/")
        request.user = user
        view = GenericAPIView(lookup_url_kwarg="meal_id")
        view.setup(request, meal_id=meal.id)
        permission = IsMealOwnerPermission()

        with django_assert_num_queries(1):
            permission.has_permission(view.request, view)


class TestIsMealComponentOwnerPermission:
    def test_has_object_permission_not_owner(self, rf, meal_ingredient, new_user):
        """
        has_object_permission() returns False if the authenticated user
        is not the owner of the meal related to the object.
        """
        request = rf.get("/")
        request.user = new_user
        view = GenericAPIView()
        view.setup(request, pk=meal_ingredient.id)
        permission = IsMealComponentOwnerPermission()

        assert not permission.has_object_permission(view.request, view, meal_ingredient)

    def test_has_object_permission_owner(self, rf, meal_ingredient, user):
        """
        has_object_permission() returns `True` if the authenticated user
        is the owner of the meal related to the object.
        """
        request = rf.get("/")
        request.user = user
        view = GenericAPIView()
        view.setup(request, pk=meal_ingredient.id)
        permission = IsMealComponentOwnerPermission()

        assert permission.has_object_permission(view.request, view, meal_ingredient)

    def test_has_object_permission_num_queries(
        self, rf, django_assert_num_queries, meal_ingredient, user
    ):
        """
        The object permission check makes only a single database query.
        """
        request = rf.get("/")
        request.user = user
        view = GenericAPIView(lookup_url_kwarg="meal_id")

        with django_assert_num_queries(1):
            view.setup(request, pk=meal_ingredient.id)
            permission = IsMealComponentOwnerPermission()
            permission.has_object_permission(view.request, view, meal_ingredient)

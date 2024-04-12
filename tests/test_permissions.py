"""Tests of main app's DRF permissions."""
from main import permissions
from main.models import Meal
from main.views.api.base_views import ComponentCollectionViewSet
from rest_framework.generics import GenericAPIView


class ViewSet(ComponentCollectionViewSet):
    component_field_name = "ingredients"
    collection_model = Meal


class TestIsCollectionOwnerPermission:
    def test_has_permission_not_owner(self, rf, meal, new_user):
        """
        Permission is denied if the user does not own the meal
        indicated by the `meal_id` url kwarg.
        """
        request = rf.get("/")
        request.user = new_user
        view = ViewSet()
        view.setup(request, meal=meal.id)
        permission = permissions.IsCollectionOwnerPermission()

        assert not permission.has_permission(view.request, view)

    def test_owner_has_permission(self, rf, meal, user):
        """
        Permission is granted if the user is the owner of the meal
        indicated by the `meal_id` url kwarg.
        """
        request = rf.get("/")
        request.user = user
        view = ViewSet()
        view.setup(request, meal=meal.id)
        permission = permissions.IsCollectionOwnerPermission()

        assert permission.has_permission(view.request, view)

    def test_has_permission_num_queries(
        self, rf, django_assert_num_queries, meal, user
    ):
        """The permission check makes only a single database query."""
        request = rf.get("/")
        request.user = user
        view = ViewSet()
        view.setup(request, meal=meal.id)
        permission = permissions.IsCollectionOwnerPermission()

        with django_assert_num_queries(1):
            permission.has_permission(view.request, view)


class TestIsCollectionComponentOwnerPermission:
    def test_has_object_permission_not_owner(self, rf, meal_ingredient, new_user):
        """
        has_object_permission() returns False if the authenticated user
        is not the owner of the meal related to the object.
        """
        request = rf.get("/")
        request.user = new_user
        view = ViewSet()
        view.setup(request, pk=meal_ingredient.id)
        permission = permissions.IsCollectionComponentOwnerPermission()

        assert not permission.has_object_permission(view.request, view, meal_ingredient)

    def test_has_object_permission_owner(self, rf, meal_ingredient, user):
        """
        has_object_permission() returns `True` if the authenticated user
        is the owner of the meal related to the object.
        """
        request = rf.get("/")
        request.user = user
        view = ViewSet()
        view.setup(request, pk=meal_ingredient.id)
        permission = permissions.IsCollectionComponentOwnerPermission()

        assert permission.has_object_permission(view.request, view, meal_ingredient)

    def test_has_object_permission_num_queries(
        self, rf, django_assert_num_queries, meal_ingredient, user
    ):
        """
        The object permission check makes only a single database query.
        """
        request = rf.get("/")
        request.user = user
        view = ViewSet()

        with django_assert_num_queries(0):
            # All queries are done before in the test setup
            view.setup(request, pk=meal_ingredient.id)
            permission = permissions.IsCollectionComponentOwnerPermission()
            permission.has_object_permission(view.request, view, meal_ingredient)


class TestIsOwnerPermission:
    def test_has_object_permission_not_owner(self, rf, meal, new_user):
        request = rf.get("/")
        request.user = new_user
        view = GenericAPIView()
        view.setup(request, pk=meal.id)
        permission = permissions.IsOwnerPermission()

        assert not permission.has_object_permission(view.request, view, meal)

    def test_has_object_permission_owner(self, rf, meal, user):
        request = rf.get("/")
        request.user = user
        view = GenericAPIView()
        view.setup(request, pk=meal.id)
        permission = permissions.IsOwnerPermission()

        assert permission.has_object_permission(view.request, view, meal)

    def test_checks_profile_attribute(self, rf, weight_measurement, user):
        request = rf.get("/")
        request.user = user
        view = GenericAPIView()
        view.setup(request, pk=weight_measurement.id)
        permission = permissions.IsOwnerPermission()

        assert permission.has_object_permission(view.request, view, weight_measurement)

    def test_has_object_permission_num_queries(
        self, rf, django_assert_num_queries, meal, user
    ):
        request = rf.get("/")
        request.user = user
        view = GenericAPIView()

        with django_assert_num_queries(0):
            # All queries are done before in the test setup
            view.setup(request, pk=meal.id)
            permission = permissions.IsOwnerPermission()
            permission.has_object_permission(view.request, view, meal)

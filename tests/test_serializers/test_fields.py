from core.models import Meal
from core.serializers.fields import OwnedPrimaryKeyField
from rest_framework.serializers import Serializer as SerializerBase


class TestOwnedPrimaryKeyField:
    class Serializer(SerializerBase):

        meal = OwnedPrimaryKeyField(queryset=Meal.objects.all())

    def test_allows_access_to_owner(self, meal, user, rf):
        request = rf.get("")
        request.user = user
        ctx = {"request": request}
        serializer = self.Serializer(data={"meal": meal.id}, context=ctx)

        assert serializer.is_valid()

    def test_denies_access_to_not_owners(self, meal, new_user, rf):
        request = rf.get("")
        request.user = new_user
        ctx = {"request": request}
        serializer = self.Serializer(data={"meal": meal.id}, context=ctx)

        assert not serializer.is_valid()

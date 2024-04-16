"""Custom serializer fields."""
from rest_framework.serializers import PrimaryKeyRelatedField


class OwnedPrimaryKeyField(PrimaryKeyRelatedField):
    """
    PrimaryKeyRelatedField that limits the accessible instances to
    those owned by the user.

    Requires an authenticated request in the context to work correctly.
    """

    def __init__(self, owner_lookup="owner", **kwargs):
        super().__init__(**kwargs)
        assert kwargs.get("read_only") or hasattr(self.queryset.model, owner_lookup), (
            f"Incorrect owner lookup {owner_lookup} for the {self.queryset.model} "
            f"model."
        )
        self.owner_lookup = owner_lookup

    # docstr-coverage: inherited
    def get_queryset(self):
        assert self.context.get("request"), (
            "OwnedPrimaryKeyField requires an authenticated request in the context "
            "to work correctly."
        )
        profile = self.context["request"].user.profile
        return self.queryset.filter(**{self.owner_lookup: profile})

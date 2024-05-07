"""Custom serializer fields."""
from rest_framework.serializers import PrimaryKeyRelatedField


class OwnedPrimaryKeyField(PrimaryKeyRelatedField):
    """
    PrimaryKeyRelatedField that limits the accessible instances to
    those owned by the user.

    Hides unowned instances in generated select fields.

    Requires an authenticated request in the context to work correctly.
    """

    def __init__(self, owner_lookup="owner", **kwargs):
        """Primary key field preventing access to unowned instances.

        Hides unowned instances in generated select fields.

        Parameters
        ----------
        owner_lookup: str
            The name of the field referencing the owning profile.
        """
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

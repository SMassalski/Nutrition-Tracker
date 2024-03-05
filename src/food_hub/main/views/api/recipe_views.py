"""API views associated with the `Recipe` model."""
from main import models, serializers
from main.views.api.base_views import ComponentCollectionViewSet, NutrientIntakeView
from main.views.generics import ModelViewSet
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.reverse import reverse

__all__ = ("RecipeIngredientViewSet", "RecipeViewSet", "RecipeIntakeView")


class RecipeIngredientViewSet(ComponentCollectionViewSet):
    """
    The ComponentCollectionViewSet for the Recipe-Ingredient
    relationship.
    """

    collection_model = models.Recipe
    component_field_name = "ingredients"
    htmx_events = ["recipeComponentsChanged"]
    serializer_class = serializers.RecipeIngredientSerializer


class RecipeIntakeView(NutrientIntakeView):
    """NutrientIntakeView for the recipe model."""

    collection_model = models.Recipe
    lookup_url_kwarg = "recipe"


class RecipeViewSet(ModelViewSet):
    """A ModelViewSet for the `Recipe` model.

    Only lists recipes owned by the request's user.
    """

    serializer_class = serializers.RecipeSerializer
    component_list_template_name = "main/data/component_search_result_list.html"
    list_template_name = "main/data/recipe_search_result_list.html"
    modal_form_template = "main/modals/new_recipe_form.html"
    recipe_edit_form_template = "main/data/recipe_detail_form.html"
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    template_map = {
        "create": modal_form_template,
        "retrieve": recipe_edit_form_template,
        "update": recipe_edit_form_template,
        "partial_update": recipe_edit_form_template,
        "destroy": "main/blank.html",
        "default": component_list_template_name,
    }

    # docstr-coverage: inherited
    def get_queryset(self):
        owner = self.request.user.profile
        return models.Recipe.objects.filter(owner=owner).order_by("name")

    # docstr-coverage: inherited
    def get_template_names(self):
        if self.action == "list" and self.request.GET.get("target") == "edit":
            return [self.list_template_name]
        return super().get_template_names()

    # docstr-coverage: inherited
    def get_template_context(self, data):
        return {"obj_type": "recipes", "preview_url_name": "meal-recipe-preview"}

    # docstr-coverage: inherited
    def get_success_headers(self, data):
        redirect = self.request.GET.get("redirect", "").lower() == "true"
        headers = super().get_success_headers(data)
        if self.action == "create" and redirect:
            headers["HX-Redirect"] = reverse("recipe-edit", args=(data["obj"].slug,))
        elif self.action in ("update", "partial_update"):
            headers["HX-Location"] = reverse("recipe-edit", args=(data["obj"].slug,))
        elif self.action == "destroy":
            headers["HX-Redirect"] = reverse("recipe")

        return headers

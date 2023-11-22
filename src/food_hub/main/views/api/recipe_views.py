"""API views associated with the `Recipe` model."""
from main import models, serializers
from main.views.api.base_views import ComponentCollectionViewSet, NutrientIntakeView
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet

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

    # docstr-coverage: inherited
    def get_queryset(self):
        owner = self.request.user.profile
        return models.Recipe.objects.filter(owner=owner).order_by("name")

    # docstr-coverage: inherited
    def get_template_names(self):
        if self.detail:
            return [self.recipe_edit_form_template]
        elif self.action == "create":
            return [self.modal_form_template]
        elif self.action == "list" and self.request.GET.get("target") == "edit":
            return [self.list_template_name]
        return [self.component_list_template_name]

    # docstr-coverage: inherited
    def list(self, *args, **kwargs):
        response = super().list(*args, **kwargs)
        response.data["obj_type"] = "recipes"
        return response

    # docstr-coverage: inherited
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            data = {
                "name": request.data.get("name"),
                "final_weight": request.data.get("final_weight"),
                "errors": e.detail,
            }
            # TODO: Currently uses 200 status code because core HTMX wont
            #  swap with a different code. The 'response-target` HTMX plugin
            #  can be a solution
            return Response(data, template_name=self.modal_form_template)
        instance = serializer.save()
        headers = self.get_success_headers(serializer.data)
        redirect = self.request.GET.get("redirect")
        if redirect and redirect.lower() == "true":
            headers["HX-Redirect"] = reverse("recipe-edit", args=(instance.slug,))

        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    # docstr-coverage: inherited
    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            response.headers["HX-Location"] = reverse(
                "recipe-edit", args=(response.data["slug"],)
            )
            return response
        except ValidationError as e:
            errors = e.detail
            # TODO: Update HTMX >= 1.9.3.
            #   HX-Reselect won't work without it
            headers = {
                "HX-Reselect": "#recipe-update-errors",
                "HX-Retarget": "#recipe-update-errors",
                "HX-Reswap": "outerHTML",
            }
            return Response({"errors": errors}, headers=headers)

    # docstr-coverage: inherited
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.headers["HX-Redirect"] = reverse("recipe")
        return response

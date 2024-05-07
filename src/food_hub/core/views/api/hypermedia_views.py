"""Views exclusively for making changes to the page's DOM."""
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

__all__ = ("MealComponentTabView",)


class MealComponentTabView(APIView):
    """
    View for rendering object type selection tabs in the component
    search of the meal page.
    """

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "core/components/add_ingredient_tabs.html"
    tabs = [("Ingredients", "ingredient-list"), ("Recipes", "recipe-list")]

    def get(self, request):
        """
        Render the object type selection tabs with `tab` set to active.
        """
        query = request.GET.get("tab")
        active = query.lower() if query else None
        tabs = []
        url = None
        for tab, pattern in self.tabs:
            selected = tab.lower() == active
            if selected:
                url = reverse(pattern)
            tabs.append((tab, selected))

        return Response({"tabs": tabs, "url": url})

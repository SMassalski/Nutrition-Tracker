"""Tests of main app's API views"""
import json

from main.views import api as views
from rest_framework import status
from rest_framework.reverse import reverse

# API root


def test_api_root_status_code(rf):
    """api_root_view() response has a 200 status code"""
    url = reverse("api-root")
    request = rf.get(url)
    response = views.api_root(request)
    assert response.status_code == status.HTTP_200_OK


def test_api_root_contains_links_to_list_views(rf):
    """
    api_root_view() response contains urls to ingredient and nutrient
    list views.
    """
    url = reverse("api-root")
    request = rf.get(url)
    response = views.api_root(request, format="json")
    response.render()
    content = json.loads(response.content)

    assert content.get("Ingredients").endswith("api/ingredients/")
    assert content.get("Nutrients").endswith("api/nutrients/")


# Ingredient views


def test_ingredient_view_status_code(rf, db):
    """IngredientView response has a 200 status code"""
    url = reverse("ingredient-list")
    request = rf.get(url)
    assert views.IngredientView.as_view()(request).status_code == status.HTTP_200_OK


def test_ingredient_view_lists_ingredients(rf, db, ingredient_1, ingredient_2):
    """IngredientView response contains a list of ingredient records"""
    url = reverse("ingredient-list")
    request = rf.get(url)
    response = views.IngredientView.as_view()(request, format="json")
    response.render()
    content = json.loads(response.content)["results"]
    assert len(content) == 2
    assert content[0]["name"] in (ingredient_1.name, ingredient_2.name)
    assert content[1]["name"] in (ingredient_1.name, ingredient_2.name)


def test_ingredient_view_fields(rf, db, ingredient_1):
    """IngredientView response entry contains the correct fields"""
    url = reverse("ingredient-list")
    request = rf.get(url)
    response = views.IngredientView.as_view()(request, format="json")
    response.render()
    entry = json.loads(response.content)["results"][0]
    assert set(entry.keys()) == {"id", "name", "url"}


def test_ingredient_detail_view_status_code(rf, db, ingredient_1):
    """IngredientDetailView response has a 200 status code"""
    pk = ingredient_1.pk
    url = reverse("ingredient-detail", args=[pk])
    request = rf.get(url)
    response = views.IngredientDetailView.as_view()(request, pk=pk)

    assert response.status_code == status.HTTP_200_OK


def test_ingredient_detail_view_fields(rf, db, ingredient_1):
    """IngredientDetailView response entry contains the correct fields"""
    pk = ingredient_1.pk
    url = reverse("ingredient-detail", args=[pk])
    request = rf.get(url)
    response = views.IngredientDetailView.as_view()(request, pk=pk, format="json")
    response.render()
    entry = json.loads(response.content)

    assert set(entry.keys()) == {"fdc_id", "name", "dataset", "nutrients"}


def test_ingredient_detail_view_nutrients_field(
    rf, db, ingredient_1, ingredient_nutrient_1_1
):
    """IngredientDetailView response entry contains the correct fields"""
    pk = ingredient_1.pk
    url = reverse("ingredient-detail", args=[pk])
    request = rf.get(url)
    response = views.IngredientDetailView.as_view()(request, pk=pk, format="json")
    response.render()
    nutrient_entry = json.loads(response.content)["nutrients"][0]

    assert set(nutrient_entry.keys()) == {"url", "nutrient", "amount"}


# Nutrient view


def test_nutrient_view_status_code(rf, db):
    """NutrientView response has a 200 status code"""
    url = reverse("nutrient-list")
    request = rf.get(url)
    assert views.NutrientView.as_view()(request).status_code == status.HTTP_200_OK


def test_nutrient_view_lists_nutrients(rf, db, nutrient_1, nutrient_2):
    """NutrientView response contains a list of nutrient records"""
    url = reverse("nutrient-list")
    request = rf.get(url)
    response = views.NutrientView.as_view()(request, format="json")
    response.render()
    content = json.loads(response.content)["results"]
    assert len(content) == 2
    assert content[0]["name"] in (nutrient_1.name, nutrient_2.name)
    assert content[1]["name"] in (nutrient_1.name, nutrient_2.name)


def test_nutrient_view_fields(rf, db, nutrient_1):
    """NutrientView response entry contains the correct fields"""
    url = reverse("nutrient-list")
    request = rf.get(url)
    response = views.NutrientView.as_view()(request, format="json")
    response.render()
    entry = json.loads(response.content)["results"][0]
    assert set(entry.keys()) == {"name", "url"}


def test_nutrient_detail_view_status_code(rf, db, nutrient_1):
    """NutrientDetailView response has a 200 status code"""
    pk = nutrient_1.pk
    url = reverse("nutrient-detail", args=[pk])
    request = rf.get(url)
    response = views.NutrientDetailView.as_view()(request, pk=pk)

    assert response.status_code == status.HTTP_200_OK


def test_nutrient_detail_view_fields(rf, db, nutrient_1):
    """NutrientDetailView response entry contains the correct fields"""
    pk = nutrient_1.pk
    url = reverse("nutrient-detail", args=[pk])
    request = rf.get(url)
    response = views.NutrientDetailView.as_view()(request, pk=pk, format="json")
    response.render()
    entry = json.loads(response.content)

    assert set(entry.keys()) == {"fdc_id", "name", "unit"}

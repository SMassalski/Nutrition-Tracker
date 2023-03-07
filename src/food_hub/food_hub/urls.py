"""food_hub URL Configuration."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
    path("authentication/", include("authentication.urls")),
    path("api/", include("main.api_urls")),
    path("api-auth/", include("rest_framework.urls")),
]

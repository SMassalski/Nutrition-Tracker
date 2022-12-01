"""main app URL Configuration"""
from django.urls import path

from .views import main as views

urlpatterns = [path("", views.home, name="home")]

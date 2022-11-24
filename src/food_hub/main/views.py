"""main app views"""
from django.http import HttpResponse


def home(_request):
    """Initial home view."""
    return HttpResponse("<h1>Hello World!</h1>")

"""Main app's regular views"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView
from main import models
from main.forms import ProfileForm

from .session_util import is_meal_expired, ping_meal_interact


@login_required
def profile_view(request):
    """
    View for setting up a user profile for intake recommendation
    calculations.
    """
    instance = getattr(request.user, "profile", None)
    from_registration = request.GET.get("from") == "registration"
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=instance)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect("profile-done")
    else:
        form = ProfileForm(instance=instance)

    return render(
        request,
        "main/profile.html",
        {
            "form": form,
            "from_registration": from_registration,
        },
    )


class MealView(TemplateView):
    """View for viewing, creating and editing meals.

    This class only handles the layout and current meal management.
    """

    template_name = "main/meal.html"

    # docstr-coverage: inherited
    def get(self, request, *args, **kwargs) -> HttpResponse:

        response = super().get(request, *args, **kwargs)

        # Retrieve or create the current meal. Check if expired.
        meal_id = self.request.session.get("meal_id")

        if meal_id is None or is_meal_expired(self.request):
            meal = models.Meal.objects.get_or_create(
                owner=self.request.user.profile, date=timezone.now().date()
            )[0]
            self.request.session["meal_id"] = meal.id

        ping_meal_interact(self.request)

        return response

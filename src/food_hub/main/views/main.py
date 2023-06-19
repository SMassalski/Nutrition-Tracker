"""main app's regular views"""
from random import random

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from main.forms import ProfileForm
from main.models import IntakeRecommendation
from main.serializers import ProfileRecommendationSerializer


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
    """View for viewing, creating and editing meals."""

    display_order = (
        "Vitamin",
        "Mineral",
        "Fatty acid type",
        "Amino acid",
    )
    template_name = "main/compose_meal.html"

    # docstr-coverage: inherited
    def get_context_data(self, **kwargs) -> HttpResponse:

        context = super().get_context_data(**kwargs)

        # Convert to snake case
        display_order = tuple(type_.replace(" ", "_") for type_ in self.display_order)

        profile = self.request.user.profile
        queryset = (
            IntakeRecommendation.objects.for_profile(profile)
            .select_related("nutrient", "nutrient__energy")
            .prefetch_related("nutrient__types")
            .order_by("nutrient__name")
        )

        recommends = ProfileRecommendationSerializer(
            queryset, many=True, context={"profile": profile}
        )
        nutrients_by_type = {}

        for rec in recommends.data:
            # Combine with intake data
            amount_min = rec.get("profile_amount_min")

            # TODO: Later retrieve intake from meal model
            intake = round(random() * (amount_min or 5) * 1.5, 1)
            rec["intake"] = intake
            rec["over_limit"] = intake >= rec.get("upper_limit")

            try:
                progress = min(round(intake * 100 / amount_min), 100)
            except (ZeroDivisionError, TypeError):  # ALAP, AMDR missing energy or other
                progress = None
            rec["progress"] = progress

            # Adding to the nutrient_types
            for type_, displayed_name in rec.get("types"):
                key = type_.replace(" ", "_")
                if key not in nutrients_by_type:
                    nutrients_by_type[key] = {
                        "name": displayed_name or type_,
                        "nutrients": [],
                    }
                nutrients_by_type[key]["nutrients"].append(rec)

        displayed_nutrients = {
            type_: nutrients_by_type.get(type_) for type_ in display_order
        }

        context.update(
            {
                "nutrients": nutrients_by_type,
                "displayed_nutrients": displayed_nutrients,
            }
        )

        return context

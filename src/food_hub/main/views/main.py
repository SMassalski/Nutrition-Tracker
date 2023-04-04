"""main app's regular views"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from main.forms import ProfileForm


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

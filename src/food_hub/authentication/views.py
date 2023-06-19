"""Views associated with authentication functionality."""
from authentication.forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy


def register_user(request):
    """User registration view."""
    # Redirect to dashboard if logged-in
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user and login
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return redirect(f"{reverse('profile')}?from=registration")
    else:
        form = CustomUserCreationForm()
    return render(request, "auth/registration.html", {"form": form})


class CustomPasswordChangeView(auth_views.PasswordChangeView):
    """View for changing passwords for logged-in users."""

    success_url = reverse_lazy("password-change-done")


class CustomPasswordResetView(auth_views.PasswordResetView):
    """View for resetting a user's password."""

    success_url = reverse_lazy("password-reset-done")
    subject_template_name = "auth/emails/password_reset_subject.txt"
    email_template_name = "auth/emails/password_reset.txt"
    html_email_template_name = "auth/emails/password_reset.html"


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View for completing password reset by setting the new password.
    """

    success_url = reverse_lazy("password-reset-complete")

"""Authentication app URL Configuration"""
from authentication.views import (
    CustomPasswordChangeView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetView,
    register_user,
)
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="auth/home.html"), name="auth-home"),
    # Registration
    path("register/", register_user, name="registration"),
    # Login / Logout
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    # Password Change
    path(
        "password-change/",
        CustomPasswordChangeView.as_view(
            template_name="auth/password_change.html",
        ),
        name="password-change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="auth/password_change_done.html",
        ),
        name="password-change-done",
    ),
    # Password Reset
    path(
        "password-reset/",
        CustomPasswordResetView.as_view(
            template_name="auth/password_reset.html",
        ),
        name="password-reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html",
        ),
        name="password-reset-done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html",
        ),
        name="password-reset-confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html",
        ),
        name="password-reset-complete",
    ),
]

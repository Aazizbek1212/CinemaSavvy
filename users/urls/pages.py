from django.urls import path
from users.views.api import VerifyEmailView
from users.views.pages import (
    LoginPageView,
    RegisterPageView,
    LogoutView,
    ProfilePageView,
    SubscriptionPageView,
    EmailVerificationRequiredView,
    PasswordResetPageView,
    PasswordResetConfirmPageView,
)
from django.views.generic import TemplateView

app_name = "auth"

urlpatterns = [
    path("login/",
         LoginPageView.as_view(),
         name="login"),

    path("register/",
         RegisterPageView.as_view(),
         name="register"),

    path("register/success/",
         TemplateView.as_view(template_name="auth/register_success.html"),
         name="register-success"),

    path("logout/",
         LogoutView.as_view(),
         name="logout"),

    path("profile/",
         ProfilePageView.as_view(),
         name="profile"),

    path("subscription/",
         SubscriptionPageView.as_view(),
         name="subscription"),

    path("verify-email/required/",
         EmailVerificationRequiredView.as_view(),
         name="email-verification-required"),

    path("verify-email/<str:uid>/<str:token>/",
         VerifyEmailPageView.as_view(),
         name="verify-email"),

    path("password-reset/",
         PasswordResetPageView.as_view(),
         name="password-reset"),

    path("password-reset/<str:uid>/<str:token>/",
         PasswordResetConfirmPageView.as_view(),
         name="password-reset-confirm"),

    path("password-reset/done/",
         TemplateView.as_view(template_name="auth/password_reset_done.html"),
         name="password-reset-done"),
]
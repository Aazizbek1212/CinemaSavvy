from django.urls import path
from users.views.pages import (
    LoginPageView,
    RegisterPageView,
    LogoutView,
    ProfilePageView,
    SubscriptionPageView,
    EmailVerificationRequiredView,
    EmailVerificationView,
    RegisterSuccessView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
)
from django.views.generic import TemplateView

app_name = "auth"

urlpatterns = [
    path("login/", LoginPageView.as_view(), name="login"),
    path("register/", RegisterPageView.as_view(), name="register"),
    path("register/success/", RegisterSuccessView.as_view(), name="register-success"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfilePageView.as_view(), name="profile"),
    path("subscription/", SubscriptionPageView.as_view(), name="subscription"),
    path("verify-email/required/", EmailVerificationRequiredView.as_view(), name="email-verification-required"),
    path("verify-email/<str:token>/", EmailVerificationView.as_view(), name="verify-email"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset/done/", PasswordResetDoneView.as_view(), name="password-reset-done"),
    path("password-reset/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]

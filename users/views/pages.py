import logging
from typing import Any

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from users.views.api import VerifyEmailView

from users.models import CustomUser
from users.tasks import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)


class LoginPageView(TemplateView):
    template_name = "auth/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["next"] = self.request.GET.get("next", "/")
        return ctx

    def post(self, request, *args, **kwargs):
        email    = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "/")

        if not email or not password:
            return self.render_to_response(
                self.get_context_data(error="Email va parol kiritish majburiy")
            )

        user = authenticate(request, email=email, password=password)

        if user is None:
            return self.render_to_response(
                self.get_context_data(error="Email yoki parol noto'g'ri")
            )

        if not user.is_verified:
            return self.render_to_response(
                self.get_context_data(
                    error="Email tasdiqlanmagan. Emailingizni tekshiring.",
                    unverified_email=email,
                )
            )

        if not user.is_active:
            return self.render_to_response(
                self.get_context_data(error="Hisobingiz faol emas")
            )

        # Django session login
        login(request, user)

        logger.info("User logged in: %s", user.email)

        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("home")


class RegisterPageView(TemplateView):
    template_name = "auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        display_name     = request.POST.get("display_name", "").strip()
        email            = request.POST.get("email", "").strip().lower()
        password         = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # Validatsiya
        if not display_name or not email or not password:
            return self.render_to_response(
                self.get_context_data(error="Barcha maydonlarni to'ldiring")
            )

        if password != password_confirm:
            return self.render_to_response(
                self.get_context_data(error="Parollar mos kelmaydi")
            )

        if len(password) < 8:
            return self.render_to_response(
                self.get_context_data(error="Parol kamida 8 ta belgidan iborat bo'lishi kerak")
            )

        if CustomUser.objects.filter(email=email).exists():
            return self.render_to_response(
                self.get_context_data(error="Bu email allaqachon ro'yxatdan o'tgan")
            )

        # Foydalanuvchi yaratish
        import uuid
        from django.conf import settings

        token = str(uuid.uuid4())
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
            verification_token=token,
            is_verified=False,
        )

        # Verification email
        verification_url = f"{settings.FRONTEND_URL}/auth/verify/{token}/"
        try:
            send_verification_email(user.email, user.display_name, verification_url)
        except Exception as e:
            logger.error("Failed to send verification email: %s", e)

        logger.info("User registered: %s", user.email)
        return redirect("auth:register_success")


class LogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("home")

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("home")


class EmailVerificationView(TemplateView):
    template_name = "auth/email_verified.html"

    def get(self, request, token, *args, **kwargs):
        try:
            user = CustomUser.objects.get(verification_token=token)
            if not user.is_verified:
                user.is_verified = True
                user.verification_token = ""
                user.save()
                login(request, user)
                logger.info("Email verified: %s", user.email)
            return self.render_to_response(self.get_context_data(success=True))
        except CustomUser.DoesNotExist:
            return self.render_to_response(self.get_context_data(success=False))


class EmailVerificationRequiredView(TemplateView):
    template_name = "auth/email_verification_required.html"


class RegisterSuccessView(TemplateView):
    template_name = "auth/register_success.html"


class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = "auth/profile.html"
    login_url = "/auth/login/"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        from watchlist.models import Watchlist
        from streaming.models import WatchHistory
        try:
            ctx["watchlist_count"] = Watchlist.objects.filter(user=self.request.user).count()
        except Exception:
            ctx["watchlist_count"] = 0
        try:
            ctx["history_count"] = WatchHistory.objects.filter(user=self.request.user).count()
        except Exception:
            ctx["history_count"] = 0
        return ctx

    def post(self, request, *args, **kwargs):
        display_name = request.POST.get("display_name", "").strip()
        if display_name:
            request.user.display_name = display_name
            request.user.save()
        return redirect("auth:profile")


class PasswordResetView(TemplateView):
    template_name = "auth/password_reset.html"

    def post(self, request, *args, **kwargs):
        from django.conf import settings
        import uuid

        email = request.POST.get("email", "").strip().lower()
        try:
            user = CustomUser.objects.get(email=email)
            token = str(uuid.uuid4())
            user.reset_token = token
            user.save()
            reset_url = f"{settings.FRONTEND_URL}/auth/password-reset-confirm/{token}/"
            send_password_reset_email(user.email, user.display_name, reset_url)
        except CustomUser.DoesNotExist:
            pass
        return redirect("auth:password_reset_done")


class PasswordResetDoneView(TemplateView):
    template_name = "auth/password_reset_done.html"


class PasswordResetConfirmView(TemplateView):
    template_name = "auth/password_reset_confirm.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["token"] = self.kwargs.get("token")
        return ctx

    def post(self, request, token, *args, **kwargs):
        password         = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if password != password_confirm:
            return self.render_to_response(
                self.get_context_data(error="Parollar mos kelmaydi", token=token)
            )
        if len(password) < 8:
            return self.render_to_response(
                self.get_context_data(error="Parol kamida 8 ta belgidan iborat bo'lishi kerak", token=token)
            )
        try:
            user = CustomUser.objects.get(reset_token=token)
            user.set_password(password)
            user.reset_token = ""
            user.save()
            login(request, user)
            return redirect("home")
        except CustomUser.DoesNotExist:
            return self.render_to_response(
                self.get_context_data(error="Havola yaroqsiz", token=token)
            )


class SubscriptionPageView(LoginRequiredMixin, TemplateView):
    template_name = "pages/subscription.html"
    login_url = "/auth/login/"

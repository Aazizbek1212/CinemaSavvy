import logging
from typing import Any
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages

from users.services import AuthService
from movies.views.pages import SeoMixin

logger = logging.getLogger(__name__)


class LoginPageView(SeoMixin, TemplateView):
    template_name = "auth/login.html"
    seo_title = "Kirish — Cinema.uz"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email    = request.POST.get("email", "").lower().strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=email, password=password)

        if user is None:
            return self.render_to_response(
                self.get_context_data(error="Email yoki parol noto'g'ri.")
            )

        if not user.is_active:
            return self.render_to_response(
                self.get_context_data(error="Hisob faolsizlantirilgan.")
            )

        if not user.is_verified:
            return self.render_to_response(
                self.get_context_data(
                    error="Email tasdiqlanmagan. Emailingizni tekshiring."
                )
            )

        # Update last login IP
        ip = self._get_ip(request)
        user.last_login_ip = ip
        user.save(update_fields=["last_login_ip"])

        login(request, user)
        logger.info("User logged in via web: %s", user.email)

        next_url = request.GET.get("next", "/")
        return redirect(next_url)

    @staticmethod
    def _get_ip(request) -> str | None:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


class RegisterPageView(SeoMixin, TemplateView):
    template_name = "auth/register.html"
    seo_title = "Ro'yxatdan o'tish — Cinema.uz"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email    = request.POST.get("email", "").lower().strip()
        password = request.POST.get("password", "")
        confirm  = request.POST.get("password_confirm", "")
        fullname = request.POST.get("full_name", "").strip()

        # Validations
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if password != confirm:
            return self.render_to_response(
                self.get_context_data(
                    error="Parollar mos kelmaydi.",
                    form_data={"email": email, "full_name": fullname},
                )
            )

        if User.objects.filter(email=email).exists():
            return self.render_to_response(
                self.get_context_data(
                    error="Bu ma'lumotlar bilan ro'yxatdan o'tib bo'lmaydi.",
                    form_data={"email": email, "full_name": fullname},
                )
            )

        try:
            AuthService.register_user(
                {"email": email, "password": password, "full_name": fullname},
                request,
            )
            return redirect("auth:register-success")
        except Exception as exc:
            logger.error("Registration error: %s", exc)
            return self.render_to_response(
                self.get_context_data(error="Ro'yxatdan o'tishda xato yuz berdi.")
            )


class LogoutView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        logger.info("User logged out: %s", request.user.email)
        logout(request)
        return redirect("home")


class ProfilePageView(LoginRequiredMixin, SeoMixin, TemplateView):
    template_name = "auth/profile.html"
    seo_title     = "Profilim — Cinema.uz"
    login_url     = "/auth/login/"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        from reviews.models import Review
        from streaming.models import WatchHistory

        ctx.update({
            "reviews_count": Review.objects.filter(
                user=self.request.user, is_active=True
            ).count(),
            "watch_count": WatchHistory.objects.filter(
                user=self.request.user, completed=True
            ).count(),
        })
        return ctx


class SubscriptionPageView(SeoMixin, TemplateView):
    template_name = "pages/subscription.html"
    seo_title     = "Premium obuna — Cinema.uz"

    PLANS = [
        {
            "name":     "Oylik",
            "price":    "29 900",
            "period":   "oy",
            "features": ["Barcha filmlar", "HD/4K sifat", "Reklama yo'q", "1 qurilma"],
            "popular":  False,
        },
        {
            "name":     "Yillik",
            "price":    "249 900",
            "period":   "yil",
            "save":     "30% tejash",
            "features": ["Barcha filmlar", "4K Ultra HD", "Reklama yo'q",
                         "3 qurilma", "Offline ko'rish"],
            "popular":  True,
        },
    ]

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["plans"] = self.PLANS
        return ctx


class EmailVerificationRequiredView(SeoMixin, TemplateView):
    template_name = "auth/email_verification_required.html"
    seo_title     = "Email tasdiqlash — Cinema.uz"

    def post(self, request, *args, **kwargs):
        """Resend verification email."""
        if request.user.is_authenticated:
            AuthService._send_verification_email(request.user, request)
            return self.render_to_response(
                self.get_context_data(resent=True)
            )
        return redirect("auth:login")


class VerifyEmailPageView(TemplateView):
    template_name = "auth/email_verified.html"

    def get(self, request, uid, token, *args, **kwargs):
        success = AuthService.verify_email(uid, token)
        return self.render_to_response(
            self.get_context_data(success=success)
        )


class PasswordResetPageView(SeoMixin, TemplateView):
    template_name = "auth/password_reset.html"
    seo_title     = "Parolni tiklash — Cinema.uz"

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").lower().strip()
        AuthService.request_password_reset(email, request)
        return self.render_to_response(
            self.get_context_data(sent=True, email=email)
        )


class PasswordResetConfirmPageView(SeoMixin, TemplateView):
    template_name = "auth/password_reset_confirm.html"
    seo_title     = "Yangi parol — Cinema.uz"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "uid":   kwargs.get("uid", self.kwargs.get("uid")),
            "token": kwargs.get("token", self.kwargs.get("token")),
        })
        return ctx

    def post(self, request, uid, token, *args, **kwargs):
        new_password = request.POST.get("new_password", "")
        confirm      = request.POST.get("new_password_confirm", "")

        if new_password != confirm:
            return self.render_to_response(
                self.get_context_data(
                    uid=uid, token=token,
                    error="Parollar mos kelmaydi."
                )
            )

        success = AuthService.confirm_password_reset(uid, token, new_password)
        if success:
            return redirect("auth:password-reset-done")

        return self.render_to_response(
            self.get_context_data(
                uid=uid, token=token,
                error="Havola noto'g'ri yoki muddati o'tgan."
            )
        )
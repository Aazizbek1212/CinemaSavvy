import logging
import secrets
from typing import Any
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from users.models import CustomUser
from users.tasks import send_password_reset_email, send_verification_email
logger = logging.getLogger(__name__)


def generate_verification_code() -> str:
    # 6 xonali raqamli tasdiqlash kodi (000 - 999).
    return f"{secrets.randbelow(1_000_000):06d}"


class LoginPageView(TemplateView):
    template_name = "auth/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Tasdiqlanmagan foydalanuvchi — kod kiritish sahifasiga
            if not request.user.is_verified:
                return redirect("auth:register")
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
            # Kontekstni yo'qotmaslik uchun sessiyaga kiritamiz va
            # kod tasdiqlash bosqichiga yo'naltiramiz.
            login(request, user)
            return redirect("auth:register")

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
    # Ro'yxatdan o'tish — bir sahifada ikki bosqich:
    # 1) forma to'ldirish; 2) emailga yuborilgan 6 xonali kodni kiritish.

    template_name = "auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        # Tasdiqlangan foydalanuvchini bosh sahifaga yuboramiz.
        if request.user.is_authenticated and request.user.is_verified:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        # `error`/`form_data`/`step`/`email` — TemplateView'ning built-in
        # kwargs'iga tushmaydi, shuning uchun qo'lda chiqarib olamiz.
        extra = {
            k: kwargs.pop(k)
            for k in ("error", "form_data", "step", "email")
            if k in kwargs
        }
        ctx = super().get_context_data(**kwargs)
        ctx.update(extra)

        # 2-bosqichda (kod tasdiqlashda) email ko'rsatish uchun.
        if self.request.user.is_authenticated:
            ctx.setdefault("step", "verify")
            ctx.setdefault("email", self.request.user.email)
        else:
            ctx.setdefault("step", "form")
        return ctx
    def post(self, request, *args, **kwargs):
        # ── 2-bosqich: kod tasdiqlash ───────────────────────────────
        if request.user.is_authenticated and request.POST.get("code") is not None:
            return self._verify_code(request)

        # ── 1-bosqich: ro'yxatdan o'tish formasi ──────────────
        return self._register(request)

    def _verify_code(self, request):
        user = request.user
        code = request.POST.get("code", "").strip()

        if len(code) != 6:
            return self.render_to_response(
                self.get_context_data(step="verify", email=user.email,
                                      error="6 xonali kodni to'liq kiriting")
            )

        if code != user.verification_token:
            return self.render_to_response(
                self.get_context_data(step="verify", email=user.email,
                                      error="Kod noto'g'ri. Qayta urinib ko'ring.")
            )

        # Kod to'g'ri — tasdiqlaymiz + 1 haftalik bepul Premium
        from datetime import timedelta
        user.is_verified = True
        user.verification_token = ""
        user.subscription_tier = CustomUser.SubscriptionTier.PREMIUM
        user.subscription_expires_at = timezone.now() + timedelta(days=7)
        user.save(update_fields=[
            "is_verified", "verification_token",
            "subscription_tier", "subscription_expires_at",
        ])

        logger.info("Email verified + 7-day premium granted: %s", user.email)
        return redirect(f"{reverse('home')}?welcome=1")

    def _register(self, request):
        # Template input nomi `full_name`; moslik uchun `display_name` ham qabul qilinadi.
        display_name     = (
            request.POST.get("full_name")
            or request.POST.get("display_name")
            or ""
        ).strip()
        email            = request.POST.get("email", "").strip().lower()
        password         = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # Xatolik holatida kiritilgan qiymatlarni qaytarish uchun
        form_data = {"full_name": display_name, "email": email}

        # Validatsiya
        if not display_name or not email or not password:
            return self.render_to_response(
                self.get_context_data(error="Barcha maydonlarni to'ldiring", form_data=form_data)
            )

        if password != password_confirm:
            return self.render_to_response(
                self.get_context_data(error="Parollar mos kelmaydi", form_data=form_data)
            )

        if len(password) < 8:
            return self.render_to_response(
                self.get_context_data(
                    error="Parol kamida 8 ta belgidan iborat bo'lishi kerak",
                    form_data=form_data,
                )
            )

        if CustomUser.objects.filter(email=email).exists():
            return self.render_to_response(
                self.get_context_data(
                    error="Bu email allaqachon ro'yxatdan o'tgan", form_data=form_data
                )
            )

        # 6 xonali raqamli tasdiqlash kodi generatsiya qilamiz
        code = generate_verification_code()
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            full_name=display_name,
            verification_token=code,
            is_verified=False,
        )

        # Tasdiqlash kodini emailga yuboramiz
        try:
            send_verification_email(user.email, user.display_name, code)
        except Exception as e:
            logger.error("Failed to send verification email: %s", e)

        logger.info("User registered (pending verification): %s", user.email)

        # Foydalanuvchini darhol tizimga kiritamiz — kod tasdiqlash shu sahifada.
        # `backend` majburiy, chunki bir nechta auth backend sozlangan.
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Bir sahifada 2-bosqichga o'tamiz (kod kiritish)
        return self.render_to_response(
            self.get_context_data(step="verify", email=user.email)
        )


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

            if not user.is_active:
                return self.render_to_response(
                    self.get_context_data(success=False, error="Hisobingiz faol emas")
                )

            if not user.is_verified:
                user.is_verified = True
                user.verification_token = ""
                user.save()
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
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
        from streaming.models import WatchHistory
        from watchlist.models import Watchlist
        # Template `reviews_count` va `watch_count` nomlarini kutadi
        # (profil statistikasi). Eski `*_count` nomlari ham saqlanadi.
        try:
            ctx["watchlist_count"] = Watchlist.objects.filter(user=self.request.user).count()
        except Exception:
            ctx["watchlist_count"] = 0
        try:
            ctx["history_count"] = WatchHistory.objects.filter(user=self.request.user).count()
        except Exception:
            ctx["history_count"] = 0
        try:
            from reviews.models import Review
            ctx["reviews_count"] = Review.objects.filter(
                user=self.request.user, is_active=True
            ).count()
        except Exception:
            ctx["reviews_count"] = 0
        ctx["watch_count"] = ctx["history_count"]
        return ctx

    def post(self, request, *args, **kwargs):
        display_name = request.POST.get("display_name", "").strip()
        if display_name:
            request.user.full_name = display_name
            request.user.save(update_fields=["full_name"])
        return redirect("auth:profile")


class PasswordResetView(TemplateView):
    template_name = "auth/password_reset.html"

    def post(self, request, *args, **kwargs):
        import uuid

        from django.conf import settings
        from django.urls import reverse

        email = request.POST.get("email", "").strip().lower()
        try:
            user = CustomUser.objects.get(email=email)
            token = str(uuid.uuid4())
            user.reset_token = token
            user.save()
            reset_path = reverse("auth:password-reset-confirm", kwargs={"token": token})
            reset_url = f"{settings.FRONTEND_URL}{reset_path}"
            send_password_reset_email(user.email, user.display_name, reset_url)
        except CustomUser.DoesNotExist:
            pass
        return redirect("auth:password-reset-done")


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

            if not user.is_active:
                return self.render_to_response(
                    self.get_context_data(error="Hisobingiz faol emas", token=token)
                )

            user.set_password(password)
            user.reset_token = ""
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
        except CustomUser.DoesNotExist:
            return self.render_to_response(
                self.get_context_data(error="Havola yaroqsiz", token=token)
            )


class SubscriptionPageView(LoginRequiredMixin, TemplateView):
    template_name = "pages/subscription.html"
    login_url = "/auth/login/"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        plans = [
            {
                "name": "Free",
                "price": "0",
                "period": "oy",
                "save": "",
                "popular": False,
                "features": [
                    "Asosiy katalogga kirish",
                    "Maqsadli cheklangan kontent",
                    "Reklamalar bilan tomosha",
                ],
            },
            {
                "name": "Premium",
                "price": "199000",
                "period": "oy",
                "save": "-20%",
                "popular": True,
                "features": [
                    "Barcha premium film va seriallar",
                    "4K/Ultra HD sifat",
                    "Reklamasiz tomosha",
                    "Offline yuklab olish",
                ],
            },
        ]

        ctx["plans"] = plans
        ctx["feature_items"] = [
            {"icon": "🎬", "title": "Keng katalog", "desc": "Yillik eng ko'p ko'rilgan filmlar va seriallar."},
            {"icon": "⚡", "title": "Tezlik", "desc": "Minimal kechikish va yuqori sifatli streaming."},
            {"icon": "🔒", "title": "Xavfsizlik", "desc": "Foydalanuvchi ma'lumotlari va hisob himoyasi."},
        ]
        ctx["faqs"] = [
            {"q": "Premium obuna qancha davom etadi?", "a": "Obuna har oy avtomatik yangilanadi. Istalgan vaqtda bekor qilishingiz mumkin."},
            {"q": "To'lov qanday amalga oshiriladi?", "a": "Texnik tayyorgarlik bosqichi davom etmoqda. Mahsulotda to'lov provayderi uchun model va webhooklar tayyorlanmoqda."},
            {"q": "Bepul rejadan Premiumga o'tish mumkinmi?", "a": "Ha, mavjud rejadan premiumga oson o'tishingiz mumkin. To'lovdan keyin imkoniyatlar darhol ochiladi."},
        ]
        ctx["is_premium"] = bool(getattr(user, "is_premium", False))
        ctx["current_plan"] = "Premium" if ctx["is_premium"] else "Free"
        ctx["subscription_expires_at"] = getattr(user, "subscription_expires_at", None)
        return ctx
import logging
from typing import Any
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from .tokens import email_verification_token, password_reset_token
from .tasks import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthService:
    """
    Single Responsibility: handles all auth business logic.
    Views are thin — they delegate here.
    """

    @staticmethod
    def register_user(validated_data: dict[str, Any], request) -> Any:
        """Create user and send verification email."""
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
            is_verified=False,
        )

        AuthService._send_verification_email(user, request)
        logger.info("User registered: %s", user.email)
        return user

    @staticmethod
    def verify_email(uid_b64: str, token: str) -> bool:
        """Verify email token — returns True on success."""
        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            logger.warning("Email verification failed: invalid uid=%s", uid_b64)
            return False

        if user.is_verified:
            return True  # already verified — idempotent

        if not email_verification_token.check_token(user, token):
            logger.warning("Email verification failed: invalid token for %s", user.email)
            return False

        user.is_verified = True
        user.save(update_fields=["is_verified"])
        logger.info("Email verified: %s", user.email)
        return True

    @staticmethod
    def get_tokens_for_user(user) -> dict[str, str]:
        """Generate JWT access + refresh token pair."""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }

    @staticmethod
    def request_password_reset(email: str, request) -> None:
        """
        Always returns success — even if email not found.
        Prevents email enumeration.
        """
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Intentionally silent
            logger.info("Password reset requested for unknown email: %s", email)
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/auth/password-reset/{uid}/{token}/"

        send_password_reset_email(
            user_email=user.email,
            user_name=user.display_name,
            reset_url=reset_url,
        )

    @staticmethod
    def confirm_password_reset(uid_b64: str, token: str, new_password: str) -> bool:
        """Validate token and set new password."""
        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return False

        if not password_reset_token.check_token(user, token):
            logger.warning("Password reset: invalid token for uid=%s", uid_b64)
            return False

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password reset successful: %s", user.email)
        return True

    @staticmethod
    def change_password(user, old_password: str, new_password: str) -> bool:
        if not user.check_password(old_password):
            return False
        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password changed: %s", user.email)
        return True

    @staticmethod
    def _send_verification_email(user, request) -> None:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{uid}/{token}/"

        send_verification_email(
            user_email=user.email,
            user_name=user.display_name,
            verification_url=verification_url,
        )
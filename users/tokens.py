import logging
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generates time-limited, single-use tokens for email verification.
    Token expires after PASSWORD_RESET_TIMEOUT seconds (default 3 days).
    """

    def _make_hash_value(self, user, timestamp: int) -> str:
        return (
            f"{user.pk}{timestamp}{user.is_verified}{user.email}"
        )


class PasswordResetTokenGeneratorExtended(PasswordResetTokenGenerator):
    """
    Extended password reset token — invalidated after password change.
    """

    def _make_hash_value(self, user, timestamp: int) -> str:
        login_timestamp = (
            user.last_login.replace(microsecond=0, tzinfo=None)
            if user.last_login
            else ""
        )
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()
password_reset_token = PasswordResetTokenGeneratorExtended()
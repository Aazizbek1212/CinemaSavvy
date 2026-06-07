import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_verification_email(
    user_email: str,
    user_name: str,
    verification_url: str,
) -> None:
    """
    Send email verification link.
    In production this should be a Celery task with @shared_task.
    """
    subject = "Cinema.uz — Emailingizni tasdiqlang"
    context = {
        "user_name": user_name,
        "verification_url": verification_url,
        "site_name": "Cinema.uz",
    }

    try:
        html_content = render_to_string("emails/verify_email.html", context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Verification email sent to: %s", user_email)

    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", user_email, exc)


def send_password_reset_email(
    user_email: str,
    user_name: str,
    reset_url: str,
) -> None:
    """Send password reset link."""
    subject = "Cinema.uz — Parolni tiklash"
    context = {
        "user_name": user_name,
        "reset_url": reset_url,
        "site_name": "Cinema.uz",
    }

    try:
        html_content = render_to_string("emails/password_reset.html", context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Password reset email sent to: %s", user_email)

    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", user_email, exc)
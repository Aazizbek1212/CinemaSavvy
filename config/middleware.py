import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)

EXEMPT_PATHS = (
    "/api/",
    "/admin/",
    "/auth/login/",
    "/auth/register/",
    "/auth/verify-email/",
    "/auth/password-reset/",
    "/static/",
    "/media/",
    "/favicon.ico",
)


class EmailVerificationMiddleware:
    """
    Redirect unverified users to a reminder page.
    Exempt: API, admin, auth pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.user.is_verified
            and not any(request.path.startswith(p) for p in EXEMPT_PATHS)
        ):
            logger.info(
                "Unverified user blocked: %s → %s",
                request.user.email, request.path,
            )
            return redirect(reverse("auth:email-verification-required"))

        return self.get_response(request)
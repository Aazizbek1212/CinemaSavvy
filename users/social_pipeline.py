from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from social_core.exceptions import AuthForbidden

User = get_user_model()


def create_or_update_social_user(
    strategy: Any = None,
    backend: Any = None,
    user: User | None = None,
    details: dict[str, Any] | None = None,
    response: dict[str, Any] | None = None,
    uid: str | None = None,
    is_new: bool = False,
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """Create or update a local user from Google OAuth details.

    This keeps the custom email-based auth model working with social-auth.
    """
    email = (details or {}).get("email")
    if not email:
        return None

    full_name = (
        (details or {}).get("fullname")
        or (details or {}).get("name")
        or ""
    ).strip()

    existing_user = User.objects.filter(email=email).first()
    if existing_user is not None:
        if not existing_user.is_active:
            raise AuthForbidden(backend)

        updated = False
        if full_name and not existing_user.full_name:
            existing_user.full_name = full_name
            updated = True
        if not existing_user.is_verified:
            existing_user.is_verified = True
            updated = True
        if updated:
            existing_user.save(update_fields=["full_name", "is_verified"])
        return {"user": existing_user, "is_new": False}

    new_user = User.objects.create_user(
        email=email,
        password=None,
        full_name=full_name,
        is_verified=True,
    )
    return {"user": new_user, "is_new": True}
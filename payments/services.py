import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import PaymentTransaction

PREMIUM_MONTHLY_AMOUNT = Decimal("199000")


def create_payment(user, provider=None, plan="premium"):
    if plan != "premium":
        raise ValueError("Unsupported payment plan")

    selected_provider = provider or settings.PAYMENT_PROVIDER
    return PaymentTransaction.objects.create(
        user=user,
        provider=selected_provider,
        plan=plan,
        amount=PREMIUM_MONTHLY_AMOUNT,
        currency="UZS",
    )


def verify_webhook_signature(raw_body: bytes, signature: str | None) -> bool:
    secret = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@transaction.atomic
def apply_successful_payment(payment_id, payload):
    payment = PaymentTransaction.objects.select_for_update().select_related("user").get(
        id=payment_id
    )
    if payment.status != PaymentTransaction.Status.PAID:
        payment.mark_paid(payload)
        expires_at = timezone.now() + timedelta(days=30)
        if payment.user.is_premium and payment.user.subscription_expires_at:
            expires_at = payment.user.subscription_expires_at + timedelta(days=30)
        payment.user.upgrade_to_premium(expires_at)
    return payment


def parse_webhook_body(raw_body: bytes):
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid webhook payload") from exc

    payment_id = payload.get("payment_id")
    status = payload.get("status")
    if not payment_id or status not in {"paid", "succeeded"}:
        raise ValueError("Incomplete successful payment payload")
    return payment_id, payload

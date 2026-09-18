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


def build_click_checkout_url(payment) -> str:
    # Click checkout sahifasiga yo'naltiruvchi URL yasaydi.
    # Foydalanuvchi shu havolaga o'tadi va Click'da to'lov qiladi.
    # merchant_trans_id — bizning PaymentTransaction.id.
    from urllib.parse import urlencode
    base = getattr(settings, "CLICK_CHECKOUT_URL", "https://my.click.uz/services/pay")
    params = {
        "service_id": getattr(settings, "CLICK_SERVICE_ID", ""),
        "merchant_id": getattr(settings, "CLICK_MERCHANT_ID", ""),
        "amount": str(payment.amount),
        "transaction_param": str(payment.id),  # merchant_trans_id
        "return_url": f"{settings.FRONTEND_URL}/auth/subscription/status/{payment.id}/",
    }
    return f"{base}?{urlencode(params)}"


def grant_premium_for_payment(payment, days: int = 30) -> None:
    # To'langan tranzaksiya uchun premium beradi (atomik).
    # Agar foydalanuvchining premium'i hali tugamagan bo'lsa —
    # mavjud muddat ustiga qo'shiladi.
    user = payment.user
    now = timezone.now()
    if user.is_premium and user.subscription_expires_at and user.subscription_expires_at > now:
        expires_at = user.subscription_expires_at + timedelta(days=days)
    else:
        expires_at = now + timedelta(days=days)
    user.upgrade_to_premium(expires_at)


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
        grant_premium_for_payment(payment)
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

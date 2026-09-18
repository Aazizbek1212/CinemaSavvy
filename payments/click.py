"""Click.uz to'lov tizimi integratsiyasi.

Click protokoli (My.click.uz / Shop API):
  - Click bizning webhook'imizga POST yuboradi (form-encoded).
  - action=0 → Prepare (tranzaksiyani tekshirish)
  - action=1 → Complete (to'lovni yakunlash)
  - Javob HAR DOIM HTTP 200 bo'lishi va JSON bilan qaytishi kerak.

Imzo formulasi (standart):
  Prepare  (action=0):
    md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time)
  Complete (action=1):
    md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + merchant_prepare_id + amount + action + sign_time)

  ⚠️ Har bir merchant kabinetida formula bir xil bo'lishi kerak, lekin
  SHARTNOMANGIZDA ko'rsatilganini tekshiring (docs.click.uz).
"""

import hashlib
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import PaymentTransaction

logger = logging.getLogger(__name__)


# Click xato kodlari (error_note bilan birga qaytadi)
class ClickError:
    SUCCESS = 0
    SIGN_CHECK_FAILED = -1
    INCORRECT_AMOUNT = -2
    ACTION_NOT_FOUND = -3
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5
    TRANSACTION_NOT_FOUND = -6
    # -7, -8, -9 Click tomonidan band qilingan
    ORDER_NOT_FOUND = -5


def _to_str(value) -> str:
    if value is None:
        return ""
    return str(value)


def verify_sign(data: dict, action: str) -> bool:
    """Click'dan kelgan sign_string'ni tekshiradi.

    action: "0" (Prepare) yoki "1" (Complete)
    """
    secret_key = getattr(settings, "CLICK_SECRET_KEY", "")
    if not secret_key:
        logger.error("CLICK_SECRET_KEY sozlanmagan")
        return False

    click_trans_id = _to_str(data.get("click_trans_id"))
    service_id = _to_str(data.get("service_id"))
    merchant_trans_id = _to_str(data.get("merchant_trans_id"))
    amount = _to_str(data.get("amount"))
    sign_time = _to_str(data.get("sign_time"))
    incoming_sign = _to_str(data.get("sign_string"))

    if action == "1":
        merchant_prepare_id = _to_str(data.get("merchant_prepare_id"))
        raw = (
            f"{click_trans_id}{service_id}{secret_key}"
            f"{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
        )
    else:
        raw = (
            f"{click_trans_id}{service_id}{secret_key}"
            f"{merchant_trans_id}{amount}{action}{sign_time}"
        )

    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    is_valid = expected == incoming_sign
    if not is_valid:
        logger.warning(
            "Click sign mos emas. expected=%s got=%s (raw=%s)",
            expected, incoming_sign, raw,
        )
    return is_valid


def parse_amount(value) -> Decimal | None:
    try:
        return Decimal(_to_str(value))
    except (InvalidOperation, TypeError):
        return None


@transaction.atomic
def handle_prepare(data: dict) -> dict:
    """action=0 — tranzaksiyani tekshirish."""
    merchant_trans_id = _to_str(data.get("merchant_trans_id"))
    click_trans_id = _to_str(data.get("click_trans_id"))
    click_paydoc_id = _to_str(data.get("click_paydoc_id"))
    amount = parse_amount(data.get("amount"))

    if amount is None:
        return _err(ClickError.INCORRECT_AMOUNT, "Amount xato", data)

    # merchant_trans_id — bizning PaymentTransaction.id
    try:
        payment = PaymentTransaction.objects.select_for_update().select_related("user").get(
            id=merchant_trans_id
        )
    except (PaymentTransaction.DoesNotExist, ValueError):
        return _err(ClickError.ORDER_NOT_FOUND, "Tranzaksiya topilmadi", data)

    if payment.status == PaymentTransaction.Status.PAID:
        return _err(ClickError.ALREADY_PAID, "Allaqachon to'langan", data)

    # Summani tekshiramiz (Click tiyin emas, so'mda yuboradi)
    if amount != payment.amount:
        return _err(ClickError.INCORRECT_AMOUNT, "Summa mos emas", data)

    # Click maydonlarini saqlaymiz
    payment.click_trans_id = click_trans_id
    payment.click_paydoc_id = click_paydoc_id
    payment.provider = "click"
    payment.raw_payload = dict(data)
    payment.save(update_fields=[
        "click_trans_id", "click_paydoc_id", "provider", "raw_payload", "updated_at",
    ])

    # merchant_prepare_id — keyingi Complete'da qaytaramiz (PaymentTransaction.id)
    return {
        "error": ClickError.SUCCESS,
        "error_note": "Success",
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": str(payment.id),
    }


@transaction.atomic
def handle_complete(data: dict) -> dict:
    """action=1 — to'lovni yakunlash."""
    merchant_trans_id = _to_str(data.get("merchant_trans_id"))
    click_trans_id = _to_str(data.get("click_trans_id"))
    click_paydoc_id = _to_str(data.get("click_paydoc_id"))
    amount = parse_amount(data.get("amount"))
    # Click xatoni error<0 bilan yuboradi (masalan -1 bekor qilindi)
    try:
        click_error = int(data.get("error", 0))
    except (TypeError, ValueError):
        click_error = 0

    if amount is None:
        return _err(ClickError.INCORRECT_AMOUNT, "Amount xato", data)

    try:
        payment = PaymentTransaction.objects.select_for_update().select_related("user").get(
            id=merchant_trans_id
        )
    except (PaymentTransaction.DoesNotExist, ValueError):
        return _err(ClickError.ORDER_NOT_FOUND, "Tranzaksiya topilmadi", data)

    # Click tomonidan bekor qilingan bo'lsa
    if click_error < 0:
        payment.status = PaymentTransaction.Status.CANCELED
        payment.raw_payload = dict(data)
        payment.save(update_fields=["status", "raw_payload", "updated_at"])
        return {
            "error": click_error,
            "error_note": _to_str(data.get("error_note")) or "Transaction canceled",
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": str(payment.id),
        }

    if payment.status == PaymentTransaction.Status.PAID:
        # Idempotent: allaqachon to'langan — yana premium qo'shmaymiz
        return {
            "error": ClickError.SUCCESS,
            "error_note": "Already paid",
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": str(payment.id),
        }

    if amount != payment.amount:
        return _err(ClickError.INCORRECT_AMOUNT, "Summa mos emas", data)

    # To'lovni tasdiqlaymiz + premium beramiz
    payment.click_trans_id = click_trans_id
    payment.click_paydoc_id = click_paydoc_id
    payment.provider = "click"
    payment.raw_payload = dict(data)
    payment.mark_paid(payload=dict(data))

    from .services import grant_premium_for_payment
    grant_premium_for_payment(payment)

    logger.info("Click to'lov yakunlandi: %s (user=%s)", payment.id, payment.user_id)

    return {
        "error": ClickError.SUCCESS,
        "error_note": "Success",
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_confirm_id": str(payment.id),
    }


def _err(code: int, note: str, data: dict) -> dict:
    """Xato javobi (Click formati)."""
    return {
        "error": code,
        "error_note": note,
        "click_trans_id": _to_str(data.get("click_trans_id")),
        "merchant_trans_id": _to_str(data.get("merchant_trans_id")),
    }

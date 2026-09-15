import hashlib
import hmac
import json
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import CustomUser

from .models import PaymentTransaction


@override_settings(PAYMENT_WEBHOOK_SECRET="test-webhook-secret")
class PaymentWebhookTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="payer@example.com",
            password="StrongPass123!",
            is_verified=True,
        )
        self.payment = PaymentTransaction.objects.create(
            user=self.user,
            provider="test",
            amount="199000",
            currency="UZS",
        )
        self.client = APIClient()

    def _post_webhook(self, payload, signature=None):
        body = json.dumps(payload).encode("utf-8")
        signature = signature or hmac.new(
            b"test-webhook-secret", body, hashlib.sha256
        ).hexdigest()
        return self.client.post(
            reverse("payments:webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_PAYMENT_SIGNATURE=signature,
        )

    def test_invalid_signature_is_rejected(self):
        response = self._post_webhook(
            {"payment_id": str(self.payment.id), "status": "paid"},
            signature="invalid",
        )

        self.assertEqual(response.status_code, 401)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentTransaction.Status.PENDING)

    def test_successful_webhook_is_idempotent(self):
        payload = {"payment_id": str(self.payment.id), "status": "paid"}

        first = self._post_webhook(payload)
        self.payment.refresh_from_db()
        self.user.refresh_from_db()
        first_expiry = self.user.subscription_expires_at

        second = self._post_webhook(payload)
        self.user.refresh_from_db()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(self.payment.status, PaymentTransaction.Status.PAID)
        self.assertEqual(self.user.subscription_tier, CustomUser.SubscriptionTier.PREMIUM)
        self.assertEqual(self.user.subscription_expires_at, first_expiry)
        self.assertGreater(first_expiry, timezone.now() + timedelta(days=29))

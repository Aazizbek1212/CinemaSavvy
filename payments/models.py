import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_transactions",
    )
    provider = models.CharField(max_length=32, default="manual")
    external_id = models.CharField(max_length=255, blank=True, default="")
    plan = models.CharField(max_length=32, default="premium")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    # ─── Click.uz maydonlari ─────────────────
    # Click tizimidagi tranzaksiya raqamlari (webhook orqali keladi)
    click_trans_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    click_paydoc_id = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                condition=~models.Q(external_id=""),
                name="unique_payment_provider_external_id",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["provider", "status"]),
        ]

    def mark_paid(self, payload=None):
        self.status = self.Status.PAID
        self.paid_at = self.paid_at or timezone.now()
        if payload is not None:
            self.raw_payload = payload
        self.save(update_fields=["status", "paid_at", "raw_payload", "updated_at"])

    def __str__(self):
        return f"{self.provider}:{self.id} ({self.status})"
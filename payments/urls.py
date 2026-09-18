from django.urls import path
from .views import (
    ClickCompleteView,
    ClickPrepareView,
    CreatePaymentView,
    PaymentStatusView,
    PaymentWebhookView,
)

app_name = "payments"

urlpatterns = [
    # Tranzaksiya yaratish (frontend chaqiradi)
    path("create/", CreatePaymentView.as_view(), name="create"),

    # Click.uz webhook'lari (Click serveri chaqiradi)
    # ⚠️ Click kabinetida aynan shu URL'larni ko'rsating.
    path("click/prepare/", ClickPrepareView.as_view(), name="click-prepare"),
    path("click/complete/", ClickCompleteView.as_view(), name="click-complete"),

    # Umumiy webhook (Stripe/manual uchun, eski)
    path("webhook/", PaymentWebhookView.as_view(), name="webhook"),

    # To'lov holati sahifasi
    path("status/<uuid:payment_id>/", PaymentStatusView.as_view(), name="status"),
]

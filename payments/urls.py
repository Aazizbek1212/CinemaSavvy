from django.urls import path

from .views import CreatePaymentView, PaymentWebhookView

app_name = "payments"

urlpatterns = [
    path("create/", CreatePaymentView.as_view(), name="create"),
    path("webhook/", PaymentWebhookView.as_view(), name="webhook"),
]

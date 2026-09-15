import json

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction
from .services import (
    apply_successful_payment,
    create_payment,
    parse_webhook_body,
    verify_webhook_signature,
)


class CreatePaymentView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            payment = create_payment(
                user=request.user,
                provider=request.data.get("provider"),
                plan=request.data.get("plan", "premium"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "payment_id": str(payment.id),
                "provider": payment.provider,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentWebhookView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        signature = request.headers.get("X-Payment-Signature")
        if not verify_webhook_signature(request.body, signature):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payment_id, payload = parse_webhook_body(request.body)
            payment = apply_successful_payment(payment_id, payload)
        except (ValueError, PaymentTransaction.DoesNotExist):
            return Response({"detail": "Invalid payment webhook."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"payment_id": str(payment.id), "status": payment.status})

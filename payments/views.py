import json
import logging
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from . import click as click_api
from .models import PaymentTransaction
from .services import (
    apply_successful_payment,
    build_click_checkout_url,
    create_payment,
    parse_webhook_body,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)


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

        checkout_url = ""
        if payment.provider == "click":
            checkout_url = build_click_checkout_url(payment)

        return Response(
            {
                "payment_id": str(payment.id),
                "provider": payment.provider,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
                "checkout_url": checkout_url,
            },
            status=status.HTTP_201_CREATED,
        )

class ClickPrepareView(View):
    # Click Prepare webhook (action=0).
    # Click bu yerga POST yuboradi; biz HAR DOIM 200 + JSON qaytaramiz.

    def post(self, request):
        data = request.POST.dict()
        logger.info("Click PREPARE: %s", {k: data.get(k) for k in (
            "click_trans_id", "merchant_trans_id", "amount", "action",
        )})

        if not click_api.verify_sign(data, action="0"):
            return JsonResponse({
                "error": click_api.ClickError.SIGN_CHECK_FAILED,
                "error_note": "SIGN CHECK FAILED!",
                "click_trans_id": data.get("click_trans_id", ""),
                "merchant_trans_id": data.get("merchant_trans_id", ""),
            })

        result = click_api.handle_prepare(data)
        return JsonResponse(result)

class ClickCompleteView(View):
    # Click Complete webhook (action=1).

    def post(self, request):
        data = request.POST.dict()
        logger.info("Click COMPLETE: %s", {k: data.get(k) for k in (
            "click_trans_id", "merchant_trans_id", "merchant_prepare_id", "amount", "error",
        )})

        if not click_api.verify_sign(data, action="1"):
            return JsonResponse({
                "error": click_api.ClickError.SIGN_CHECK_FAILED,
                "error_note": "SIGN CHECK FAILED!",
                "click_trans_id": data.get("click_trans_id", ""),
                "merchant_trans_id": data.get("merchant_trans_id", ""),
            })

        result = click_api.handle_complete(data)
        return JsonResponse(result)

class PaymentStatusView(View):
    # To'lovdan keyin foydalanuvchi ko'radigan holat sahifasi.

    def get(self, request, payment_id):
        payment = get_object_or_404(
            PaymentTransaction, id=payment_id, user=request.user
        )
        return render(request, "pages/payment_status.html", {"payment": payment})


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

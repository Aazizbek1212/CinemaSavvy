from django.contrib import admin, messages
from django.utils import timezone
from .models import PaymentTransaction
@admin.action(description="✅ Tanlangan to'lovlarni tasdiqlash (premium berish)")
def mark_as_paid(modeladmin, request, queryset):
    from .services import grant_premium_for_payment
    granted = 0
    for payment in queryset:
        if payment.status != PaymentTransaction.Status.PAID:
            payment.mark_paid(payload={"manual": True, "by": request.user.email})
            grant_premium_for_payment(payment)
            granted += 1
    modeladmin.message_user(
        request, f"{granted} ta to'lov tasdiqlandi va premium berildi.", messages.SUCCESS
    )

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "provider",
        "amount",
        "currency",
        "status",
        "created_at",
        "paid_at",
    )
    list_filter = ("provider", "status", "currency")
    search_fields = ("user__email", "external_id", "click_trans_id")
    readonly_fields = (
        "id", "created_at", "updated_at", "paid_at",
        "click_trans_id", "click_paydoc_id",
    )
    actions = [mark_as_paid]
    date_hierarchy = "created_at"
    list_per_page = 50

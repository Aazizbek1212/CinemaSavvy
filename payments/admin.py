from django.contrib import admin

from .models import PaymentTransaction


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
    search_fields = ("user__email", "external_id")
    readonly_fields = ("id", "created_at", "updated_at", "paid_at")

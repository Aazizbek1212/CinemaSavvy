from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "full_name", "is_verified", "subscription_tier", "is_premium", "is_active", "date_joined")
    list_filter = ("is_active", "is_verified", "is_staff", "subscription_tier")
    search_fields = ("email", "full_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login", "last_login_ip")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (_("Personal info"), {"fields": ("full_name", "avatar", "bio")}),
        (_("Subscription"), {"fields": ("subscription_tier", "subscription_expires_at")}),
        (_("Permissions"), {"fields": ("is_active", "is_verified", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("date_joined", "last_login", "last_login_ip")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "is_staff", "is_verified"),
        }),
    )
from django.contrib import admin
from .models import Review, ReviewLike


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "rating", "like_count", "is_active", "created_at")
    list_filter = ("is_active", "rating")
    search_fields = ("user__email", "movie__title")
    readonly_fields = ("like_count", "created_at", "updated_at")
    actions = ["soft_delete_reviews"]

    def soft_delete_reviews(self, request, queryset):
        for review in queryset:
            review.soft_delete()
        self.message_user(request, f"{queryset.count()} ta review o'chirildi.")
    soft_delete_reviews.short_description = "Tanlangan review'larni o'chirish"


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "review", "created_at")
    readonly_fields = ("created_at",)
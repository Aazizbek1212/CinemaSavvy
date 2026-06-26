from django.contrib import admin
from .models import Watchlist


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "movie",
        "created_at",
    )

    search_fields = (
        "user__email",
        "movie__title",
    )

    autocomplete_fields = (
        "user",
        "movie",
    )

    ordering = (
        "-created_at",
    )
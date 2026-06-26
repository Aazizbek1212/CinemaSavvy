from django.contrib import admin
from .models import Collection, CollectionMovie


class CollectionMovieInline(admin.TabularInline):
    model = CollectionMovie
    extra = 1
    autocomplete_fields = ("movie",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_featured",
        "created_at",
    )

    list_filter = (
        "is_featured",
    )

    search_fields = (
        "title",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }

    inlines = [
        CollectionMovieInline
    ]
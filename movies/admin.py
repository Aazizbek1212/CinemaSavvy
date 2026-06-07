from django.contrib import admin
from django.utils.html import format_html
from .models import Genre, Person, Language, Movie, MovieCast, MovieFile, Subtitle


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "birth_date", "birth_place")
    list_filter = ("role",)
    search_fields = ("full_name",)
    prepopulated_fields = {"slug": ("full_name",)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 1
    autocomplete_fields = ("person",)


class MovieFileInline(admin.TabularInline):
    model = MovieFile
    extra = 0
    readonly_fields = ("status", "file_size_bytes", "duration_seconds")


class SubtitleInline(admin.TabularInline):
    model = Subtitle
    extra = 0


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title", "release_year", "status",
        "is_premium", "average_rating",
        "rating_count", "view_count", "poster_preview",
    )
    list_filter = ("status", "is_premium", "age_rating", "release_year")
    search_fields = ("title", "title_original", "slug")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("genres", "languages")
    readonly_fields = ("average_rating", "rating_count", "view_count", "published_at")
    inlines = [MovieCastInline, MovieFileInline, SubtitleInline]
    list_per_page = 25

    fieldsets = (
        ("Asosiy", {"fields": ("title", "title_original", "slug", "tagline", "description")}),
        ("Media", {"fields": ("poster", "backdrop", "trailer_url")}),
        ("Tasnif", {"fields": ("genres", "primary_language", "languages", "country", "age_rating")}),
        ("Detallar", {"fields": ("release_year", "duration_minutes", "is_premium", "status")}),
        ("Statistika", {"fields": ("average_rating", "rating_count", "view_count", "published_at")}),
    )

    def poster_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" height="40" />', obj.poster.url)
        return "—"
    poster_preview.short_description = "Poster"
import logging
from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView, ListView
from django.utils.functional import cached_property

from movies.models import Movie, Genre, Language, Person
from streaming.services import WatchHistoryService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Mixins
# ─────────────────────────────────────────────

class SeoMixin:
    """
    Inject SEO meta tags into context.
    Override get_seo() in subclass.
    """
    seo_title:       str = "Cinema.uz"
    seo_description: str = "O'zbekistonning eng yaxshi kino platformasi"
    seo_image:       str = ""

    def get_seo(self) -> dict[str, str]:
        return {
            "seo_title":       self.seo_title,
            "seo_description": self.seo_description,
            "seo_image":       self.seo_image,
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.get_seo())
        return ctx


class PremiumRequiredMixin(LoginRequiredMixin):
    """
    Requires authenticated + premium user.
    Non-premium users redirected to subscription page.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_premium:
            from django.shortcuts import redirect
            return redirect("auth:subscription")
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────

class HomePageView(SeoMixin, TemplateView):
    template_name = "pages/home.html"
    seo_title = "Cinema.uz — O'zbek va xorijiy filmlar"
    seo_description = "O'zbekistonning eng yaxshi kino platformasi. HD sifatda tomosha qiling."

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        base_qs = Movie.objects.published().with_relations()

        ctx.update({
            "featured_movie": (
                base_qs
                .filter(backdrop__isnull=False)
                .order_by("-view_count", "-average_rating")
                .first()
            ),
            "new_movies": list(
                base_qs.order_by("-published_at")[:18]
            ),
            "top_movies": list(
                base_qs.top_rated()[:18]
            ),
            "uzbek_movies": list(
                base_qs.filter(
                    languages__code="uz"
                ).distinct().order_by("-published_at")[:18]
            ),
            "genres": Genre.objects.all()[:12],
        })
        return ctx


# ─────────────────────────────────────────────
# Catalog
# ─────────────────────────────────────────────

class CatalogPageView(SeoMixin, TemplateView):
    template_name  = "pages/catalog.html"
    seo_title      = "Filmlar katalogi — Cinema.uz"
    paginate_by    = 24

    def get_template_names(self) -> list[str]:
        # HTMX so'rovi bo'lsa faqat grid partial'ini qaytaramiz (to'liq sahifa emas)
        if self.request.headers.get("HX-Request"):
            return ["partials/movies_grid.html"]
        return [self.template_name]

    ALLOWED_ORDERINGS = {
        "-published_at":    "Yangiligi",
        "-average_rating":  "Reytingi",
        "-view_count":      "Ko'rishlar",
        "release_year":     "Yili (eski)",
        "-release_year":    "Yili (yangi)",
    }

    def get_queryset(self) -> QuerySet:
        qs = Movie.objects.published().with_relations()
        p  = self.request.GET

        if genre := p.get("genre"):
            qs = qs.filter(genres__slug=genre)

        if language := p.get("language"):
            qs = qs.filter(languages__code=language)

        if country := p.get("country"):
            qs = qs.filter(country__icontains=country)

        if year_min := p.get("year_min"):
            qs = qs.filter(release_year__gte=year_min)

        if year_max := p.get("year_max"):
            qs = qs.filter(release_year__lte=year_max)

        if rating_min := p.get("rating_min"):
            qs = qs.filter(average_rating__gte=rating_min)

        if is_premium := p.get("is_premium"):
            qs = qs.filter(is_premium=is_premium == "true")

        if age_rating := p.get("age_rating"):
            qs = qs.filter(age_rating=age_rating)

        if search := p.get("q"):
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(title_original__icontains=search) |
                Q(cast__full_name__icontains=search)
            ).distinct()

        ordering = p.get("ordering", "-published_at")
        if ordering not in self.ALLOWED_ORDERINGS:
            ordering = "-published_at"

        return qs.order_by(ordering)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx  = super().get_context_data(**kwargs)
        qs   = self.get_queryset()
        page = self.request.GET.get("page", 1)

        paginator = Paginator(qs, self.paginate_by)
        try:
            movies = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            movies = paginator.page(1)

        # Active filters for UI
        p = self.request.GET
        ctx.update({
            "movies":            movies,
            "total_count":       paginator.count,
            "genres":            Genre.objects.all(),
            "languages":         Language.objects.all(),
            "orderings":         self.ALLOWED_ORDERINGS,
            "selected_genre":    p.get("genre", ""),
            "selected_language": p.get("language", ""),
            "selected_ordering": p.get("ordering", "-published_at"),
            "year_min":          p.get("year_min", ""),
            "year_max":          p.get("year_max", ""),
            "rating_min":        p.get("rating_min", ""),
            "search_query":      p.get("q", ""),
            "is_premium_filter": p.get("is_premium", ""),
        })
        return ctx


# ─────────────────────────────────────────────
# Movie Detail
# ─────────────────────────────────────────────

class MovieReviewsPartialView(ListView):
    """movie_detail sahifasidagi HTMX uchun sharhlar ro'yxatini HTML partial qaytaradi."""
    template_name = "partials/review_list.html"
    context_object_name = "reviews"

    def get_queryset(self) -> QuerySet:
        from reviews.models import Review
        movie = get_object_or_404(Movie, slug=self.kwargs["slug"])
        return (
            Review.objects.active()
            .with_relations()
            .filter(movie=movie)
            .order_by("-created_at")
        )


class MovieDetailPageView(SeoMixin, DetailView):
    template_name   = "pages/movie_detail.html"
    model           = Movie
    slug_field      = "slug"
    context_object_name = "movie"

    def get_queryset(self) -> QuerySet:
        return Movie.objects.published().with_relations()

    def get_seo(self) -> dict[str, str]:
        movie = self.get_object()
        return {
            "seo_title":       f"{movie.title} ({movie.release_year}) — Cinema.uz",
            "seo_description": (movie.description[:155] + "...") if movie.description else "",
            "seo_image":       movie.poster.url if movie.poster else "",
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx   = super().get_context_data(**kwargs)
        movie = self.object

        available_files = movie.video_files.filter(status="ready").select_related("language")

        languages = []
        seen = set()
        for f in available_files:
            if f.language and f.language.code not in seen:
                languages.append(f.language)
                seen.add(f.language.code)

        default_lang = (
            movie.primary_language.code if movie.primary_language
            else (languages[0].code if languages else "")
        )

        # Birinchi mavjud fayldan video_url olish
        first_file = available_files.first()
        video_url = f"/media/{first_file.file_key}" if first_file else ""

        ctx.update({
            "available_files":     available_files,
            "available_languages": languages,
            "default_lang":        default_lang,
            "resume_position":     WatchHistoryService.get_resume_position(
                self.request.user, movie
            ),
            "subtitles":       movie.subtitles.select_related("language").all(),
            "youtube_url":     movie.youtube_url,
            "video_url":       video_url if not movie.youtube_url else "",
            "youtube_embed_id": movie.youtube_url.split("v=")[-1].split("&")[0] if movie.youtube_url and "v=" in movie.youtube_url else "",
        })
        return ctx


# ─────────────────────────────────────────────
# Watch
# ─────────────────────────────────────────────

class WatchPageView(LoginRequiredMixin, SeoMixin, DetailView):
    template_name       = "pages/watch.html"
    model               = Movie
    slug_field          = "slug"
    context_object_name = "movie"
    login_url           = "/auth/login/"

    def get_queryset(self) -> QuerySet:
        return Movie.objects.published()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        movie = self.get_object()

        # Premium check
        if movie.is_premium and not request.user.is_premium:
            from django.shortcuts import redirect
            return redirect("auth:subscription")

        return response

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx   = super().get_context_data(**kwargs)
        movie = self.object

        # Barcha tayyor fayllar
        available_files = movie.video_files.filter(status="ready").select_related("language")
        
        # Tillar ro'yxati (takrorsiz)
        languages = []
        seen = set()
        for f in available_files:
            if f.language and f.language.code not in seen:
                languages.append(f.language)
                seen.add(f.language.code)

        # Default til — birinchi mavjud til yoki primary_language
        default_lang = (
            movie.primary_language.code if movie.primary_language 
            else (languages[0].code if languages else "")
        )

        ctx.update({
            "available_files": available_files,
            "available_languages": languages,
            "default_lang": default_lang,
            "resume_position": WatchHistoryService.get_resume_position(
                self.request.user, movie
            ),
            "subtitles": movie.subtitles.select_related("language").all(),
            "youtube_url": movie.youtube_url,
            "video_url": f"/media/videos/{movie.slug}.mp4" if not movie.youtube_url else "",
            "youtube_embed_id": movie.youtube_url.split("v=")[-1].split("&")[0] if movie.youtube_url and "v=" in movie.youtube_url else "",
        })
        return ctx
from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)


# ─────────────────────────────────────────────
# Person Detail
# ─────────────────────────────────────────────

class PersonDetailPageView(SeoMixin, DetailView):
    template_name       = "pages/person_detail.html"
    model               = Person
    slug_field          = "slug"
    context_object_name = "person"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx    = super().get_context_data(**kwargs)
        person = self.object

        movies = (
            Movie.objects.published()
            .filter(cast=person)
            .with_relations()
            .order_by("-release_year")
        )
        ctx["person_movies"] = movies
        return ctx


# ─────────────────────────────────────────────
# Search (HTMX partial)
# ─────────────────────────────────────────────

class SearchView(TemplateView):
    """
    HTMX partial — returns movie cards fragment.
    GET /search/?q=...
    """
    template_name = "partials/search_results.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx   = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()

        results = []
        if len(query) >= 2:
            from django.db.models import Q
            results = (
                Movie.objects.published()
                .filter(
                    Q(title__icontains=query) |
                    Q(title_original__icontains=query)
                )
                .with_relations()
                .order_by("-average_rating")[:8]
            )

        ctx.update({
            "results": results,
            "query":   query,
        })
        return ctx

FEATURE_ITEMS = [
    {"icon": "🎬", "title": "Barcha filmlar",
     "desc": "10,000+ film va serialga cheksiz kirish"},
    {"icon": "📺", "title": "4K Ultra HD",
     "desc": "Eng yuqori sifatda tomosha qiling"},
    {"icon": "🚫", "title": "Reklama yo'q",
     "desc": "Hech qanday reklama, to'liq zavq"},
    {"icon": "📱", "title": "Ko'p qurilma",
     "desc": "Telefon, planshet, TV da bir vaqtda"},
    {"icon": "⬇️", "title": "Offline ko'rish",
     "desc": "Internetisiz ham tomosha qiling"},
    {"icon": "🇺🇿", "title": "O'zbek kontent",
     "desc": "Eksklyuziv mahalliy filmlar"},
]

FAQS = [
    {"q": "Bekor qilish mumkinmi?",
     "a": "Ha, istalgan vaqtda bekor qilishingiz mumkin. Hech qanday jarima yo'q."},
    {"q": "Bepul sinab ko'rish qanday ishlaydi?",
     "a": "7 kun davomida barcha premium funksiyalardan bepul foydalanasiz. "
          "Karta ma'lumotlari kerak emas."},
    {"q": "Necta qurilmada ishlatsa bo'ladi?",
     "a": "Oylik obunada 1 ta, Yillik obunada 3 ta qurilmada bir vaqtda."},
    {"q": "To'lov qanday amalga oshiriladi?",
     "a": "Payme, Click va Uzcard orqali to'lashingiz mumkin."},
]

def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    ctx["plans"]         = self.PLANS
    ctx["feature_items"] = self.FEATURE_ITEMS
    ctx["faqs"]          = self.FAQS
    return ctx


# ─────────────────────────────────────────────
# Watch History
# ─────────────────────────────────────────────

class WatchHistoryPageView(LoginRequiredMixin, SeoMixin, TemplateView):
    template_name = "pages/watch_history.html"
    seo_title     = "Ko'rish tarixi — Cinema.uz"
    login_url     = "/auth/login/"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        from streaming.models import WatchHistory

        history = (
            WatchHistory.objects
            .filter(user=self.request.user)
            .select_related("movie")
            .order_by("-updated_at")
        )

        paginator = Paginator(history, 20)
        page = self.request.GET.get("page", 1)
        try:
            history_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            history_page = paginator.page(1)

        ctx["history"] = history_page
        return ctx
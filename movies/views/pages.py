import logging
from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView, ListView

from movies.models import Movie, Genre, Language, Person
from streaming.services import WatchHistoryService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Mixins
# ─────────────────────────────────────────────

class SeoMixin:
    seo_title:       str = "CinemaSavvy"
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
    seo_title = "CinemaSavvy — O'zbek va xorijiy filmlar"
    seo_description = "O'zbekistonning eng yaxshi kino platformasi. HD sifatda tomosha qiling."

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        base_qs = Movie.objects.published().with_relations()

        ctx.update({
            "new_movies":     base_qs.order_by("-published_at")[:12],
            "top_movies":     base_qs.order_by("-average_rating")[:12],
            "genres":         Genre.objects.all()[:20],
            "uzbek_movies":   base_qs.filter(primary_language__code="uz").order_by("-published_at")[:8],
            "turkish_movies": base_qs.filter(primary_language__code="tr").order_by("-published_at")[:8],
            "korean_movies":  base_qs.filter(primary_language__code="ko").order_by("-published_at")[:8],
            "indian_movies":  base_qs.filter(primary_language__code="hi").order_by("-published_at")[:8],
            "cartoon_movies": base_qs.filter(content_type="animation").order_by("-published_at")[:8],
            "retro_movies":   base_qs.filter(release_year__lte=1999).order_by("-release_year")[:8],
            "anime_movies":   base_qs.filter(genres__slug="anime").order_by("-published_at")[:8],
            "oscar_movies":   base_qs.filter(imdb_rating__gte=8.0).order_by("-imdb_rating")[:8],
            "featured_movie": base_qs.order_by("-average_rating").first(),
        })
        return ctx


# ─────────────────────────────────────────────
# Catalog
# ─────────────────────────────────────────────

class CatalogPageView(SeoMixin, TemplateView):
    template_name = "pages/catalog.html"
    seo_title     = "Filmlar katalogi — CinemaSavvy"
    paginate_by   = 24

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request"):
            return ["partials/movies_grid.html"]
        return [self.template_name]

    ALLOWED_ORDERINGS = {
        "-published_at":   "Yangiligi bo'yicha",
        "-average_rating": "Reytingi bo'yicha",
        "-view_count":     "Ko'rishlar bo'yicha",
        "-release_year":   "Yili bo'yicha",
    }

    def get_queryset(self) -> QuerySet:
        qs = Movie.objects.published().with_relations()
        p  = self.request.GET

        if genre := p.get("genre"):
            qs = qs.filter(genres__slug=genre)

        if language := p.get("language"):
            qs = qs.filter(primary_language__code=language)

        if content_type := p.get("content_type"):
            qs = qs.filter(content_type=content_type)

        if year_min := p.get("year_min"):
            qs = qs.filter(release_year__gte=year_min)

        if year_max := p.get("year_max"):
            qs = qs.filter(release_year__lte=year_max)

        if imdb_min := p.get("imdb_min"):
            qs = qs.filter(imdb_rating__gte=imdb_min)

        if is_premium := p.get("is_premium"):
            qs = qs.filter(is_premium=is_premium == "true")

        if search := p.get("q"):
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(title_original__icontains=search)
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
            "selected_content_type": p.get("content_type", ""),
            "year_min":          p.get("year_min", ""),
            "year_max":          p.get("year_max", ""),
            "search_query":      p.get("q", ""),
            "is_premium_filter": p.get("is_premium", ""),
        })
        return ctx


# ─────────────────────────────────────────────
# Movie Detail
# ─────────────────────────────────────────────

class MovieReviewsPartialView(ListView):
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
    template_name       = "pages/movie_detail.html"
    model               = Movie
    slug_field          = "slug"
    context_object_name = "movie"

    def get_queryset(self) -> QuerySet:
        return Movie.objects.published().with_relations()

    def get_seo(self) -> dict[str, str]:
        movie = self.get_object()
        return {
            "seo_title":       f"{movie.title} ({movie.release_year}) — CinemaSavvy",
            "seo_description": (movie.description[:155] + "...") if movie.description else "",
            "seo_image":       movie.poster.url if movie.poster else "",
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx   = super().get_context_data(**kwargs)
        movie = self.object

        # User specific — AnonymousUser uchun xavfsiz
        user_review    = None
        is_watchlisted = False
        if self.request.user.is_authenticated:
            try:
                from reviews.models import Review
                user_review = Review.objects.filter(
                    user=self.request.user, movie=movie, is_active=True,
                ).first()
            except Exception:
                pass
            try:
                from watchlist.models import Watchlist
                is_watchlisted = Watchlist.objects.filter(
                    user=self.request.user, movie=movie
                ).exists()
            except Exception:
                pass

        # Related movies
        related_movies = (
            Movie.objects.published()
            .filter(genres__in=movie.genres.all())
            .exclude(pk=movie.pk)
            .distinct()
            .order_by("-average_rating")[:6]
        )

        ctx.update({
            "user_review":     user_review,
            "is_watchlisted":  is_watchlisted,
            "related_movies":  related_movies,
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
        # Avval login tekshiruvi (LoginRequiredMixin orqali)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        response = super().dispatch(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx   = super().get_context_data(**kwargs)
        movie = self.object

        # Premium tekshiruv
        if movie.is_premium and not self.request.user.is_premium:
            from django.shortcuts import redirect
            return redirect("auth:subscription")

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

        first_file = available_files.first()
        video_url = f"/media/{first_file.file_key}" if first_file else ""

        resume_position = 0
        try:
            resume_position = WatchHistoryService.get_resume_position(
                self.request.user, movie
            )
        except Exception:
            pass

        ctx.update({
            "available_files":     available_files,
            "available_languages": languages,
            "default_lang":        default_lang,
            "resume_position":     resume_position,
            "subtitles":           movie.subtitles.select_related("language").all(),
            "youtube_url":         movie.youtube_url,
            "video_url":           video_url if not movie.youtube_url else "",
            "youtube_embed_id":    movie.youtube_url.split("v=")[-1].split("&")[0]
                                   if movie.youtube_url and "v=" in movie.youtube_url else "",
        })
        return ctx


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
# Search
# ─────────────────────────────────────────────

class SearchView(TemplateView):
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
        ctx.update({"results": results, "query": query})
        return ctx


# ─────────────────────────────────────────────
# Watch History
# ─────────────────────────────────────────────

class WatchHistoryPageView(LoginRequiredMixin, SeoMixin, TemplateView):
    template_name = "pages/watch_history.html"
    seo_title     = "Ko'rish tarixi — CinemaSavvy"
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
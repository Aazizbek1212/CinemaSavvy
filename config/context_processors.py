import logging

from django.urls import reverse

from movies.models import Genre, Movie

logger = logging.getLogger(__name__)


def global_context(request):
    """Har bir shablon kontekstiga qo'shiladi (navbar va footer uchun)."""
    nav_items = [
        {"title": "Bosh sahifa", "url": reverse("home"), "icon": "🏠"},
        {"title": "Katalog", "url": reverse("catalog"), "icon": "🎬"},
        {"title": "To'plamlar", "url": "#", "icon": "📁"},
        {"title": "Premium", "url": reverse("auth:subscription"), "icon": "👑"},
    ]

    nav_genres = []
    footer_movie_links = []
    try:
        nav_genres = list(Genre.objects.all()[:10])
        footer_movie_links = list(
            Movie.objects.filter(status=Movie.Status.PUBLISHED)
            .order_by("-average_rating")[:5]
        )
    except Exception as exc:  # DB hali tayyor bo'lmasa (migratsiyalardan oldin)
        logger.warning("global_context ma'lumot yuklay olmadi: %s", exc)

    return {
        "nav_items": nav_items,
        "nav_genres": nav_genres,
        "site_name": "CinemaSavvy",
        "site_url": "https://cinemasavvy.uz",
        "footer_movie_links": footer_movie_links,
    }

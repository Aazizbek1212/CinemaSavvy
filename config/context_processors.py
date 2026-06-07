import logging
from movies.models import Genre

logger = logging.getLogger(__name__)


def global_context(request) -> dict:
    """
    Injected into every template context.
    Cached per request — no repeated DB queries.
    """
    nav_genres = []
    try:
        nav_genres = list(Genre.objects.all()[:8])
    except Exception as exc:
        logger.warning("Could not load nav genres: %s", exc)

    return {
        "nav_items": [
            {"label": "Bosh sahifa", "url": "/"},
            {"label": "Filmlar",     "url": "/movies/"},
            {"label": "Seriallar",   "url": "/movies/?type=series"},
            {"label": "O'zbek",      "url": "/movies/?language=uz"},
            {"label": "Top",         "url": "/movies/?ordering=-average_rating"},
        ],
        "nav_genres": nav_genres,
        "site_name":  "Cinema.uz",
        "site_url":   "https://cinema.uz",
    }


def global_context(request) -> dict:
    return {
        # ... mavjud kod ...
        "footer_movie_links": [
            {"label": "Yangi filmlar",    "url": "/movies/?ordering=-published_at"},
            {"label": "Top reytingli",    "url": "/movies/?ordering=-average_rating"},
            {"label": "O'zbek filmlar",   "url": "/movies/?language=uz"},
            {"label": "Bepul filmlar",    "url": "/movies/?is_premium=false"},
            {"label": "Premium kontent",  "url": "/movies/?is_premium=true"},
        ],
    }
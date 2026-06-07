from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ── Error handlers ──────────────────────────
handler400 = "pages.views.error_400"
handler403 = "pages.views.error_403"
handler404 = "pages.views.error_404"
handler500 = "pages.views.error_500"

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # ── Page URLs (template views) ──────────
    path("", include("movies.urls.pages")),
    path("auth/", include("users.urls.pages")),

    # ── API URLs ────────────────────────────
    path("api/auth/",      include("users.urls.api",      namespace="users-api")),
    path("api/movies/",    include("movies.urls.api",      namespace="movies-api")),
    path("api/",           include("reviews.urls",         namespace="reviews")),
    path("api/streaming/", include("streaming.urls",       namespace="streaming")),

    # ── Social auth ─────────────────────────
    path("auth/social/", include("social_django.urls", namespace="social")),

    path("", include("search.urls", namespace="search")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
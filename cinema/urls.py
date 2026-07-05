from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Error handlers
handler400 = "pages.views.error_400"
handler403 = "pages.views.error_403"
handler404 = "pages.views.error_404"
handler500 = "pages.views.error_500"

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Page URLs (template views)
    path("", include("movies.urls.pages")),
    path("auth/", include(("users.urls.pages", "auth"), namespace="auth")),

    # API URLs
    path("api/auth/", include(("users.urls", "users"), namespace="users")),
    path("api/movies/", include(("movies.urls", "movies"), namespace="movies")),
    path("api/reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),
    path("api/streaming/", include(("streaming.urls", "streaming"), namespace="streaming")),
    path("api/watchlist/", include(("watchlist.urls", "watchlist"), namespace="watchlist")),

    # Social auth
    path("social/", include("social_django.urls", namespace="social")),

    # Search
    path("", include("search.urls", namespace="search")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
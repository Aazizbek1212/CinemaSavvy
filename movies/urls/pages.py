from django.urls import path

from movies.views.pages import (
    CatalogPageView,
    HomePageView,
    MovieDetailPageView,
    MovieReviewsPartialView,
    PersonDetailPageView,
    WatchHistoryPageView,
    WatchPageView,
)

urlpatterns = [
    path("",
         HomePageView.as_view(),
         name="home"),

    path("movies/",
         CatalogPageView.as_view(),
         name="catalog"),

    path("movies/<slug:slug>/",
         MovieDetailPageView.as_view(),
         name="movie-detail"),

    path("movies/<slug:slug>/reviews-html/",
         MovieReviewsPartialView.as_view(),
         name="movie-reviews-html"),

    path("watch/<slug:slug>/",
         WatchPageView.as_view(),
         name="watch"),

    path("persons/<slug:slug>/",
         PersonDetailPageView.as_view(),
         name="person-detail"),

    # Eslatma: `search/` URL `search.urls` da ro'yxatga olingan
    # (name="search-page"). Bu yerda takroran ro'yxatga olish URL
    # konfliktiga olib kelgan edi — olib tashlandi.

    path("history/",
         WatchHistoryPageView.as_view(),
         name="watch-history"),
]
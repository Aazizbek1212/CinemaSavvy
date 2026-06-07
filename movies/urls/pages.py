from django.urls import path
from movies.views.pages import (
    HomePageView,
    CatalogPageView,
    MovieDetailPageView,
    WatchPageView,
    PersonDetailPageView,
    SearchView,
    WatchHistoryPageView,
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

    path("watch/<slug:slug>/",
         WatchPageView.as_view(),
         name="watch"),

    path("persons/<slug:slug>/",
         PersonDetailPageView.as_view(),
         name="person-detail"),

    path("search/",
         SearchView.as_view(),
         name="search"),

    path("history/",
         WatchHistoryPageView.as_view(),
         name="watch-history"),
]
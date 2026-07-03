from django.urls import path
from ..views import (
    MovieListView, 
    MovieDetailView, 
    GenreListView, 
    PersonDetailView,
    MovieComparisonView,
    MovieShareView,
)

app_name = "movies-api"

urlpatterns = [
    path("", MovieListView.as_view(), name="movie-list"),
    path("genres/", GenreListView.as_view(), name="genre-list"),
    path("persons/<slug:slug>/", PersonDetailView.as_view(), name="person-detail"),
    path("compare/", MovieComparisonView.as_view(), name="movie-comparison"),
    path("<slug:slug>/share/", MovieShareView.as_view(), name="movie-share"),
    path("<slug:slug>/", MovieDetailView.as_view(), name="movie-detail"),
]

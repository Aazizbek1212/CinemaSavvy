from django.urls import path
from ..views import MovieListView, MovieDetailView, GenreListView, PersonDetailView

app_name = "movies-api"

urlpatterns = [
    path("", MovieListView.as_view(), name="movie-list"),
    path("<slug:slug>/", MovieDetailView.as_view(), name="movie-detail"),
    path("genres/", GenreListView.as_view(), name="genre-list"),
    path("persons/<slug:slug>/", PersonDetailView.as_view(), name="person-detail"),
]

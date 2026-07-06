from django.urls import path
from ..views import (
    MovieReviewListView,
    MovieReviewCreateView,
)

urlpatterns = [
    path('movies/<slug:slug>/reviews/', MovieReviewListView.as_view(), name='movie-reviews'),
    path('movies/<slug:slug>/reviews/create/', MovieReviewCreateView.as_view(), name='movie-review-create'),
]
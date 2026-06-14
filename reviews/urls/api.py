from django.urls import path
from ..views import (
    MovieReviewListView,
    MovieReviewCreateView,
    ReviewDetailView,
    ReviewLikeToggleView,
)

urlpatterns = [
    path("<slug:slug>/reviews/", MovieReviewListView.as_view(), name="movie-reviews"),
    path("<slug:slug>/reviews/create/", MovieReviewCreateView.as_view(), name="create-review"),
    path("reviews/<uuid:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("reviews/<uuid:pk>/like/", ReviewLikeToggleView.as_view(), name="like-review"),
]

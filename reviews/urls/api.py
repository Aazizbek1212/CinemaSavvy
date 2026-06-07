from django.urls import path
from ..views import MovieReviewListView, MovieReviewCreateView, ReviewLikeToggleView

urlpatterns = [
    path("<slug:slug>/reviews/", MovieReviewListView.as_view(), name="movie-reviews"),
    path("<slug:slug>/reviews/create/", MovieReviewCreateView.as_view(), name="create-review"),
    path("<int:review_id>/like/", ReviewLikeToggleView.as_view(), name="like-review"),
]

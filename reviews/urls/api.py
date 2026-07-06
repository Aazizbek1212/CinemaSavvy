from django.urls import path
from ..views.movie_review_views import MovieReviewListView, MovieReviewCreateView
from ..views.review_detail_views import ReviewDetailView

urlpatterns = [
    path('movies/<slug:slug>/reviews/', MovieReviewListView.as_view(), name='movie-reviews'),
    path('movies/<slug:slug>/reviews/create/', MovieReviewCreateView.as_view(), name='movie-review-create'),
    path('reviews/<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
]

app_name = 'reviews'
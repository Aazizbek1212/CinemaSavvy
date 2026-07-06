from django.urls import path, include
from .api import urlpatterns as api_patterns
from views.movie_review_views import MovieReviewListView, MovieReviewCreateView

__all__ = [
    'MovieReviewListView',
    'MovieReviewCreateView',
]
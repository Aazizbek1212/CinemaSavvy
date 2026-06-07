from django.urls import path, include
from .api import urlpatterns as api_patterns

app_name = "reviews"

urlpatterns = [
    path("movies/", include(api_patterns)),
]

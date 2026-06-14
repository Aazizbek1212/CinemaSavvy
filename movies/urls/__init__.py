from django.urls import path, include
from .api import urlpatterns as api_patterns


urlpatterns = [
    path("api/", include("movies.urls.api")),  # app_namesiz
]

from django.urls import path, include
from .api import urlpatterns as api_patterns


urlpatterns = [
    path("", include("users.urls.api")),
]

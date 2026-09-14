from django.urls import include, path

from .api import urlpatterns as api_patterns

app_name = "streaming"

urlpatterns = [
    path("", include(api_patterns)),
]

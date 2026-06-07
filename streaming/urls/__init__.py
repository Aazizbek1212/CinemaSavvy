from django.urls import path, include
from .api import urlpatterns as api_patterns

app_name = "streaming"

urlpatterns = [
    path("", include(api_patterns)),
]

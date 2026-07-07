from django.urls import path, include

urlpatterns = [
    path('', include('reviews.urls.api')),
]
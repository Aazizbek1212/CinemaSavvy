from django.urls import path

from . import views

app_name = "search"

urlpatterns = [
    # To'liq qidiruv sahifasi — /search/
    path("search/",                  views.SearchPageView.as_view(),      name="search-page"),
    # Qidiruv API — /api/search/  (namespace: search)
    path("api/search/",              views.SearchAPIView.as_view(),       name="api-search"),
    path("api/search/autocomplete/", views.AutocompleteAPIView.as_view(), name="autocomplete"),
]
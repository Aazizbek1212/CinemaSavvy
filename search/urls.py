from django.urls import path
from . import views

app_name = "search"

urlpatterns = [
    path("", views.SearchPageView.as_view(), name="index"),
    path("api/search/",              views.SearchAPIView.as_view(),      name="api-search"),
    path("api/search/autocomplete/", views.AutocompleteAPIView.as_view(), name="autocomplete"),
    path("search/",                  views.SearchPageView.as_view(),      name="search-page"),
]
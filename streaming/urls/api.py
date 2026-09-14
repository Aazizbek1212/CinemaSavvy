from django.urls import path

from ..views import StreamURLView, WatchHistoryView, WatchProgressView

app_name = "streaming"

urlpatterns = [
    path("history/", WatchHistoryView.as_view(), name="watch-history"),
    path("<slug:slug>/progress/", WatchProgressView.as_view(), name="watch-progress"),
    path("<slug:slug>/", StreamURLView.as_view(), name="stream-url"),
]

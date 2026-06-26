from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Watchlist
from .serializers import WatchlistSerializer

class WatchlistViewSet(viewsets.ModelViewSet):

    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Watchlist.objects
            .select_related("movie")
            .filter(user=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


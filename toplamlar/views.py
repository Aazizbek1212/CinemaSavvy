from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Collection
from .serializers import CollectionSerializer

class CollectionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = CollectionSerializer
    permission_classes = [AllowAny]

    queryset = (
        Collection.objects
        .prefetch_related(
            "collection_movies",
            "collection_movies__movie"
        )
        .all()
    )
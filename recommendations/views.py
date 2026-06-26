from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Recommendation
from .serializers import RecommendationSerializer

class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            Recommendation.objects
            .select_related("movie")
            .filter(user=self.request.user)
            .order_by("-score")
        )

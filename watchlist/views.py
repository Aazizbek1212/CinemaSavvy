from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from .models import Watchlist
from .serializers import WatchlistSerializer


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Faqat o'z foydalanuvchisining watchlistini qaytaradi
        return Watchlist.objects.filter(
            user=self.request.user
        ).select_related('movie').order_by('-created_at')

    def perform_create(self, serializer):
        # Yangi item qo'shilganda user avtomatik biriktiriladi
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        """Kino watchlistda bor bo'lsa o'chiradi, yo'q bo'lsa qo'shadi"""
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id majburiy'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item = Watchlist.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).first()

        if item:
            item.delete()
            return Response({'status': 'removed'}, status=status.HTTP_200_OK)
        else:
            obj = Watchlist.objects.create(
                user=request.user,
                movie_id=movie_id
            )
            serializer = self.get_serializer(obj)
            return Response(
                {'status': 'added', 'item': serializer.data},
                status=status.HTTP_201_CREATED
            )
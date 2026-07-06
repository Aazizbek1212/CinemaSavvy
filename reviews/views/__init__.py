from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import get_object_or_404

from movies.models import Movie
from reviews.serializers import ReviewSerializer
from reviews.models import Review


class MovieReviewListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        movie = get_object_or_404(Movie, slug=self.kwargs['slug'])
        return (
            Review.objects.active()
            .with_relations()
            .filter(movie=movie)
            .order_by('-created_at')
        )


class MovieReviewCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def create(self, request, *args, **kwargs):
        movie = get_object_or_404(Movie, slug=self.kwargs['slug'])

        # Foydalanuvchi bu filmga avval baho berganmi?
        if Review.objects.filter(movie=movie, user=request.user, is_active=True).exists():
            return Response(
                {'error': {'non_field_errors': ['Siz bu filmga allaqachon baho bergansiz']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, movie=movie)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
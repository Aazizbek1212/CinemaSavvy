from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from movies.models import Movie
from reviews.models import Review
from reviews.serializers import ReviewSerializer,ReviewCreateSerializer


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
    serializer_class = ReviewCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['movie'] = get_object_or_404(Movie, slug=self.kwargs['slug'])
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()

        output_serializer = ReviewSerializer(review, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
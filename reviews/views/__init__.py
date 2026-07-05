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
        movie = get_object_or_404(Movie, slug=self.kwargs["slug"])
        return (
            Review.objects.active()
            .with_relations()
            .filter(movie=movie)
            .order_by("-created_at")
        )


class MovieReviewCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        movie = get_object_or_404(Movie, slug=self.kwargs["slug"])
        serializer.save(user=self.request.user, movie=movie)

    def create(self, request, *args, **kwargs):
        movie = get_object_or_404(Movie, slug=self.kwargs["slug"])

        # Foydalanuvchi allaqachon baho berganmi?
        if Review.objects.filter(user=request.user, movie=movie, is_active=True).exists():
            return Response(
                {"error": {"non_field_errors": ["Siz allaqachon baho bergansiz"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class ReviewLikeToggleView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, is_active=True)
        if request.user in review.likes.all():
            review.likes.remove(request.user)
            liked = False
        else:
            review.likes.add(request.user)
            liked = True
        return Response({"liked": liked, "likes_count": review.likes.count()})
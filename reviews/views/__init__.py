from logging import getLogger
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.models import Movie
from ..models import Review, ReviewLike
from ..serializers import ReviewSerializer, ReviewCreateSerializer

logger = getLogger(__name__)


class MovieReviewListView(generics.ListAPIView):
    """
    GET /api/movies/<slug>/reviews/
    Kimda kim ko'rishi mumkin, login shart emas.
    """
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        movie = get_object_or_404(Movie, slug=self.kwargs["slug"])
        return (
            Review.objects.active()
            .with_relations()
            .filter(movie=movie)
            .prefetch_related("likes")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class MovieReviewCreateView(generics.CreateAPIView):
    """POST /api/movies/<slug>/reviews/"""
    serializer_class = ReviewCreateSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        ctx["movie"] = get_object_or_404(Movie, slug=self.kwargs["slug"])
        return ctx


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/reviews/<id>/
    PATCH  /api/reviews/<id>/
    DELETE /api/reviews/<id>/
    """
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        return Review.objects.active().with_relations()

    def get_object(self):
        review = get_object_or_404(
            Review,
            pk=self.kwargs["pk"],
            is_active=True,
        )
        # Faqat o'z review'ini tahrirlashi/o'chirishi mumkin
        if self.request.method not in ("GET",):
            if review.user_id != self.request.user.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Bu review sizga tegishli emas.")
        return review

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        review = self.get_object()
        review.soft_delete()
        return Response(
            {"detail": "Review o'chirildi."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        if hasattr(self.get_object(), "movie"):
            ctx["movie"] = self.get_object().movie
        return ctx


class ReviewLikeToggleView(APIView):
    """
    POST /api/reviews/<pk>/like/
    Like bosish / olib tashlash (toggle).
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: str) -> Response:
        review = get_object_or_404(Review, pk=pk, is_active=True)

        # O'z review'iga like bosa olmaydi
        if review.user_id == request.user.id:
            return Response(
                {"detail": "O'z review'ingizga like bosa olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        like, created = ReviewLike.objects.get_or_create(
            user=request.user,
            review=review,
        )

        if not created:
            like.delete()
            return Response({"liked": False, "like_count": review.like_count - 1})

        return Response({"liked": True, "like_count": review.like_count + 1})

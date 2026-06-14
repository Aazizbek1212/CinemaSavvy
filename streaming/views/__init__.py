from logging import getLogger
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.models import Movie
from ..models import WatchHistory
from ..serializers import StreamURLSerializer, WatchProgressSerializer, WatchHistorySerializer
from ..services import VideoStreamingService, WatchHistoryService

logger = getLogger(__name__)


class StreamURLView(APIView):
    """
    GET /api/streaming/<slug>/
    Returns presigned HLS URL + resume position.
    Premium check included.
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request: Request, slug: str) -> Response:
        movie = get_object_or_404(Movie.objects.published(), slug=slug)

        # Premium gating — AnonymousUser uchun xavfsiz tekshiruv
        if movie.is_premium:
            if not request.user.is_authenticated or not getattr(request.user, "is_premium", False):
                return Response(
                    {"detail": "Bu kontent premium obuna talab qiladi."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        quality = request.query_params.get("quality")
        movie_file = VideoStreamingService.get_best_quality_file(movie, quality)

        if not movie_file:
            return Response(
                {"detail": "Video hali tayyor emas."},
                status=status.HTTP_404_NOT_FOUND,
            )

        stream_url = VideoStreamingService.get_stream_url(movie_file)
        if not stream_url:
            return Response(
                {"detail": "Stream URL yaratishda xato."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        resume_position = 0
        if request.user.is_authenticated:
            resume_position = WatchHistoryService.get_resume_position(request.user, movie)

        # Subtitle presigned URLs
        subtitles = []
        for subtitle in movie.subtitles.select_related("language").all():
            from ..storage import minio_storage
            url = minio_storage.generate_presigned_url(subtitle.file_key, expires_in=7200)
            if url:
                subtitles.append({
                    "language_code": subtitle.language.code,
                    "language_name": subtitle.language.name,
                    "url": url,
                })

        return Response({
            "stream_url": stream_url,
            "quality": movie_file.quality,
            "resume_position": resume_position,
            "subtitles": subtitles,
        })


class WatchProgressView(APIView):
    """
    POST /api/streaming/<slug>/progress/
    Frontend har 10 sekundda pozitsiyani saqlaydi.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, slug: str) -> Response:
        movie = get_object_or_404(Movie, slug=slug)

        serializer = WatchProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        WatchHistoryService.update_progress(
            user=request.user,
            movie=movie,
            position_seconds=serializer.validated_data["position_seconds"],
            duration_seconds=serializer.validated_data.get("duration_seconds"),
        )

        return Response({"saved": True}, status=status.HTTP_200_OK)


class WatchHistoryView(generics.ListAPIView):
    """
    GET /api/streaming/history/
    Foydalanuvchining ko'rish tarixi.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = WatchHistorySerializer

    def get_queryset(self):
        return (
            WatchHistory.objects.filter(user=self.request.user)
            .select_related("movie")
            .order_by("-updated_at")[:50]
        )

import logging
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from movies.models import Movie, Genre, Person
from movies.serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
    GenreSerializer,
    PersonSerializer,
    MovieComparisonSerializer,
    MovieShareSerializer,
)

logger = logging.getLogger(__name__)


class MovieListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = MovieListSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["title", "title_original"]
    filterset_fields = ["genres__slug", "is_premium", "age_rating"]

    def get_queryset(self):
        qs = Movie.objects.published().prefetch_related(
            "genres", "languages"
        )

        slug = self.request.query_params.get("slug")
        if slug:
            qs = qs.filter(slug=slug)

        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(genres__slug=genre)

        language = self.request.query_params.get("language")
        if language:
            qs = qs.filter(primary_language__code=language)

        content_type = self.request.query_params.get("content_type")
        if content_type:
            qs = qs.filter(content_type=content_type)

        ordering = self.request.query_params.get("ordering", "-published_at")
        allowed = ["-published_at", "-average_rating", "-view_count", "-release_year", "release_year"]
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs.distinct()


class MovieDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = MovieDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Movie.objects.published().prefetch_related(
            "genres", "languages", "movie_cast__person",
            "subtitles__language", "video_files"
        ).select_related("primary_language")


class GenreListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = GenreSerializer
    queryset = Genre.objects.all().order_by("name")


class PersonDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = PersonSerializer
    lookup_field = "slug"
    queryset = Person.objects.all()


class MovieComparisonView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = MovieComparisonSerializer

    def get_queryset(self):
        slugs = self.request.query_params.getlist("slug")
        if not slugs:
            return Movie.objects.none()
        return Movie.objects.published().filter(
            slug__in=slugs
        ).prefetch_related("genres")


class MovieShareView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, slug):
        movie = get_object_or_404(Movie, slug=slug, status="published")
        data = {
            "title": movie.title,
            "slug": movie.slug,
            "poster": request.build_absolute_uri(movie.poster.url) if movie.poster else None,
            "url": request.build_absolute_uri(f"/movies/{movie.slug}/"),
            "description": movie.description[:200] if movie.description else "",
            "release_year": movie.release_year,
        }
        return Response(data)
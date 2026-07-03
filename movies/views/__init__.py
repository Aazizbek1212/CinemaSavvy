from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import get_object_or_404
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from ..models import Movie, Genre, Person
from ..serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
    GenreSerializer,
    PersonSerializer,
    MovieComparisonSerializer,
    MovieShareSerializer,
)
from ..filters import MovieFilter

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 5  # 5 daqiqa


class MovieListView(generics.ListAPIView):
    """
    GET /api/movies/
    Filters: genre, language, year_min, year_max, rating_min, is_premium
    Search: title, title_original
    Ordering: -average_rating, -view_count, -published_at, release_year
    """
    serializer_class = MovieListSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = MovieFilter
    search_fields = ("title", "title_original", "cast__full_name")
    ordering_fields = ("average_rating", "view_count", "published_at", "release_year")
    ordering = ("-published_at",)

    def get_queryset(self):
        return (
            Movie.objects.published()
            .with_relations()
            .only(
                "id", "title", "slug", "poster",
                "release_year", "duration_minutes",
                "average_rating", "rating_count",
                "is_premium", "age_rating", "published_at",
            )
        )

    @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MovieDetailView(generics.RetrieveAPIView):
    """GET /api/movies/<slug>/"""
    serializer_class = MovieDetailSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"

    def get_queryset(self):
        return Movie.objects.published().with_relations()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        # Increment view count async (no await — fire and forget)
        Movie.objects.filter(pk=self.get_object().pk).update(
            view_count=models.F("view_count") + 1
        )
        return response


class GenreListView(generics.ListAPIView):
    serializer_class = GenreSerializer
    permission_classes = (AllowAny,)
    queryset = Genre.objects.all()

    @method_decorator(cache_page(60 * 60))  # 1 soat cache
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PersonDetailView(generics.RetrieveAPIView):
    serializer_class = PersonSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    queryset = Person.objects.all()


class MovieComparisonView(APIView):
    """
    GET /api/movies/compare/?ids=id1,id2,id3
    Compare multiple movies side by side
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        ids_param = request.query_params.get("ids", "")
        if not ids_param:
            return Response(
                {"detail": "ids parametri zarur: ?ids=id1,id2,id3"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        ids = [id.strip() for id in ids_param.split(",")]
        movies = Movie.objects.filter(id__in=ids, status=Movie.Status.PUBLISHED)
        
        if not movies.exists():
            return Response(
                {"detail": "Topilgan filmlar yo'q."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = MovieComparisonSerializer(movies, many=True)
        return Response({
            "comparison": serializer.data,
            "count": len(serializer.data),
        })


class MovieShareView(APIView):
    """
    POST /api/movies/<slug>/share/
    Generate share links for social media
    """
    permission_classes = (AllowAny,)

    def post(self, request, slug):
        from django.conf import settings
        
        try:
            movie = Movie.objects.get(slug=slug, status=Movie.Status.PUBLISHED)
        except Movie.DoesNotExist:
            return Response(
                {"detail": "Film topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Generate share URLs for different platforms
        base_url = f"{settings.FRONTEND_URL}/movies/{slug}/"
        
        share_links = {
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={base_url}",
            "twitter": f"https://twitter.com/intent/tweet?url={base_url}&text={movie.title}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={base_url}",
            "whatsapp": f"https://wa.me/?text={movie.title} {base_url}",
            "email": f"mailto:?subject={movie.title}&body={base_url}",
        }
        
        logger.info("Movie shared: %s", movie.slug)
        
        return Response({
            "movie": {
                "title": movie.title,
                "slug": movie.slug,
                "poster": str(movie.poster) if movie.poster else None,
            },
            "share_links": share_links,
        })


class HomePageView(TemplateView):
    template_name = "pages/home.html"

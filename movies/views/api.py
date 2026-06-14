import logging
from django.db.models import F
from rest_framework import generics
from movies.models import Movie
from movies.serializers import MovieListSerializer, MovieDetailSerializer

logger = logging.getLogger(__name__)


# ✅ Xato #7: .only() da duration_minutes qo‘shildi
class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.only(
        "id",
        "title",
        "slug",
        "poster",
        "release_year",
        "duration_minutes",   # ← qo‘shildi
        "average_rating",
        "rating_count",
        "is_premium",
        "age_rating",
    )
    serializer_class = MovieListSerializer


# ✅ Xato #8: get_object() faqat 1 marta chaqiriladi
class MovieDetailView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        movie = self.get_object()  # faqat 1 marta chaqiriladi
        response = super().retrieve(request, *args, **kwargs)  # self.object ishlatiladi
        Movie.objects.filter(pk=movie.pk).update(view_count=F("view_count") + 1)
        logger.info("Movie viewed: %s (id=%d)", movie.title, movie.pk)
        return response

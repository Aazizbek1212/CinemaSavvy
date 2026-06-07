import django_filters
from .models import Movie, Genre, Language


class MovieFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(field_name="genres__slug", lookup_expr="exact")
    language = django_filters.CharFilter(field_name="languages__code", lookup_expr="exact")
    year_min = django_filters.NumberFilter(field_name="release_year", lookup_expr="gte")
    year_max = django_filters.NumberFilter(field_name="release_year", lookup_expr="lte")
    rating_min = django_filters.NumberFilter(field_name="average_rating", lookup_expr="gte")
    is_premium = django_filters.BooleanFilter(field_name="is_premium")
    age_rating = django_filters.CharFilter(field_name="age_rating", lookup_expr="exact")

    class Meta:
        model = Movie
        fields = ["genre", "language", "year_min", "year_max", "rating_min", "is_premium", "age_rating"]
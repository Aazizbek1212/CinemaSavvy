import logging
from rest_framework import serializers
from .models import Genre, Person, Language, Movie, MovieCast, MovieFile, Subtitle

logger = logging.getLogger(__name__)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", "slug")


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("id", "code", "name")


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ("id", "full_name", "slug", "role", "photo", "birth_date")


class MovieCastSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)

    class Meta:
        model = MovieCast
        fields = ("person", "character_name", "order")


class MovieFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieFile
        fields = ("id", "quality", "status", "duration_seconds")


class SubtitleSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)

    class Meta:
        model = Subtitle
        fields = ("id", "language", "is_auto_generated")


class MovieListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views. No heavy relations."""
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = (
            "id", "title", "slug", "poster",
            "release_year", "duration_display",
            "average_rating", "rating_count",
            "is_premium", "age_rating", "genres",
        )


class MovieDetailSerializer(serializers.ModelSerializer):
    """Full detail — for single movie view."""
    genres = GenreSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    primary_language = LanguageSerializer(read_only=True)
    cast = MovieCastSerializer(source="movie_cast", many=True, read_only=True)
    subtitles = SubtitleSerializer(many=True, read_only=True)
    available_qualities = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            "id", "title", "title_original", "slug",
            "description", "tagline", "poster", "backdrop",
            "trailer_url", "release_year", "duration_minutes",
            "duration_display", "country", "age_rating",
            "is_premium", "average_rating", "rating_count",
            "view_count", "genres", "primary_language",
            "languages", "cast", "subtitles",
            "available_qualities", "published_at",
        )

    def get_available_qualities(self, obj) -> list[str]:
        return list(
            obj.video_files.filter(
                status=MovieFile.Status.READY
            ).values_list("quality", flat=True)
        )
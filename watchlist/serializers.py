from rest_framework import serializers
from .models import Watchlist

class WatchlistSerializer(serializers.ModelSerializer):

    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True
    )

    movie_slug = serializers.CharField(
        source="movie.slug",
        read_only=True
    )

    movie_poster = serializers.ImageField(
        source="movie.poster",
        read_only=True
    )

    class Meta:
        model = Watchlist

        fields = [
            "id",
            "movie",
            "movie_title",
            "movie_slug",
            "movie_poster",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]
from rest_framework import serializers
from .models import Watchlist


class WatchlistSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(
        source='movie.title',
        read_only=True
    )
    movie_slug = serializers.CharField(
        source='movie.slug',
        read_only=True
    )
    movie_poster = serializers.ImageField(
        source='movie.poster',
        read_only=True
    )
    movie_year = serializers.IntegerField(
        source='movie.year',
        read_only=True
    )
    movie_rating = serializers.FloatField(
        source='movie.rating',
        read_only=True
    )

    class Meta:
        model = Watchlist
        fields = (
            'id',
            'movie',
            'movie_title',
            'movie_slug',
            'movie_poster',
            'movie_year',
            'movie_rating',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')
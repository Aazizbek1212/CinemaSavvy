from rest_framework import serializers
from .models import Collection, CollectionMovie

class CollectionMovieSerializer(serializers.ModelSerializer):

    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True
    )

    movie_poster = serializers.ImageField(
        source="movie.poster",
        read_only=True
    )

    class Meta:
        model = CollectionMovie

        fields = [
            "id",
            "movie",
            "movie_title",
            "movie_poster",
            "order",
        ]

    class CollectionSerializer(serializers.ModelSerializer):

    movies = CollectionMovieSerializer(
        source="collection_movies",
        many=True,
        read_only=True
    )

    class Meta:
        model = Collection

        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover",
            "is_featured",
            "movies",
        ]

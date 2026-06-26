from rest_framework import serializers
from .models import Recommendation

class RecommendationSerializer(serializers.ModelSerializer):

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
        model = Recommendation

        fields = [
            "id",
            "movie",
            "movie_title",
            "movie_slug",
            "movie_poster",
            "score",
            "reason",
        ]
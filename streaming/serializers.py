from rest_framework import serializers
from .models import WatchHistory


class StreamURLSerializer(serializers.Serializer):
    """Response for stream URL endpoint."""
    stream_url = serializers.URLField(read_only=True)
    quality = serializers.CharField(read_only=True)
    resume_position = serializers.IntegerField(read_only=True)
    subtitles = serializers.ListField(read_only=True)


class WatchProgressSerializer(serializers.Serializer):
    """Request body for progress update."""
    position_seconds = serializers.IntegerField(min_value=0)
    duration_seconds = serializers.IntegerField(min_value=1, required=False)


class WatchHistorySerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    movie_slug = serializers.CharField(source="movie.slug", read_only=True)
    movie_poster = serializers.ImageField(source="movie.poster", read_only=True)
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = WatchHistory
        fields = (
            "id", "movie_title", "movie_slug", "movie_poster",
            "position_seconds", "duration_seconds",
            "progress_percent", "completed", "updated_at",
        )
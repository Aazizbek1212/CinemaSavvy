from rest_framework import serializers


class MovieSearchResultSerializer(serializers.Serializer):
    id            = serializers.CharField()
    title         = serializers.CharField()
    title_original = serializers.CharField()
    slug          = serializers.CharField()
    release_year  = serializers.IntegerField()
    poster_url    = serializers.CharField()
    average_rating = serializers.FloatField()
    is_premium    = serializers.BooleanField()
    genres        = serializers.ListField()
    duration_minutes = serializers.IntegerField()
    highlight     = serializers.DictField(required=False)
    score         = serializers.FloatField(required=False)


class PersonSearchResultSerializer(serializers.Serializer):
    id           = serializers.CharField()
    full_name    = serializers.CharField()
    slug         = serializers.CharField()
    role         = serializers.CharField()
    photo_url    = serializers.CharField()
    movies_count = serializers.IntegerField()


class SearchResponseSerializer(serializers.Serializer):
    query        = serializers.CharField()
    total        = serializers.IntegerField()
    took_ms      = serializers.IntegerField()
    movies       = MovieSearchResultSerializer(many=True)
    persons      = PersonSearchResultSerializer(many=True)
    suggestions  = serializers.ListField(child=serializers.CharField())
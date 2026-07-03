import logging
from typing import Any
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Review, ReviewLike

logger = logging.getLogger(__name__)
User = get_user_model()


class ReviewAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "avatar")


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewAuthorSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id", "user", "rating", "text",
            "like_count", "is_liked", "can_edit",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "like_count", "created_at", "updated_at")

    def get_is_liked(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_can_edit(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("rating", "text")

    def validate_rating(self, value: int) -> int:
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Reyting 1 dan 10 gacha bo'lishi kerak.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]
        movie = self.context["movie"]

        existing = Review.objects.filter(
            user=request.user,
            movie=movie,
            is_active=True,
        ).exists()

        if existing and not self.instance:
            raise serializers.ValidationError(
                {"non_field_errors": "Siz bu filmga allaqachon baho bergansiz."}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Review:
        return Review.objects.create(
            user=self.context["request"].user,
            movie=self.context["movie"],
            **validated_data,
        )

    def update(self, instance: Review, validated_data: dict[str, Any]) -> Review:
        instance.rating = validated_data.get("rating", instance.rating)
        instance.text = validated_data.get("text", instance.text)
        instance.save(update_fields=["rating", "text", "updated_at"])
        return instance


class ReviewLikeSerializer(serializers.ModelSerializer):
    user = ReviewAuthorSerializer(read_only=True)
    
    class Meta:
        model = ReviewLike
        fields = ("id", "user", "review", "created_at")
        read_only_fields = ("id", "user", "created_at")
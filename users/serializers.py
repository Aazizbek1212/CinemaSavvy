import logging
from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Registration serializer.
    - Password confirmation validation
    - Email uniqueness check (case-insensitive)
    - Django password validators applied
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "password", "password_confirm")

    def validate_email(self, value: str) -> str:
        normalized = value.lower().strip()
        if User.objects.filter(email=normalized).exists():
            # Generic message — prevents email enumeration
            raise serializers.ValidationError(
                "Bu ma'lumotlar bilan ro'yxatdan o'tib bo'lmaydi."
            )
        return normalized

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi."})

        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
            is_verified=False,
        )


class UserLoginSerializer(serializers.Serializer):
    """
    Login serializer — returns JWT tokens.
    Constant-time comparison to prevent timing attacks.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        from django.contrib.auth import authenticate

        email = attrs["email"].lower().strip()
        password = attrs["password"]

        # authenticate() uses constant-time compare internally
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        # Single generic error — prevents user enumeration
        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": "Email yoki parol noto'g'ri."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "Hisob faolsizlantirilgan."}
            )

        if not user.is_verified:
            raise serializers.ValidationError(
                {"non_field_errors": "Email tasdiqlanmagan. Emailingizni tekshiring."}
            )

        attrs["user"] = user
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Output serializer for login/token responses."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()

    def get_user(self, obj: dict) -> dict:
        user = obj["user"]
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.display_name,
            "is_premium": user.is_premium,
            "avatar": user.avatar.url if user.avatar else None,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Profile read/update serializer.
    Sensitive fields (password, is_staff) are excluded.
    """

    avatar_url = serializers.SerializerMethodField(read_only=True)
    is_premium = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "bio",
            "avatar",
            "avatar_url",
            "is_premium",
            "subscription_tier",
            "subscription_expires_at",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "email",
            "subscription_tier",
            "subscription_expires_at",
            "date_joined",
        )
        extra_kwargs = {
            "avatar": {"write_only": True},
        }

    def get_avatar_url(self, obj) -> str | None:
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None

    def validate_avatar(self, value):
        max_size = 2 * 1024 * 1024  # 2 MB
        allowed_types = ("image/jpeg", "image/png", "image/webp")

        if value.size > max_size:
            raise serializers.ValidationError("Avatar hajmi 2MB dan oshmasligi kerak.")
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Faqat JPEG, PNG, WebP formatlar qabul qilinadi.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password": "Parollar mos kelmaydi."})

        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password": "Parollar mos kelmaydi."})

        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        return attrs
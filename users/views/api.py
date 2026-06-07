import logging
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from ..services import AuthService

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    def post(self, request: Request) -> Response:
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.register_user(serializer.validated_data, request)

        return Response(
            {"detail": "Ro'yxatdan o'tdingiz. Emailingizni tasdiqlang."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    def post(self, request: Request) -> Response:
        serializer = UserLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Track last login IP
        ip = self._get_client_ip(request)
        user.last_login_ip = ip
        user.save(update_fields=["last_login_ip"])

        tokens = AuthService.get_tokens_for_user(user)
        logger.info("User logged in: %s from IP: %s", user.email, ip)

        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.display_name,
                    "is_premium": user.is_premium,
                },
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request: Request) -> str | None:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: %s", request.user.email)
        except TokenError as exc:
            return Response(
                {"detail": "Token noto'g'ri yoki muddati o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Chiqildi."}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request: Request, uid: str, token: str) -> Response:
        success = AuthService.verify_email(uid, token)
        if success:
            return Response({"detail": "Email tasdiqlandi."}, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Havola noto'g'ri yoki muddati o'tgan."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = AuthService.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return Response(
                {"detail": "Joriy parol noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Parol o'zgartirildi."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.request_password_reset(
            email=serializer.validated_data["email"],
            request=request,
        )

        # Always return success — prevents email enumeration
        return Response(
            {"detail": "Agar bu email mavjud bo'lsa, tiklash havolasi yuborildi."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = AuthService.confirm_password_reset(
            uid_b64=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )

        if not success:
            return Response(
                {"detail": "Havola noto'g'ri yoki muddati o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Parol muvaffaqiyatli tiklandi."}, status=status.HTTP_200_OK)

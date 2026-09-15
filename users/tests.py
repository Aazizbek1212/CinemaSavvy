from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from users.serializers import UserLoginSerializer
from users.social_pipeline import create_or_update_social_user

User = get_user_model()


class AuthIntegrationTests(TestCase):
    def test_login_serializer_accepts_email_based_auth(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
            full_name="Test User",
            is_verified=True,
        )

        serializer = UserLoginSerializer(data={"email": user.email, "password": "StrongPass123!"})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], user)

    def test_user_model_has_verification_and_reset_token_fields(self):
        user = User.objects.create_user(
            email="token-user@example.com",
            password="StrongPass123!",
            full_name="Token User",
            is_verified=True,
        )

        self.assertTrue(hasattr(user, "verification_token"))
        self.assertTrue(hasattr(user, "reset_token"))

    def test_subscription_page_provides_plan_data(self):
        user = User.objects.create_user(
            email="premium-user@example.com",
            password="StrongPass123!",
            full_name="Premium User",
            is_verified=True,
        )

        self.client.force_login(user)
        response = self.client.get("/auth/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("plans", response.context)
        self.assertIn("feature_items", response.context)
        self.assertTrue(any(plan["popular"] for plan in response.context["plans"]))

    def test_is_premium_is_true_only_for_active_premium_subscription(self):
        active_user = User.objects.create_user(
            email="active-premium@example.com",
            password="StrongPass123!",
            full_name="Active Premium",
            is_verified=True,
            subscription_tier=User.SubscriptionTier.PREMIUM,
            subscription_expires_at=timezone.now() + timedelta(days=30),
        )
        expired_user = User.objects.create_user(
            email="expired-premium@example.com",
            password="StrongPass123!",
            full_name="Expired Premium",
            is_verified=True,
            subscription_tier=User.SubscriptionTier.PREMIUM,
            subscription_expires_at=timezone.now() - timedelta(days=1),
        )

        self.assertTrue(active_user.is_premium)
        self.assertFalse(expired_user.is_premium)

    def test_social_pipeline_creates_user_from_google_email(self):
        details = {"email": "google-user@example.com", "fullname": "Google User", "name": "Google User"}

        result = create_or_update_social_user(
            strategy=None,
            backend=None,
            user=None,
            details=details,
            response={},
            uid="google-123",
            is_new=True,
        )

        self.assertIsNotNone(result)
        self.assertTrue(User.objects.filter(email="google-user@example.com").exists())
        self.assertEqual(User.objects.get(email="google-user@example.com").full_name, "Google User")
        self.assertTrue(User.objects.get(email="google-user@example.com").is_verified)

    def test_login_page_exposes_google_login_without_dead_provider_link(self):
        response = self.client.get("/auth/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/social/begin/google-oauth2/")
        self.assertNotContains(response, 'href="#"')

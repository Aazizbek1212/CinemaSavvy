import uuid
import logging
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)


def user_avatar_upload_path(instance: "CustomUser", filename: str) -> str:
    """
    Unique upload path to prevent filename collisions.
    Result: avatars/2024/01/<uuid>.<ext>
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return f"avatars/{timezone.now().strftime('%Y/%m')}/{unique_name}"


class CustomUserManager(BaseUserManager):
    """
    Manager that uses email as the unique identifier instead of username.
    """

    def _create_user(
        self,
        email: str,
        password: str | None,
        **extra_fields,
    ) -> "CustomUser":
        if not email:
            raise ValueError(_("Email address is required."))

        email = self.normalize_email(email).lower()  # force lowercase
        user: CustomUser = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        logger.info("New user created: %s (staff=%s)", email, extra_fields.get("is_staff", False))
        return user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "CustomUser":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "CustomUser":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Production-grade custom user model.

    - Email is the primary identifier (no username field).
    - Soft delete via `is_active=False` instead of hard delete.
    - `is_verified` controls email confirmation.
    - UUID primary key prevents enumeration attacks.
    """

    class SubscriptionTier(models.TextChoices):
        FREE = "free", _("Free")
        PREMIUM = "premium", _("Premium")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=254,
        db_index=True,
    )
    full_name = models.CharField(_("full name"), max_length=150, blank=True)
    avatar = models.ImageField(
        _("avatar"),
        upload_to=user_avatar_upload_path,
        blank=True,
        null=True,
    )
    bio = models.TextField(_("bio"), max_length=500, blank=True, null=True)

    # Status flags
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Soft delete: uncheck instead of deleting the record."),
    )
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_verified = models.BooleanField(
        _("email verified"),
        default=False,
        help_text=_("User cannot log in until email is verified."),
    )

    # Subscription
    subscription_tier = models.CharField(
        _("subscription tier"),
        max_length=10,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE,
        db_index=True,
    )
    subscription_expires_at = models.DateTimeField(
        _("subscription expires at"),
        null=True,
        blank=True,
    )

    # Timestamps
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login_ip = models.GenericIPAddressField(
        _("last login IP"),
        null=True,
        blank=True,
        protocol="both",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser da faqat email + password so'raladi

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["subscription_tier", "subscription_expires_at"]),
        ]

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<CustomUser id={self.id} email={self.email}>"

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def is_premium(self) -> bool:
        """Returns True only if subscription is active and not expired."""
        if self.subscription_tier != self.SubscriptionTier.PREMIUM:
            return False
        if self.subscription_expires_at is None:
            return False
        return self.subscription_expires_at > timezone.now()

    @property
    def display_name(self) -> str:
        return self.full_name.strip() or self.email.split("@")[0]

    # ------------------------------------------------------------------ #
    # Methods
    # ------------------------------------------------------------------ #

    def deactivate(self) -> None:
        """Soft delete — do not use .delete() directly."""
        self.is_active = False
        self.save(update_fields=["is_active"])
        logger.warning("User deactivated: %s", self.email)

    def upgrade_to_premium(self, expires_at) -> None:
        self.subscription_tier = self.SubscriptionTier.PREMIUM
        self.subscription_expires_at = expires_at
        self.save(update_fields=["subscription_tier", "subscription_expires_at"])
        logger.info("User upgraded to premium: %s, expires: %s", self.email, expires_at)
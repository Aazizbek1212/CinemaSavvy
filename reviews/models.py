import uuid
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
User = get_user_model()


class ReviewQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_relations(self):
        return self.select_related("user", "movie")

    def for_movie(self, movie):
        return self.filter(movie=movie, is_active=True)


class ReviewManager(models.Manager):
    def get_queryset(self) -> ReviewQuerySet:
        return ReviewQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_relations(self):
        return self.get_queryset().with_relations()


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("user"),
    )
    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("movie"),
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    text = models.TextField(_("review text"), blank=True, max_length=2000)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Soft delete"),
    )
    like_count = models.PositiveIntegerField(_("like count"), default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReviewManager()

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")
        # One review per user per movie
        unique_together = [("user", "movie")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["movie", "is_active", "-created_at"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.movie.title} ({self.rating}/10)"

    def soft_delete(self) -> None:
        self.is_active = False
        self.save(update_fields=["is_active"])
        logger.info("Review soft deleted: %s", self.id)


class ReviewLike(models.Model):
    """Tracks who liked which review — prevents duplicate likes."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="review_likes",
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("review like")
        verbose_name_plural = _("review likes")
        unique_together = [("user", "review")]

    def __str__(self) -> str:
        return f"{self.user.email} liked {self.review.id}"
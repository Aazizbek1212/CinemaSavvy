import uuid
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
User = get_user_model()


class WatchHistory(models.Model):
    """
    Tracks where user stopped watching — resume from last position.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watch_history",
    )
    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        related_name="watch_history",
    )
    # Last watched position in seconds
    position_seconds = models.PositiveIntegerField(
        _("position (seconds)"), default=0
    )
    # Total duration at time of watching
    duration_seconds = models.PositiveIntegerField(
        _("duration (seconds)"), null=True, blank=True
    )
    completed = models.BooleanField(_("completed"), default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("watch history")
        verbose_name_plural = _("watch histories")
        unique_together = [("user", "movie")]
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.movie.title} @ {self.position_seconds}s"

    @property
    def progress_percent(self) -> float:
        if not self.duration_seconds or self.duration_seconds == 0:
            return 0.0
        return round(self.position_seconds / self.duration_seconds * 100, 1)


class VideoProcessingJob(models.Model):
    """
    Tracks FFmpeg HLS conversion jobs.
    """
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie_file = models.OneToOneField(
        "movies.MovieFile",
        on_delete=models.CASCADE,
        related_name="processing_job",
    )
    status = models.CharField(
        _("status"),
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    progress_percent = models.PositiveSmallIntegerField(
        _("progress (%)"), default=0
    )
    error_message = models.TextField(_("error message"), blank=True)
    started_at = models.DateTimeField(_("started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("video processing job")
        verbose_name_plural = _("video processing jobs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Job {self.id} — {self.status}"
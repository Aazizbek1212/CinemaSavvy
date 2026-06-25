import uuid
import logging
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

logger = logging.getLogger(__name__)


def movie_poster_path(instance: "Movie", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"posters/{instance.release_year}/{uuid.uuid4().hex}.{ext}"


def person_photo_path(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"persons/{uuid.uuid4().hex}.{ext}"


class TimeStampedModel(models.Model):
    """Abstract base — created_at, updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ──────────────────────────────────────────────
# Genre
# ──────────────────────────────────────────────

class Genre(TimeStampedModel):
    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True, blank=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genres")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────
# Person (Actor / Director — shared model)
# ──────────────────────────────────────────────

class Person(TimeStampedModel):
    class Role(models.TextChoices):
        ACTOR = "actor", _("Actor")
        DIRECTOR = "director", _("Director")
        BOTH = "both", _("Actor & Director")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(_("full name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=220, unique=True, blank=True)
    role = models.CharField(
        _("role"), max_length=10,
        choices=Role.choices,
        default=Role.ACTOR,
        db_index=True,
    )
    bio = models.TextField(_("biography"), blank=True)
    birth_date = models.DateField(_("birth date"), null=True, blank=True)
    birth_place = models.CharField(_("birth place"), max_length=200, blank=True)
    photo = models.ImageField(
        _("photo"), upload_to=person_photo_path,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = _("person")
        verbose_name_plural = _("persons")
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["role", "full_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.full_name)
            slug = base_slug
            counter = 1
            while Person.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────
# Language
# ──────────────────────────────────────────────

class Language(models.Model):
    code = models.CharField(_("code"), max_length=10, unique=True)  # uz, ru, en
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        verbose_name = _("language")
        verbose_name_plural = _("languages")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


# ──────────────────────────────────────────────
# Movie Manager
# ──────────────────────────────────────────────

class MovieQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Movie.Status.PUBLISHED)

    def premium(self):
        return self.filter(is_premium=True)

    def free(self):
        return self.filter(is_premium=False)

    def with_relations(self):
        return self.prefetch_related(
            "genres",
            "languages",
            "cast",           # ← to'g'ri
            "movie_cast",     # ← cast members uchun
            "movie_cast__person",  # ← person ma'lumotlari uchun
        ).select_related("primary_language")

    def by_year(self, year: int):
        return self.filter(release_year=year)

    def top_rated(self, min_rating: float = 7.0):
        return self.filter(
            average_rating__gte=min_rating,
            rating_count__gte=10,
        ).order_by("-average_rating")


class MovieManager(models.Manager):
    def get_queryset(self) -> MovieQuerySet:
        return MovieQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def with_relations(self):
        return self.get_queryset().with_relations()


# ──────────────────────────────────────────────
# Movie
# ──────────────────────────────────────────────

class Movie(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    class AgeRating(models.TextChoices):
        ALL = "all", _("Umumiy")
        PG_12 = "12+", _("12+")
        PG_16 = "16+", _("16+")
        PG_18 = "18+", _("18+")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("title"), max_length=255)
    title_original = models.CharField(_("original title"), max_length=255, blank=True)
    slug = models.SlugField(_("slug"), max_length=280, unique=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    tagline = models.CharField(_("tagline"), max_length=300, blank=True)

    # Classification
    genres = models.ManyToManyField(Genre, verbose_name=_("genres"), blank=True)
    cast = models.ManyToManyField(
        Person,
        through="MovieCast",
        verbose_name=_("cast"),
        blank=True,
    )
    languages = models.ManyToManyField(Language, verbose_name=_("languages"), blank=True)
    primary_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="primary_movies",
        verbose_name=_("primary language"),
    )

    # Media
    poster = models.ImageField(
        _("poster"), upload_to=movie_poster_path,
        null=True, blank=True,
    )
    backdrop = models.ImageField(
        _("backdrop"), upload_to=movie_poster_path,
        null=True, blank=True,
    )
    trailer_url = models.URLField(_("trailer URL"), blank=True)
    youtube_url = models.URLField(_("YouTube URL"), blank=True, help_text="YouTube video URL (embed uchun)")

    # Details
    release_year = models.PositiveSmallIntegerField(
        _("release year"),
        validators=[MinValueValidator(1888), MaxValueValidator(2100)],
        db_index=True,
    )
    duration_minutes = models.PositiveSmallIntegerField(
        _("duration (minutes)"),
        null=True, blank=True,
    )
    country = models.CharField(_("country"), max_length=100, blank=True)
    age_rating = models.CharField(
        _("age rating"),
        max_length=5,
        choices=AgeRating.choices,
        default=AgeRating.ALL,
    )

    # Monetization
    is_premium = models.BooleanField(_("premium content"), default=False, db_index=True)

    # Status
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)

    # Denormalized stats — updated via signals
    average_rating = models.DecimalField(
        _("average rating"),
        max_digits=3, decimal_places=1,
        default=0.0,
        db_index=True,
    )
    rating_count = models.PositiveIntegerField(_("rating count"), default=0)
    view_count = models.PositiveIntegerField(_("view count"), default=0)

    objects = MovieManager()

    class Meta:
        verbose_name = _("movie")
        verbose_name_plural = _("movies")
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "is_premium"]),
            models.Index(fields=["release_year", "status"]),
            models.Index(fields=["average_rating", "rating_count"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.release_year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.release_year}")
            slug = base_slug
            counter = 1
            while Movie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def duration_display(self) -> str:
        if not self.duration_minutes:
            return ""
        hours, minutes = divmod(self.duration_minutes, 60)
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"


# ──────────────────────────────────────────────
# MovieCast (through model)
# ──────────────────────────────────────────────

class MovieCast(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="movie_cast")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="movie_roles")
    character_name = models.CharField(_("character name"), max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(_("order"), default=0)

    class Meta:
        verbose_name = _("cast member")
        verbose_name_plural = _("cast members")
        ordering = ["order"]
        unique_together = [("movie", "person")]

    def __str__(self) -> str:
        return f"{self.person.full_name} → {self.movie.title}"


# ──────────────────────────────────────────────
# MovieFile (HLS video files)
# ──────────────────────────────────────────────

class MovieFile(TimeStampedModel):
    class Quality(models.TextChoices):
        Q_360P = "360p", "360p"
        Q_720P = "720p", "720p"
        Q_1080P = "1080p", "1080p"
        Q_4K = "4k", "4K"

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        READY = "ready", _("Ready")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="video_files",
        verbose_name=_("movie"),
    )
    quality = models.CharField(
        _("quality"), max_length=10,
        choices=Quality.choices,
    )
    file_key = models.CharField(
        _("MinIO file key"), max_length=500,
        help_text="MinIO bucket ichidagi fayl yo'li",
    )
    # Master playlist for HLS
    hls_playlist_key = models.CharField(
        _("HLS playlist key"), max_length=500,
        blank=True,
    )
    duration_seconds = models.PositiveIntegerField(
        _("duration (seconds)"), null=True, blank=True,
    )
    file_size_bytes = models.BigIntegerField(
        _("file size (bytes)"), null=True, blank=True,
    )
    status = models.CharField(
        _("status"), max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    processing_error = models.TextField(_("processing error"), blank=True)

    class Meta:
        verbose_name = _("movie file")
        verbose_name_plural = _("movie files")
        unique_together = [("movie", "quality")]
        ordering = ["quality"]

    def __str__(self) -> str:
        return f"{self.movie.title} — {self.quality}"


# ──────────────────────────────────────────────
# Subtitle
# ──────────────────────────────────────────────

class Subtitle(TimeStampedModel):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE,
        related_name="subtitles",
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE,
        related_name="subtitles",
    )
    file_key = models.CharField(_("subtitle file key"), max_length=500)
    is_auto_generated = models.BooleanField(_("auto generated"), default=False)

    class Meta:
        verbose_name = _("subtitle")
        verbose_name_plural = _("subtitles")
        unique_together = [("movie", "language")]

    def __str__(self) -> str:
        return f"{self.movie.title} — {self.language.name}"
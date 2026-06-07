import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from django.db import models


from .models import Review, ReviewLike

logger = logging.getLogger(__name__)


def _recalculate_movie_rating(movie) -> None:
    """Recalculate denormalized rating fields on Movie."""
    result = Review.objects.filter(
        movie=movie, is_active=True
    ).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )
    movie.average_rating = round(result["avg"] or 0.0, 1)
    movie.rating_count = result["count"] or 0
    movie.save(update_fields=["average_rating", "rating_count"])
    logger.info(
        "Movie rating updated: %s → %.1f (%d reviews)",
        movie.title,
        movie.average_rating,
        movie.rating_count,
    )


@receiver(post_save, sender=Review)
def on_review_save(sender, instance: Review, **kwargs) -> None:
    _recalculate_movie_rating(instance.movie)


@receiver(post_delete, sender=Review)
def on_review_delete(sender, instance: Review, **kwargs) -> None:
    _recalculate_movie_rating(instance.movie)


@receiver(post_save, sender=ReviewLike)
def on_like_save(sender, instance: ReviewLike, created: bool, **kwargs) -> None:
    if created:
        Review.objects.filter(pk=instance.review_id).update(
            like_count=models.F("like_count") + 1
        )


@receiver(post_delete, sender=ReviewLike)
def on_like_delete(sender, instance: ReviewLike, **kwargs) -> None:
    Review.objects.filter(pk=instance.review_id).update(
        like_count=models.F("like_count") - 1
    )
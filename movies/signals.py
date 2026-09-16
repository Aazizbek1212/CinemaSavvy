import logging

from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def update_movie_rating(movie) -> None:
    """Recalculate and save denormalized rating fields."""
    from reviews.models import Review
    result = Review.objects.filter(
        movie=movie, is_active=True
    ).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )
    movie.average_rating = round(result["avg"] or 0, 1)
    movie.rating_count = result["count"] or 0
    movie.save(update_fields=["average_rating", "rating_count"])
    logger.info("Rating updated for movie: %s → %.1f (%d)", movie.title, movie.average_rating, movie.rating_count)


@receiver(post_save, sender="reviews.Review")
@receiver(post_delete, sender="reviews.Review")
def review_changed(sender, instance, **kwargs):
    """Signal receiver: har safar Review yaratilganda/o'zgartirilganda/o'chirilganda chaqiriladi."""
    update_movie_rating(instance.movie)
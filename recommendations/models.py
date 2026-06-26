from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Recommendation(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recommendations"
    )

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    reason = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-score"]
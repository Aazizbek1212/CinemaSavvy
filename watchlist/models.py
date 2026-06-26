from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Watchlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist_items"
    )

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE,
        related_name="watchlisted_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "movie")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} -> {self.movie.title}"
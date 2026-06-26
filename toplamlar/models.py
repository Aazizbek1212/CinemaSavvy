from django.db import models
from django.utils.text import slugify


class Collection(models.Model):
    title = models.CharField(max_length=255)

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    description = models.TextField(blank=True)

    cover = models.ImageField(
        upload_to="collections/",
        blank=True,
        null=True
    )

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args,**kwargs)

    def __str__(self):
        return self.title
class CollectionMovie(models.Model):

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="collection_movies"
    )

    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.CASCADE
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [
            ("collection","movie")
        ]

        ordering = ["order"]
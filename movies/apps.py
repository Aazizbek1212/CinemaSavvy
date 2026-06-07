from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "movies"
    verbose_name = "Movies"

    def ready(self):
        import movies.signals  # noqa
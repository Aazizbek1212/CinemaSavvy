from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "search"
    verbose_name = "Search"

    def ready(self):
        import contextlib

        with contextlib.suppress(Exception):
            import search.documents  # noqa
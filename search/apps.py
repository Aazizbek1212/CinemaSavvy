from django.apps import AppConfig

class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "search"
    verbose_name = "Search"

    def ready(self):
        try:
            import search.documents  # noqa
        except Exception:
            pass  # Elasticsearch yo'q bo'lsa ham ishlasin
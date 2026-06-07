import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from movies.models import Movie, Person

logger = logging.getLogger(__name__)


@registry.register_document
class MovieDocument(Document):
    """
    Elasticsearch document for Movie model.
    Multi-language analyzer: uzbek, russian, english.
    """

    # Nested/related fields
    genres = fields.NestedField(properties={
        "name": fields.KeywordField(),
        "slug": fields.KeywordField(),
    })

    cast = fields.NestedField(properties={
        "full_name": fields.TextField(
            analyzer="standard",
            fields={"keyword": fields.KeywordField()},
        ),
        "slug": fields.KeywordField(),
    })

    primary_language_code = fields.KeywordField()
    language_codes = fields.KeywordField(multi=True)

    # Computed fields
    poster_url = fields.KeywordField()

    class Index:
        name = "movies"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "cinema_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "cinema_stop",
                            "cinema_synonym",
                        ],
                    },
                    "autocomplete_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding", "edge_ngram_filter"],
                    },
                    "autocomplete_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"],
                    },
                },
                "filter": {
                    "cinema_stop": {
                        "type": "stop",
                        "stopwords": ["va", "bilan", "uchun", "the", "a", "an"],
                    },
                    "cinema_synonym": {
                        "type": "synonym",
                        "synonyms": [
                            "avtar, avatar",
                            "terminator, terminetor",
                        ],
                    },
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 15,
                    },
                },
            },
        }

    class Django:
        model = Movie
        fields = [
            "id",
            "tagline",
            "release_year",
            "country",
            "age_rating",
            "is_premium",
            "average_rating",
            "rating_count",
            "view_count",
            "duration_minutes",
        ]
        queryset_pagination = 100

    # ── Custom field mappings ──────────────────

    title = fields.TextField(
        analyzer="cinema_analyzer",
        search_analyzer="cinema_analyzer",
        fields={
            "autocomplete": fields.TextField(
                analyzer="autocomplete_analyzer",
                search_analyzer="autocomplete_search_analyzer",
            ),
            "keyword": fields.KeywordField(),
            "raw": fields.KeywordField(normalizer="lowercase"),
        },
    )

    title_original = fields.TextField(
        analyzer="cinema_analyzer",
    )

    description = fields.TextField(
        analyzer="cinema_analyzer",
    )

    slug = fields.KeywordField()
    status = fields.KeywordField()
    published_at = fields.DateField()

    # ── Prepare methods ───────────────────────

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status=Movie.Status.PUBLISHED)
            .prefetch_related("genres", "cast", "languages")
            .select_related("primary_language")
        )

    def prepare_genres(self, instance: Movie) -> list[dict]:
        return [{"name": g.name, "slug": g.slug} for g in instance.genres.all()]

    def prepare_cast(self, instance: Movie) -> list[dict]:
        return [{"full_name": p.full_name, "slug": p.slug} for p in instance.cast.all()[:20]]

    def prepare_primary_language_code(self, instance: Movie) -> str:
        return instance.primary_language.code if instance.primary_language else ""

    def prepare_language_codes(self, instance: Movie) -> list[str]:
        return list(instance.languages.values_list("code", flat=True))

    def prepare_poster_url(self, instance: Movie) -> str:
        return instance.poster.url if instance.poster else ""

    def prepare_published_at(self, instance: Movie):
        return instance.published_at

    def prepare_status(self, instance: Movie) -> str:
        return instance.status


@registry.register_document
class PersonDocument(Document):
    """Elasticsearch document for Person (actors, directors)."""

    movies_count = fields.IntegerField()

    class Index:
        name = "persons"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Person
        fields = ["id", "role", "bio", "birth_place"]

    full_name = fields.TextField(
        analyzer="standard",
        fields={
            "autocomplete": fields.TextField(analyzer="standard"),
            "keyword": fields.KeywordField(),
        },
    )

    slug = fields.KeywordField()
    photo_url = fields.KeywordField()

    def prepare_movies_count(self, instance: Person) -> int:
        return instance.movie_roles.filter(movie__status="published").count()

    def prepare_photo_url(self, instance: Person) -> str:
        return instance.photo.url if instance.photo else ""

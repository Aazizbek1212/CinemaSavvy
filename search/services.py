import logging
from dataclasses import dataclass, field
from elasticsearch_dsl import Q, Search
from elasticsearch_dsl import response

from .documents import MovieDocument, PersonDocument

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    movies:      list[dict] = field(default_factory=list)
    persons:     list[dict] = field(default_factory=list)
    total:       int = 0
    took_ms:     int = 0
    suggestions: list[str] = field(default_factory=list)


class ElasticsearchService:
    """
    Centralized search service.
    Handles: full-text, autocomplete, filters, suggestions.
    """

    MAX_RESULTS    = 50
    DEFAULT_LIMIT  = 20
    AUTOCOMPLETE_LIMIT = 8

    @classmethod
    def search(
        cls,
        query: str,
        *,
        genre: str | None        = None,
        language: str | None     = None,
        year_min: int | None     = None,
        year_max: int | None     = None,
        is_premium: bool | None  = None,
        rating_min: float | None = None,
        page: int                = 1,
        limit: int               = DEFAULT_LIMIT,
    ) -> SearchResult:
        """
        Full search with filters, relevance scoring, highlights.
        """
        query = query.strip()
        if not query:
            return SearchResult()

        limit  = min(limit, cls.MAX_RESULTS)
        offset = (page - 1) * limit

        try:
            movies  = cls._search_movies(
                query, genre=genre, language=language,
                year_min=year_min, year_max=year_max,
                is_premium=is_premium, rating_min=rating_min,
                offset=offset, limit=limit,
            )
            persons = cls._search_persons(query, limit=5)

            return SearchResult(
                movies=movies["hits"],
                persons=persons,
                total=movies["total"],
                took_ms=movies["took"],
                suggestions=cls._get_suggestions(query),
            )

        except Exception as exc:
            logger.error("Elasticsearch search error: %s", exc)
            return SearchResult()

    @classmethod
    def autocomplete(cls, query: str) -> list[dict]:
        """
        Fast autocomplete for navbar search.
        Uses edge_ngram analyzer.
        """
        query = query.strip()
        if len(query) < 2:
            return []

        try:
            s = (
                MovieDocument.search()
                .query(
                    Q("multi_match",
                      query=query,
                      fields=["title.autocomplete^3", "title^2", "title_original"],
                      type="bool_prefix",
                    )
                )
                .filter("term", status="published")
                .source(["title", "slug", "release_year",
                          "poster_url", "average_rating", "is_premium"])
                [:cls.AUTOCOMPLETE_LIMIT]
            )

            response = s.execute()
            return [
                {
                    "id":             str(hit.meta.id),
                    "title":          hit.title,
                    "slug":           hit.slug,
                    "release_year":   hit.release_year,
                    "poster":         hit.poster_url,
                    "average_rating": getattr(hit, "average_rating", 0),
                    "is_premium":     getattr(hit, "is_premium", False),
                }
                for hit in response
            ]

        except Exception as exc:
            logger.error("Autocomplete error: %s", exc)
            return []

    # ── Private methods ───────────────────────────────

    @classmethod
    def _search_movies(
        cls, query: str, *,
        genre: str | None, language: str | None,
        year_min: int | None, year_max: int | None,
        is_premium: bool | None, rating_min: float | None,
        offset: int, limit: int,
    ) -> dict:

        # Multi-field relevance query
        must_query = Q(
            "multi_match",
            query=query,
            fields=[
                "title^3",
                "title.autocomplete^2",
                "title_original^2",
                "tagline^1.5",
                "description^0.5",
                "cast.full_name^1",
            ],
            type="best_fields",
            fuzziness="AUTO",          # typo tolerance
            prefix_length=2,
            operator="or",
        )

        s = (
            MovieDocument.search()
            .query(must_query)
            .filter("term", status="published")
        )

        # Filters
        if genre:
            s = s.filter("nested",
                         path="genres",
                         query=Q("term", genres__slug=genre))

        if language:
            s = s.filter("term", language_codes=language)

        if year_min or year_max:
            year_range = {}
            if year_min: year_range["gte"] = year_min
            if year_max: year_range["lte"] = year_max
            s = s.filter("range", release_year=year_range)

        if is_premium is not None:
            s = s.filter("term", is_premium=is_premium)

        if rating_min:
            s = s.filter("range", average_rating={"gte": rating_min})

        # Boost popular movies in relevance
        s = s.query(
            "function_score",
            query=s.query,
            functions=[
                {
                    "field_value_factor": {
                        "field":    "average_rating",
                        "factor":   0.1,
                        "modifier": "sqrt",
                        "missing":  0,
                    }
                },
                {
                    "field_value_factor": {
                        "field":    "view_count",
                        "factor":   0.001,
                        "modifier": "log1p",
                        "missing":  0,
                    }
                },
            ],
            score_mode="sum",
            boost_mode="multiply",
        )

        # Highlighting
        s = s.highlight(
            "title", "description",
            pre_tags=["<mark>"],
            post_tags=["</mark>"],
            number_of_fragments=1,
            fragment_size=150,
        )

        s = s[offset: offset + limit]
        response = s.execute()

        hits = []
        for hit in response:
            highlight = {}
            if hasattr(hit.meta, "highlight"):
                highlight = {
                    k: list(v)
                    for k, v in hit.meta.highlight.to_dict().items()
                }

            hits.append({
                "id":             str(hit.meta.id),
                "title":          hit.title,
                "title_original": getattr(hit, "title_original", ""),
                "slug":           hit.slug,
                "release_year":   getattr(hit, "release_year", 0),
                "poster_url":     getattr(hit, "poster_url", ""),
                "average_rating": float(getattr(hit, "average_rating", 0)),
                "is_premium":     getattr(hit, "is_premium", False),
                "genres":         list(getattr(hit, "genres", [])),
                "duration_minutes": getattr(hit, "duration_minutes", None),
                "score":          float(hit.meta.score),
                "highlight":      highlight,
            })

        return {
            "hits":  hits,
            "total": response.hits.total.value,
            "took":  response.took,
        }

    @classmethod
    def _search_persons(cls, query: str, limit: int = 5) -> list[dict]:
        try:
            s = (
                PersonDocument.search()
                .query(
                    Q("match", full_name={
                        "query": query,
                        "fuzziness": "AUTO",
                        "prefix_length": 1,
                    })
                )
                [:limit]
            )
            response = s.execute()
            return [
                {
                    "id":           str(hit.meta.id),
                    "full_name":    hit.full_name,
                    "slug":         hit.slug,
                    "role":         getattr(hit, "role", ""),
                    "photo_url":    getattr(hit, "photo_url", ""),
                    "movies_count": getattr(hit, "movies_count", 0),
                }
                for hit in response
            ]
        except Exception as exc:
            logger.error("Person search error: %s", exc)
            return []

    @classmethod
    def _get_suggestions(cls, query: str) -> list[str]:
        """
        Did-you-mean suggestions using term suggester.
        """
        try:
            s = MovieDocument.search()
            s = s.suggest(
                "title_suggest",
                query,
                term={
                    "field":          "title",
                    "suggest_mode":   "missing",
                    "min_word_length": 3,
                },
            )
            response = s.execute()

            suggestions = []
            for option in response.suggest.title_suggest:
                for opt in option.options:
                    suggestions.append(opt.text)
            return suggestions[:3]

        except Exception:
            return []
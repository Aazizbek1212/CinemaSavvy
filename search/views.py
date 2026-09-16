
# Create your views here.
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.views.pages import SeoMixin

from .services import ElasticsearchService

logger = logging.getLogger(__name__)


def _safe_int(value, default=None):
    """Query parametrni xavfsiz int ga o'tkazadi. Xato bo'lsa default qaytaradi."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=None):
    """Query parametrni xavfsiz float ga o'tkazadi. Xato bo'lsa default qaytaradi."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class SearchAPIView(APIView):
    """
    GET /api/search/?q=&genre=&year_min=&year_max=&page=
    Full search with filters.
    """
    permission_classes = (AllowAny,)
    throttle_scope = "search"

    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {"detail": "Qidiruv so'rovi bo'sh."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) > 200:
            return Response(
                {"detail": "So'rov juda uzun."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        p = request.query_params
        result = ElasticsearchService.search(
            query=query,
            genre=p.get("genre") or None,
            language=p.get("language") or None,
            year_min=_safe_int(p.get("year_min")),
            year_max=_safe_int(p.get("year_max")),
            is_premium=(
                True  if p.get("is_premium") == "true"  else
                False if p.get("is_premium") == "false" else
                None
            ),
            rating_min=_safe_float(p.get("rating_min")),
            page=_safe_int(p.get("page"), default=1),
            limit=_safe_int(p.get("limit"), default=20),
        )

        return Response({
            "query":       query,
            "total":       result.total,
            "took_ms":     result.took_ms,
            "movies":      result.movies,
            "persons":     result.persons,
            "suggestions": result.suggestions,
        })


class AutocompleteAPIView(APIView):
    """
    GET /api/search/autocomplete/?q=
    Fast navbar autocomplete — cached 60s.
    """
    permission_classes = (AllowAny,)

    @method_decorator(cache_page(60))
    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response({"results": []})

        results = ElasticsearchService.autocomplete(query)
        return Response({"results": results})


class SearchPageView(SeoMixin, TemplateView):
    """
    GET /search/?q=
    Full search results page.
    """
    template_name = "pages/search.html"
    seo_title     = "Qidirish — Cinema.uz"

    def get_context_data(self, **kwargs):
        ctx   = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()

        result = None
        if query:
            p = self.request.GET
            result = ElasticsearchService.search(
                query=query,
                genre=p.get("genre") or None,
                language=p.get("language") or None,
            )

        ctx.update({
            "query":        query,
            "result":       result,
            "search_query": query,
        })
        return ctx
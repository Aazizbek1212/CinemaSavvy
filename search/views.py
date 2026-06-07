from django.shortcuts import render

# Create your views here.
import logging
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .services import ElasticsearchService
from .serializers import SearchResponseSerializer
from movies.views.pages import SeoMixin

logger = logging.getLogger(__name__)


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
            year_min=int(p["year_min"]) if p.get("year_min", "").isdigit() else None,
            year_max=int(p["year_max"]) if p.get("year_max", "").isdigit() else None,
            is_premium=(
                True  if p.get("is_premium") == "true"  else
                False if p.get("is_premium") == "false" else
                None
            ),
            rating_min=float(p["rating_min"]) if p.get("rating_min") else None,
            page=int(p.get("page", 1)),
            limit=int(p.get("limit", 20)),
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
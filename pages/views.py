from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


def error_400(request, exception=None):
    return render(request, "errors/400.html", status=400)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)

class HomeAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = {
            "featured_movie": {},
            "continue_watching": [],
            "trending": [],
            "recommended": [],
            "collections": [],
            "top10": [],
        }

        return Response(data)
# utils/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "error": response.data,
            "status_code": response.status_code,
        }
    return response


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context) -> Response | None:
    response = exception_handler(exc, context)

    if response is not None:
        view = context.get("view")
        logger.warning(
            "API error %s in %s: %s",
            response.status_code,
            view.__class__.__name__ if view else "unknown",
            response.data,
        )
        response.data = {
            "success": False,
            "status_code": response.status_code,
            "error": response.data,
        }

    return response
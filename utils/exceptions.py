# utils/exceptions.py
import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

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
"""The one blessed error shape: RFC 9457 application/problem+json (docs/conventions.md).

Body: type, title, status, code (machine code), detail (Turkish user message) and, for
validation errors, errors (field -> messages). Nothing internal ever leaks: unexpected
exceptions are logged and answered with a generic 500.
"""

import logging
from http import HTTPStatus
from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"


def problem(status_code: int, code: str, detail: str, errors: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": status_code,
        "code": code,
        "detail": detail,
    }
    if errors is not None:
        body["errors"] = errors
    return body


def problem_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    response = exception_handler(exc, context)
    if response is None:
        logger.error("unhandled API error", exc_info=exc)
        response = Response(
            problem(500, "server_error", "Beklenmeyen bir hata oluştu."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    elif isinstance(exc, ValidationError):
        response.data = problem(
            response.status_code,
            "validation_error",
            "Gönderilen bilgiler geçersiz.",
            errors=response.data,
        )
    elif isinstance(exc, APIException):
        codes = exc.get_codes()
        response.data = problem(
            response.status_code,
            codes if isinstance(codes, str) else exc.default_code,
            str(exc.detail),
        )
    response.content_type = PROBLEM_CONTENT_TYPE
    return response

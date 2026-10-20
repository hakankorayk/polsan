"""Session authentication whose CSRF failure has the documented shape: code `csrf_failed` and a
Turkish message (docs/conventions.md), like the login endpoint's own check (review L2)."""

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.request import Request


class CsrfFailedAPIError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "csrf_failed"
    default_detail = "Güvenlik doğrulaması başarısız. Lütfen sayfayı yenileyin."


class CsrfAwareSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request: Request) -> None:
        try:
            super().enforce_csrf(request)
        except PermissionDenied as error:
            raise CsrfFailedAPIError from error

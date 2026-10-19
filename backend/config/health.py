"""Public health check: reports only whether the server and its database are reachable.

The single endpoint that is deliberately open (docs/security.md, default deny). The response
never carries versions, environment, personal data or error details (spec 0001, AC-5/AC-6).
"""

import logging

from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.ChoiceField(choices=["ok", "unavailable"])


class HealthView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []  # public: no session, no CSRF
    permission_classes: list[type[BasePermission]] = [AllowAny]

    @extend_schema(
        operation_id="health_retrieve",
        responses={200: HealthSerializer, 503: HealthSerializer},
        auth=[],
    )
    def get(self, request: Request) -> Response:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError:
            logger.warning("health check: database unavailable", exc_info=True)
            return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"status": "ok"})

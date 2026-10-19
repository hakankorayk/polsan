"""Test-only URLconf: a view that declares no permissions, to prove the default is deny."""

from django.urls import path
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class UndeclaredView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"secret": "should never be visible"})


urlpatterns = [path("api/undeclared/", UndeclaredView.as_view())]

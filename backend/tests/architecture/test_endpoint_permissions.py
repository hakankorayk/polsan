"""AC-7: every endpoint declares its permissions explicitly (default deny otherwise)."""

from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from tests.architecture.checks import undeclared_permission_violations


def _routes(
    patterns: list[URLPattern | URLResolver], prefix: str = ""
) -> list[tuple[str, type | None]]:
    routes: list[tuple[str, type | None]] = []
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            routes += _routes(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            routes.append((prefix + str(pattern.pattern), getattr(pattern.callback, "cls", None)))
    return routes


def test_every_endpoint_declares_permissions() -> None:
    routes = _routes(get_resolver().url_patterns)

    assert routes, "no routes found — the check would pass vacuously"
    assert undeclared_permission_violations(routes) == []


class _Declared(APIView):
    permission_classes = [IsAuthenticated]


class _InheritsDeclared(_Declared):
    pass


class _Undeclared(APIView):
    pass


class _ExplicitlyOpen(APIView):
    permission_classes = [AllowAny]


class _EmptyPermissions(APIView):
    permission_classes = []


def test_checker_flags_undeclared_view() -> None:
    routes: list[tuple[str, type | None]] = [
        ("api/a/", _Declared),
        ("api/b/", _InheritsDeclared),
        ("api/c/", _Undeclared),
        ("plain/", None),
        ("api/open/", _ExplicitlyOpen),
        ("api/empty/", _EmptyPermissions),
    ]

    assert undeclared_permission_violations(routes) == [
        "api/c/: _Undeclared declares no permission_classes",
        "plain/: not a DRF view, permissions cannot be enforced",
        "api/empty/: _EmptyPermissions declares empty permission_classes "
        "(open access must be an explicit AllowAny)",
    ]

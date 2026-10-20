"""AC-7 (spec 0001): every endpoint declares its permissions explicitly (default deny otherwise).
Spec 0002 adds the admin site: its routes are not DRF views, so they must all belong to the
HR-only HRAdminSite, which enforces access itself (spec 0002, AC-5)."""

from django.contrib.admin import AdminSite
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from config.admin import HRAdminSite, hr_admin_site
from tests.architecture.checks import undeclared_permission_violations


def _routes(
    patterns: list[URLPattern | URLResolver], prefix: str = ""
) -> tuple[list[tuple[str, type | None]], list[str]]:
    """(API routes with their DRF view class, routes owned by the HR admin site)."""
    routes: list[tuple[str, type | None]] = []
    admin_routes: list[str] = []
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver) and pattern.namespace == hr_admin_site.name:
            admin_routes.append(route)
        elif isinstance(pattern, URLResolver):
            nested, nested_admin = _routes(pattern.url_patterns, route)
            routes += nested
            admin_routes += nested_admin
        else:
            routes.append((route, getattr(pattern.callback, "cls", None)))
    return routes, admin_routes


def test_every_endpoint_declares_permissions() -> None:
    routes, _ = _routes(get_resolver().url_patterns)

    assert routes, "no routes found — the check would pass vacuously"
    assert undeclared_permission_violations(routes) == []


def test_admin_routes_belong_to_the_hr_only_site() -> None:
    _, admin_routes = _routes(get_resolver().url_patterns)

    assert admin_routes == ["admin/"]
    assert isinstance(hr_admin_site, HRAdminSite)
    assert HRAdminSite.has_permission is not AdminSite.has_permission  # HR-only check in place


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

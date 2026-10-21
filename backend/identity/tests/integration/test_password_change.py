"""Spec 0002 — AC-10, AC-11: a temporary password unlocks only the password change."""

import pytest
from django.urls import get_resolver

from identity.tests.integration.conftest import NEW_PASSWORD, PASSWORD, log_in

OPEN_ROUTES = {"api/health/", "api/auth/csrf/", "api/auth/login/"}
CHANGE_ROUTES = {"api/auth/password/", "api/auth/logout/"}


def _api_routes() -> list[str]:
    routes = []
    for pattern in get_resolver().url_patterns:
        nested = getattr(pattern, "url_patterns", None)
        for p in nested if nested is not None else [pattern]:
            route = str(getattr(pattern, "pattern", "")) if nested is not None else ""
            routes.append(route + str(p.pattern))
    return [r for r in routes if r.startswith("api/")]


def _change(client, new: str = NEW_PASSWORD, confirm: str | None = None):  # noqa: ANN202
    return client.post(
        "/api/auth/password/",
        {"new_password": new, "new_password_confirm": new if confirm is None else confirm},
        format="json",
    )


def test_temporary_password_blocks_every_other_endpoint(client, make_user) -> None:
    make_user("gecici", must_change=True)
    login = log_in(client, "gecici")
    protected = [r for r in _api_routes() if r not in OPEN_ROUTES | CHANGE_ROUTES]

    assert login.json() == {"must_change_password": True}
    assert protected, "no protected routes found — the test would pass vacuously"
    for route in protected:
        response = client.get("/" + route)
        assert response.status_code == 403, route
        assert response.json()["code"] == "password_change_required", route


@pytest.mark.parametrize(
    ("new", "confirm", "field"),
    [
        ("Kisa-1!", None, "new_password"),  # shorter than 12
        ("password1234", None, "new_password"),  # too common
        ("123456789012345", None, "new_password"),  # digits only
        (PASSWORD, None, "new_password"),  # same as the temporary password
        (NEW_PASSWORD, "Baska-Parola-2028!", "new_password_confirm"),  # mismatch
    ],
)
def test_invalid_new_passwords_rejected_per_field(client, make_user, new, confirm, field) -> None:
    user = make_user("gecici", must_change=True)
    log_in(client, "gecici")

    response = _change(client, new, confirm)

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert field in response.json()["errors"]
    user.refresh_from_db()
    assert user.must_change_password
    assert user.check_password(PASSWORD)


def test_valid_change_reaches_home_and_new_password_works(client, make_user) -> None:
    make_user("gecici", must_change=True)
    log_in(client, "gecici")

    change = _change(client)
    me = client.get("/api/me/")
    client.post("/api/auth/logout/")
    old = log_in(client, "gecici", PASSWORD)
    new = log_in(client, "gecici", NEW_PASSWORD)

    assert change.status_code == 204
    assert me.status_code == 200
    assert old.status_code == 400
    assert new.json() == {"must_change_password": False}


def test_change_refused_without_temporary_password(client, make_user) -> None:
    make_user("kalici")
    log_in(client, "kalici")

    response = _change(client)

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_not_required"

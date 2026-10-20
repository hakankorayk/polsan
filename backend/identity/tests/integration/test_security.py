"""Spec 0002 — AC-18, AC-19, AC-20: anonymous access, CSRF, cookie flags, password storage."""

import logging

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from identity.models import User
from identity.tests.integration.conftest import NEW_PASSWORD, PASSWORD, log_in

PROTECTED = [
    ("get", "/api/me/"),
    ("post", "/api/auth/logout/"),
    ("post", "/api/auth/password/"),
]


@pytest.mark.parametrize(("method", "route"), PROTECTED)
def test_anonymous_rejected_on_every_protected_endpoint(db, method: str, route: str) -> None:
    response = getattr(APIClient(), method)(route)

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


def test_health_still_public(db) -> None:
    assert APIClient().get("/api/health/").status_code == 200


def test_login_and_password_require_csrf(make_user) -> None:
    make_user("gecici", must_change=True)
    client = APIClient(enforce_csrf_checks=True)

    without_token = log_in(client, "gecici")
    client.get("/api/auth/csrf/")
    token = client.cookies["csrftoken"].value
    with_token = client.post(
        "/api/auth/login/",
        {"username": "gecici", "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    change_without_token = client.post(
        "/api/auth/password/",
        {"new_password": NEW_PASSWORD, "new_password_confirm": NEW_PASSWORD},
        format="json",
    )

    assert without_token.status_code == 403
    assert without_token.json()["code"] == "csrf_failed"
    assert with_token.status_code == 200
    assert change_without_token.status_code == 403


def test_session_cookie_flags(client, make_user) -> None:
    make_user("ayilmaz")

    log_in(client, "ayilmaz")
    cookie = client.cookies["sessionid"]

    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.Argon2PasswordHasher"])
def test_password_stored_as_argon2(make_user) -> None:
    user = make_user("ayilmaz")

    stored = User.objects.get(pk=user.pk).password

    assert stored.startswith("argon2$")
    assert PASSWORD not in stored


def test_no_secret_in_responses_or_logs(client, make_user, caplog) -> None:
    make_user("gecici", must_change=True)
    caplog.set_level(logging.DEBUG)

    responses = [
        log_in(client, "gecici", "yanlis-parola-123"),
        log_in(client, "gecici"),
        client.post(
            "/api/auth/password/",
            {"new_password": NEW_PASSWORD, "new_password_confirm": NEW_PASSWORD},
            format="json",
        ),
        client.get("/api/me/"),
    ]
    session_key = client.cookies["sessionid"].value

    for secret in (PASSWORD, NEW_PASSWORD, "yanlis-parola-123", session_key):
        assert secret not in caplog.text
        for response in responses:
            assert secret not in response.content.decode()

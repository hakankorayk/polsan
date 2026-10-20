"""Factories for the identity integration tests (real PostgreSQL via Testcontainers)."""

from collections.abc import Callable

import pytest
from rest_framework.test import APIClient

from identity.models import User
from tests.factories import create_employee

PASSWORD = "Guclu-Parola-2026!"
NEW_PASSWORD = "Yepyeni-Parola-2027?"


@pytest.fixture
def make_employee(db: None) -> Callable[..., object]:
    return create_employee


@pytest.fixture
def make_user(make_employee: Callable[..., object]) -> Callable[..., User]:
    def make(
        username: str = "ayilmaz",
        *,
        employee: object | None = None,
        password: str = PASSWORD,
        must_change: bool = False,
        is_hr: bool = False,
        active: bool = True,
    ) -> User:
        return User.objects.create_user(
            username,
            password,
            employee=employee or make_employee(),
            must_change_password=must_change,
            is_hr=is_hr,
            is_active=active,
        )

    return make


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def log_in(client: APIClient, username: str, password: str = PASSWORD):  # noqa: ANN201
    return client.post(
        "/api/auth/login/", {"username": username, "password": password}, format="json"
    )

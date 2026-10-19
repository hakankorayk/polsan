"""AC-5, AC-6, AC-7: the health endpoint and the default-deny rule (no database needed)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from django.db import OperationalError
from rest_framework.test import APIClient

import config.health


class _OkCursor:
    def execute(self, sql: str) -> None:
        assert sql == "SELECT 1"


@contextmanager
def _ok_cursor() -> Iterator[_OkCursor]:
    yield _OkCursor()


def _failing_cursor() -> Any:
    raise OperationalError(
        'connection to server at "10.0.0.5", port 5432 failed: database "leave_manager" missing'
    )


def test_anonymous_allowed_and_body_is_status_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config.health.connection, "cursor", _ok_cursor)

    response = APIClient().get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_down_returns_503_without_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config.health.connection, "cursor", _failing_cursor)

    response = APIClient().get("/api/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    body = response.content.decode()
    for leaked in ("10.0.0.5", "5432", "leave_manager", "connection"):
        assert leaked not in body


@pytest.mark.urls("tests.unit.urls_protected")
def test_default_permission_rejects_anonymous() -> None:
    response = APIClient().get("/api/undeclared/")

    assert response.status_code in (401, 403)
    assert "should never be visible" not in response.content.decode()

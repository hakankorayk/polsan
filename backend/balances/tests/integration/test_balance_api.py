"""Spec 0003 — the employee's own balance: AC-3, AC-22, AC-23, AC-24, AC-26, AC-29."""

import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from balances import clock
from balances.api import add_adjustment, set_start_date
from balances.tests.integration.conftest import BORN, HIRE, D
from tests.factories import Employee, create_employee

TODAY = D(2026, 10, 21)
PASSWORD = "Guclu-Parola-2026!"


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clock, "today", lambda: TODAY)


def _client_for(employee: Employee, username: str = "edemir", must_change: bool = False):  # noqa: ANN202
    user = get_user_model().objects.create_user(
        username, PASSWORD, employee=employee, must_change_password=must_change
    )
    client = APIClient()
    client.force_login(user)
    return client


def test_summary_balance_and_next_accrual(started: None, employee: Employee) -> None:
    add_adjustment(employee.pk, Decimal("-1.5"), "Eski sistemden kullanım", uuid.uuid4(), TODAY)

    body = _client_for(employee).get("/api/balance/").json()

    # Hired 2020-03-10: years 1-5 x 14 + year 6 x 20 = 90, minus 1.5.
    assert body["balance"] == "88.5"
    assert body["next_accrual"] == {"date": "2027-03-10", "days": "20.0"}


def test_no_next_accrual_before_start_or_without_start(employee: Employee) -> None:
    client = _client_for(employee)
    without_start = client.get("/api/balance/").json()
    set_start_date(D(2027, 3, 11))  # after the next anniversary
    before_start = client.get("/api/balance/").json()

    assert without_start["next_accrual"] is None
    assert before_start["next_accrual"] is None


def test_entries_newest_first_with_kind_and_reason(started: None, employee: Employee) -> None:
    add_adjustment(employee.pk, Decimal(3), "Açılış bakiyesi", uuid.uuid4(), TODAY)

    entries = _client_for(employee).get("/api/balance/").json()["entries"]

    assert [(e["date"], e["kind"], e["amount"], e["reason"]) for e in entries[:3]] == [
        ("2026-10-21", "ADJUSTMENT", "3.0", "Açılış bakiyesi"),
        ("2026-03-10", "ACCRUAL", "20.0", None),
        ("2025-03-10", "ACCRUAL", "14.0", None),
    ]
    assert len(entries) == 7
    assert all(uuid.UUID(e["id"]) for e in entries)


def test_empty_ledger(employee: Employee) -> None:
    body = _client_for(employee).get("/api/balance/").json()

    assert body == {"balance": "0.0", "next_accrual": None, "entries": []}


def test_response_has_no_birth_date(started: None, employee: Employee) -> None:
    body = _client_for(employee).get("/api/balance/").content.decode()

    assert "birth" not in body
    assert BORN.isoformat() not in body


def _property_names(node: object) -> set[str]:
    if isinstance(node, dict):
        names = (
            set(node.get("properties", {})) if isinstance(node.get("properties"), dict) else set()
        )
        return names.union(*(_property_names(value) for value in node.values()))
    if isinstance(node, list):
        return set().union(*(_property_names(item) for item in node))
    return set()


def test_schema_has_no_birth_date() -> None:
    schema = SchemaGenerator().get_schema(request=None, public=True)
    names = _property_names(schema)

    assert {"balance", "next_accrual", "entries"} <= names  # the walk does reach the schemas
    assert not [name for name in names if "birth" in name]


def test_only_own_balance(started: None, employee: Employee) -> None:
    other = create_employee("Başka", "Kişi", hire_date=D(2015, 1, 5), birth_date=BORN)
    add_adjustment(other.pk, Decimal(7), "Başkasının düzeltmesi", uuid.uuid4(), TODAY)

    body = _client_for(employee).get("/api/balance/").content.decode()

    assert "Başkasının" not in body
    assert "2015" not in body


def test_guessed_other_employee_paths_404(employee: Employee) -> None:
    other = create_employee("Başka", "Kişi", hire_date=HIRE, birth_date=BORN)
    client = _client_for(employee)

    for route in (
        f"/api/balance/{other.public_id}/",
        f"/api/employees/{other.public_id}/balance/",
        f"/api/balances/{other.public_id}/",
    ):
        assert client.get(route).status_code == 404, route


def test_anonymous_rejected(employee: Employee) -> None:
    response = APIClient().get("/api/balance/")

    assert response.status_code in (401, 403)
    assert response.json()["code"] == "not_authenticated"


def test_password_change_required_rejected(started: None, employee: Employee) -> None:
    response = _client_for(employee, must_change=True).get("/api/balance/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"
    assert "balance" not in response.json()

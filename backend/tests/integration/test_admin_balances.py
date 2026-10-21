"""Spec 0003 through the HR admin: AC-1, AC-2, AC-11, AC-14, AC-16, AC-17, AC-19, AC-20, AC-30.

Lives outside every module: it exercises the composition root (config/admin.py), which wires
employees, identity, balances and audit together.
"""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from audit.api import records_for
from balances import clock
from balances.api import balance_of, set_start_date, start_date
from balances.models import AccrualSettings, LedgerEntry, LedgerKind
from tests.factories import Employee, create_employee

D = datetime.date
TODAY = D(2026, 10, 21)
PASSWORD = "Guclu-Parola-2026!"


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clock, "today", lambda: TODAY)


@pytest.fixture
def hr(db: None) -> Employee:
    return create_employee("İnsan", "Kaynakları")


@pytest.fixture
def hr_client(hr: Employee) -> Client:
    user = get_user_model().objects.create_user(
        "ik", PASSWORD, employee=hr, is_hr=True, must_change_password=False
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def employee(db: None) -> Employee:
    return create_employee("Ece", "Demir", hire_date=D(2020, 3, 10), birth_date=D(1990, 1, 1))


def _employee_form(employee: Employee | None = None, **overrides: str) -> dict[str, str]:
    data = {
        "first_name": employee.first_name if employee else "Ali",
        "last_name": employee.last_name if employee else "Veli",
        "hire_date": (employee.hire_date if employee else D(2021, 3, 15)).isoformat(),
        "birth_date": (employee.birth_date if employee else D(1990, 4, 23)).isoformat(),
        "manager": "",
    }
    active = overrides.pop("is_active", "on")
    if active:
        data["is_active"] = active
    data.update(overrides)
    return data


def _errors(response, field: str) -> list[str]:  # noqa: ANN001
    return [error.code for error in response.context["adminform"].form.errors.as_data()[field]]


def test_employee_form_requires_birth_date(hr_client: Client) -> None:
    response = hr_client.post("/admin/employees/employee/add/", _employee_form(birth_date=""))

    assert response.status_code == 200
    assert _errors(response, "birth_date") == ["required"]
    assert not Employee.objects.filter(first_name="Ali").exists()


@pytest.mark.parametrize(
    ("birth_date", "code"),
    [
        ("2026-10-22", "birth_date_in_future"),
        ("2021-03-15", "birth_date_not_before_hire"),
        ("2022-01-01", "birth_date_not_before_hire"),
    ],
)
def test_employee_form_rejects_invalid_birth_date(
    hr_client: Client, monkeypatch: pytest.MonkeyPatch, birth_date: str, code: str
) -> None:
    monkeypatch.setattr("django.utils.timezone.localdate", lambda *args: TODAY)

    response = hr_client.post(
        "/admin/employees/employee/add/", _employee_form(birth_date=birth_date)
    )

    assert _errors(response, "birth_date") == [code]
    assert not Employee.objects.filter(first_name="Ali").exists()


def test_hr_adds_adjustment(hr_client: Client, hr: Employee, employee: Employee) -> None:
    response = hr_client.post(
        "/admin/balances/ledgerentry/add/",
        {"employee": employee.pk, "amount": "-2.5", "reason": "  Açılış bakiyesi düzeltmesi "},
    )

    [entry] = LedgerEntry.objects.filter(employee=employee)
    [audit] = records_for(entry.public_id)
    assert response.status_code == 302
    assert (entry.kind, entry.amount, entry.reason, entry.effective_date) == (
        LedgerKind.ADJUSTMENT,
        Decimal("-2.5"),
        "Açılış bakiyesi düzeltmesi",
        TODAY,
    )
    assert (audit.actor_id, audit.action) == (hr.public_id, "balance.adjustment")
    assert balance_of(employee.pk, TODAY) == Decimal("-2.5")


@pytest.mark.parametrize(
    ("amount", "reason", "field", "code"),
    [
        ("0", "Gerekçe", "amount", "amount_zero"),
        ("1.3", "Gerekçe", "amount", "amount_not_half_multiple"),
        ("100.5", "Gerekçe", "amount", "amount_too_large"),
        ("2", "", "reason", "reason_required"),
        ("2", "    ", "reason", "reason_required"),
    ],
)
def test_adjustment_form_field_errors(  # noqa: PLR0913
    hr_client: Client, employee: Employee, amount: str, reason: str, field: str, code: str
) -> None:
    response = hr_client.post(
        "/admin/balances/ledgerentry/add/",
        {"employee": employee.pk, "amount": amount, "reason": reason},
    )

    assert response.status_code == 200
    assert _errors(response, field) == [code]
    assert not LedgerEntry.objects.exists()


def test_ledger_entries_cannot_be_changed_or_deleted(hr_client: Client, employee: Employee) -> None:
    hr_client.post(
        "/admin/balances/ledgerentry/add/",
        {"employee": employee.pk, "amount": "3", "reason": "Açılış"},
    )
    entry = LedgerEntry.objects.get()
    base = f"/admin/balances/ledgerentry/{entry.pk}"

    view = hr_client.get(f"{base}/change/")
    change = hr_client.post(
        f"{base}/change/", {"employee": employee.pk, "amount": "50", "reason": "Değişti"}
    )
    delete = hr_client.post(f"{base}/delete/", {"post": "yes"})
    bulk = hr_client.post(
        "/admin/balances/ledgerentry/",
        {"action": "delete_selected", "_selected_action": [entry.pk], "post": "yes"},
    )

    assert view.status_code == 200
    assert 'name="_save"' not in view.content.decode()  # read-only view, no save button
    assert change.status_code == 403
    assert delete.status_code == 403
    assert bulk.status_code in (200, 302)
    entry.refresh_from_db()
    assert (entry.amount, entry.reason) == (Decimal(3), "Açılış")
    assert LedgerEntry.objects.count() == 1


def test_hr_sees_balance_and_filters_entries(hr_client: Client, employee: Employee) -> None:
    set_start_date(D(2020, 1, 1))
    other = create_employee("Mehmet", "Çelik", hire_date=D(2024, 1, 15))

    page = hr_client.get(f"/admin/employees/employee/{employee.pk}/change/").content.decode()
    filtered = hr_client.get(f"/admin/balances/ledgerentry/?employee__id__exact={employee.pk}")
    shown = list(filtered.context["cl"].result_list)

    assert "Bakiye" in page
    assert "90 gün" in page  # 5 x 14 + 20
    assert len(shown) == 6
    assert {entry.employee_id for entry in shown} == {employee.pk}
    assert balance_of(other.pk, TODAY) == Decimal(28)  # the other employee is still separate


def test_start_date_form_locked(hr_client: Client, employee: Employee) -> None:
    created = hr_client.post("/admin/balances/accrualsettings/add/", {"start_date": "2030-01-01"})
    url = f"/admin/balances/accrualsettings/{AccrualSettings.objects.get().pk}/change/"
    changed = hr_client.post(url, {"start_date": "2024-01-01"})
    balance_of(employee.pk, TODAY)  # first automatic accruals (2024, 2025, 2026)

    locked = hr_client.post(url, {"start_date": "2025-01-01"})

    assert created.status_code == 302
    assert changed.status_code == 302
    assert locked.status_code == 200
    assert _errors(locked, "start_date") == ["accrual_start_locked"]
    assert start_date() == D(2024, 1, 1)
    assert hr_client.get("/admin/balances/accrualsettings/add/").status_code == 403  # one row


def test_admin_reactivation_does_not_backfill(hr_client: Client, employee: Employee) -> None:
    set_start_date(D(2020, 1, 1))
    url = f"/admin/employees/employee/{employee.pk}/change/"

    hr_client.post(url, _employee_form(employee, is_active=""))  # deactivated on 2026-10-21
    years = LedgerEntry.objects.filter(employee=employee).values_list("seniority_year", flat=True)
    years_at_deactivation = sorted(year for year in years if year is not None)
    hr_client.post(url, _employee_form(employee))  # reactivated the same day
    employee.refresh_from_db()

    assert years_at_deactivation == [1, 2, 3, 4, 5, 6]
    assert employee.is_active
    assert balance_of(employee.pk, TODAY) == Decimal(90)


def test_admin_created_employee_accrues_from_creation_day(
    hr_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-34 (review M3): HR adds on 2026-10-21 an employee hired years ago. The 2026-05-01
    anniversary predates the record (HR's opening adjustment covers it); 2027-05-01 accrues."""
    set_start_date(D(2026, 1, 1))
    hr_client.post(
        "/admin/employees/employee/add/",
        _employee_form(first_name="Geç", last_name="Kayıt", hire_date="2012-05-01"),
    )
    late = Employee.objects.get(first_name="Geç")

    on_creation = balance_of(late.pk, TODAY)
    monkeypatch.setattr(clock, "today", lambda: D(2027, 5, 1))
    next_year = balance_of(late.pk, D(2027, 5, 1))

    assert on_creation == Decimal(0)
    assert next_year == Decimal(26)  # the 15th anniversary


def test_admin_missed_anniversary_while_inactive_is_not_backfilled(
    hr_client: Client, employee: Employee, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-14 through the admin (review L5): the 2026-03-10 anniversary passes while the employee
    is inactive; reactivating on 2026-06-01 does not add it, the next one accrues normally."""
    set_start_date(D(2020, 1, 1))
    url = f"/admin/employees/employee/{employee.pk}/change/"

    monkeypatch.setattr(clock, "today", lambda: D(2026, 1, 1))
    hr_client.post(url, _employee_form(employee, is_active=""))
    monkeypatch.setattr(clock, "today", lambda: D(2026, 6, 1))
    hr_client.post(url, _employee_form(employee))

    after_reactivation = balance_of(employee.pk, D(2026, 10, 21))
    next_anniversary = balance_of(employee.pk, D(2027, 3, 10))
    years = LedgerEntry.objects.filter(employee=employee).values_list("seniority_year", flat=True)

    assert after_reactivation == Decimal(14 * 5)  # years 1-5; year 6 (2026-03-10) missed
    assert next_anniversary == Decimal(14 * 5 + 20)
    assert sorted(year for year in years if year is not None) == [1, 2, 3, 4, 5, 7]

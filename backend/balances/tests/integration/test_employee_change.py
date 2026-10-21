"""Spec 0003 — AC-14, AC-15: deactivation, reactivation and date changes (plan 0003, risk 2)."""

import datetime
from decimal import Decimal
from typing import Any

from balances.api import (
    after_employee_change,
    balance_of,
    before_employee_change,
    set_start_date,
    summary_of,
)
from balances.models import LedgerEntry, LedgerKind
from balances.tests.integration.conftest import D
from tests.factories import Employee


def _change(employee: Employee, today: datetime.date, **fields: Any) -> None:
    """What the HR admin does around a save."""
    before = before_employee_change(employee.pk, today)
    for name, value in fields.items():
        setattr(employee, name, value)
    employee.save()
    after_employee_change(employee.pk, today, before)


def _years(employee: Employee) -> list[int]:
    return sorted(
        year
        for year in LedgerEntry.objects.filter(
            employee=employee, kind=LedgerKind.ACCRUAL
        ).values_list("seniority_year", flat=True)
        if year is not None
    )


def test_inactive_on_anniversary_no_accrual(started: None, employee: Employee) -> None:
    _change(employee, D(2021, 1, 1), is_active=False)

    assert balance_of(employee.pk, D(2021, 6, 1)) == Decimal(0)


def test_deactivation_keeps_what_was_earned_before(started: None, employee: Employee) -> None:
    _change(employee, D(2022, 6, 1), is_active=False)  # 2021 and 2022 anniversaries passed unread

    assert _years(employee) == [1, 2]


def test_reactivation_does_not_backfill(started: None, employee: Employee) -> None:
    _change(employee, D(2021, 1, 1), is_active=False)
    _change(employee, D(2021, 6, 1), is_active=True)  # missed the 2021-03-10 anniversary

    balance_of(employee.pk, D(2022, 6, 1))

    assert _years(employee) == [2]


def test_reactivation_on_anniversary_day_accrues(started: None, employee: Employee) -> None:
    _change(employee, D(2021, 1, 1), is_active=False)
    _change(employee, D(2021, 3, 10), is_active=True)

    assert balance_of(employee.pk, D(2021, 3, 10)) == Decimal(14)


def test_hire_date_change_keeps_existing_entries(started: None, employee: Employee) -> None:
    balance_of(employee.pk, D(2022, 6, 1))  # years 1, 2 on 2021-03-10 and 2022-03-10
    kept = list(
        LedgerEntry.objects.order_by("pk").values_list("seniority_year", "effective_date", "amount")
    )

    _change(employee, D(2022, 6, 1), hire_date=D(2019, 3, 10))  # now 3 completed years
    balance_of(employee.pk, D(2023, 6, 1))

    after = list(
        LedgerEntry.objects.order_by("pk").values_list("seniority_year", "effective_date", "amount")
    )
    assert after[: len(kept)] == kept
    # Year 3 (2022-03-10 under the new date) predates the change: not created, HR adjusts.
    assert _years(employee) == [1, 2, 4]


def test_birth_date_change_applies_to_next_anniversary(started: None, employee: Employee) -> None:
    balance_of(employee.pk, D(2021, 6, 1))
    _change(employee, D(2021, 6, 1), birth_date=D(1971, 1, 1))  # 51 at the next anniversary

    summary = summary_of(employee.pk, D(2022, 3, 10))

    assert [(e.amount, e.effective_date) for e in summary.entries] == [
        (Decimal(20), D(2022, 3, 10)),
        (Decimal(14), D(2021, 3, 10)),
    ]


def test_next_accrual_after_hire_date_moved_forward(started: None, employee: Employee) -> None:
    """AC-36 (review M2): the next accrual line shows the accrual that will really be made."""
    balance_of(employee.pk, D(2026, 10, 21))  # years 1-6
    _change(employee, D(2026, 10, 21), hire_date=D(2022, 3, 10))

    upcoming = summary_of(employee.pk, D(2026, 10, 21)).next_accrual
    unchanged = summary_of(employee.pk, D(2027, 3, 10)).balance
    later = summary_of(employee.pk, D(2029, 3, 10))

    assert upcoming is not None and (upcoming.date, upcoming.days) == (D(2029, 3, 10), Decimal(20))
    assert unchanged == Decimal(90)  # nothing on 2027-03-10
    assert later.balance == Decimal(110)
    assert later.entries[0].effective_date == D(2029, 3, 10)


def test_changes_before_start_date_set_no_floor(employee: Employee) -> None:
    """AC-35 (review M3): setup changes made before the start date exists set no floor."""
    _change(employee, D(2026, 10, 1), is_active=False)
    _change(employee, D(2026, 10, 2), is_active=True)
    _change(employee, D(2026, 10, 3), birth_date=D(1991, 1, 1))

    set_start_date(D(2020, 1, 1))  # in the past: applies to this employee like to everyone

    assert balance_of(employee.pk, D(2026, 10, 21)) == Decimal(90)  # years 1-6, none skipped

"""Spec 0003 — automatic accrual start date: AC-9, AC-10, AC-11."""

from decimal import Decimal

import pytest

from balances.api import (
    StartDateLockedError,
    balance_of,
    set_start_date,
    start_date,
    start_date_locked,
)
from balances.models import LedgerEntry
from balances.tests.integration.conftest import D
from tests.factories import Employee


def test_no_accrual_without_start_date(employee: Employee) -> None:
    assert balance_of(employee.pk, D(2026, 10, 21)) == Decimal(0)
    assert not LedgerEntry.objects.exists()


def test_anniversary_on_start_date_accrues(employee: Employee) -> None:
    set_start_date(D(2024, 3, 10))  # the 4th anniversary itself

    balance_of(employee.pk, D(2024, 6, 1))

    assert list(LedgerEntry.objects.values_list("seniority_year", flat=True)) == [4]


def test_start_date_changeable_before_first_accrual(employee: Employee) -> None:
    set_start_date(D(2030, 1, 1))
    balance_of(employee.pk, D(2026, 10, 21))  # nothing due yet

    set_start_date(D(2024, 1, 1))

    assert start_date() == D(2024, 1, 1)
    assert not start_date_locked()


def test_start_date_locked_after_first_accrual(employee: Employee) -> None:
    set_start_date(D(2024, 1, 1))
    balance_of(employee.pk, D(2026, 10, 21))

    with pytest.raises(StartDateLockedError):
        set_start_date(D(2025, 1, 1))
    assert start_date() == D(2024, 1, 1)
    assert start_date_locked()

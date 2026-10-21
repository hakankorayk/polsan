"""Spec 0003 — accruals appear in the ledger on reading: AC-4, AC-8, AC-12, AC-13, AC-21."""

from decimal import Decimal

from balances.api import balance_of, summary_of
from balances.models import LedgerEntry, LedgerKind
from balances.tests.integration.conftest import BORN, D
from tests.factories import Employee


def _accrual_years(employee: Employee) -> list[int | None]:
    return list(
        LedgerEntry.objects.filter(employee=employee, kind=LedgerKind.ACCRUAL)
        .order_by("seniority_year")
        .values_list("seniority_year", flat=True)
    )


def test_br3_visible_on_anniversary_not_day_before(started: None, employee: Employee) -> None:
    assert balance_of(employee.pk, D(2021, 3, 9)) == Decimal(0)
    assert balance_of(employee.pk, D(2021, 3, 10)) == Decimal(14)

    [entry] = summary_of(employee.pk, D(2021, 3, 10)).entries
    assert (entry.kind, entry.amount, entry.effective_date) == (
        LedgerKind.ACCRUAL,
        Decimal(14),
        D(2021, 3, 10),
    )


def test_feb29_accrual_on_feb28(started: None, make_employee) -> None:
    leap = make_employee("Şubat", "Yirmidokuz", hire_date=D(2020, 2, 29), birth_date=BORN)

    assert balance_of(leap.pk, D(2021, 2, 27)) == Decimal(0)
    assert balance_of(leap.pk, D(2021, 2, 28)) == Decimal(14)


def test_repeated_reads_create_one_entry(started: None, employee: Employee) -> None:
    for _ in range(3):
        balance_of(employee.pk, D(2021, 6, 1))
        summary_of(employee.pk, D(2021, 6, 1))

    assert _accrual_years(employee) == [1]
    assert balance_of(employee.pk, D(2021, 6, 1)) == Decimal(14)


def test_catch_up_creates_one_entry_per_year(started: None, employee: Employee) -> None:
    balance = balance_of(employee.pk, D(2026, 10, 21))

    assert _accrual_years(employee) == [1, 2, 3, 4, 5, 6]
    assert balance == Decimal(14 * 5 + 20)


def test_br11_balance_same_on_dec31_and_jan1(started: None, employee: Employee) -> None:
    dec31 = balance_of(employee.pk, D(2022, 12, 31))
    count = LedgerEntry.objects.count()
    jan1 = balance_of(employee.pk, D(2023, 1, 1))

    assert dec31 == jan1 == Decimal(28)
    assert LedgerEntry.objects.count() == count


def test_inactive_employee_accrues_nothing_on_read(started: None, make_employee) -> None:
    passive = make_employee("Pasif", "Akın", active=False, hire_date=D(2020, 3, 10))

    assert balance_of(passive.pk, D(2026, 10, 21)) == Decimal(0)

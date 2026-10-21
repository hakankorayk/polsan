"""Spec 0003 — AC-19: ledger entries cannot be changed or deleted (BR-12)."""

import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError

from balances.api import ImmutableEntryError, add_adjustment
from balances.models import LedgerEntry, LedgerKind
from balances.tests.integration.conftest import D
from tests.factories import Employee


@pytest.fixture
def entry(employee: Employee) -> LedgerEntry:
    add_adjustment(employee.pk, Decimal(2), "Açılış", uuid.uuid4(), D(2026, 10, 21))
    return LedgerEntry.objects.get()


def test_entry_cannot_be_changed(entry: LedgerEntry) -> None:
    entry.amount = Decimal(50)

    with pytest.raises(ImmutableEntryError):
        entry.save()
    assert LedgerEntry.objects.get().amount == Decimal(2)


def test_entry_cannot_be_deleted(entry: LedgerEntry) -> None:
    with pytest.raises(ImmutableEntryError):
        entry.delete()
    assert LedgerEntry.objects.count() == 1


def test_queryset_update_and_delete_refused(entry: LedgerEntry) -> None:
    with pytest.raises(ImmutableEntryError):
        LedgerEntry.objects.update(amount=Decimal(50))
    with pytest.raises(ImmutableEntryError):
        LedgerEntry.objects.all().delete()
    assert LedgerEntry.objects.get().amount == Decimal(2)


@pytest.mark.parametrize("amount", ["0", "1.3"])
def test_database_refuses_invalid_amounts(employee: Employee, amount: str) -> None:
    with pytest.raises(IntegrityError):
        LedgerEntry.objects.create(
            employee=employee,
            kind=LedgerKind.ADJUSTMENT,
            amount=Decimal(amount),
            effective_date=D(2026, 10, 21),
            reason="Doğrudan yazım",
        )


def test_database_refuses_second_accrual_for_a_year(employee: Employee) -> None:
    fields = {"employee": employee, "kind": LedgerKind.ACCRUAL, "amount": Decimal(14)}
    LedgerEntry.objects.create(effective_date=D(2021, 3, 10), seniority_year=1, **fields)

    with pytest.raises(IntegrityError):
        LedgerEntry.objects.create(effective_date=D(2021, 3, 11), seniority_year=1, **fields)

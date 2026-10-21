"""Spec 0003 — HR adjustments: AC-16, AC-17 (service side), AC-18, AC-20 (BR-12)."""

import datetime
import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from audit.api import records_for
from balances.api import AdjustmentError, add_adjustment, balance_of, summary_of
from balances.models import LedgerEntry, LedgerKind
from balances.tests.integration.conftest import D
from tests.factories import Employee

HR = uuid.uuid4()
TODAY = D(2026, 10, 21)


def test_br12_positive_negative_half_adjustments_change_balance(employee: Employee) -> None:
    add_adjustment(employee.pk, Decimal("12.5"), "Açılış bakiyesi", HR, TODAY)
    add_adjustment(employee.pk, Decimal("-2"), "Eski sistemde kullanılan izin", HR, TODAY)

    summary = summary_of(employee.pk, TODAY)

    assert summary.balance == Decimal("10.5")
    assert [(e.kind, e.amount, e.reason, e.effective_date) for e in summary.entries] == [
        (LedgerKind.ADJUSTMENT, Decimal("-2"), "Eski sistemde kullanılan izin", TODAY),
        (LedgerKind.ADJUSTMENT, Decimal("12.5"), "Açılış bakiyesi", TODAY),
    ]


def test_adjustment_may_make_balance_negative(employee: Employee) -> None:
    add_adjustment(employee.pk, Decimal("-3"), "Fazla verilen hak ediş düzeltmesi", HR, TODAY)

    assert balance_of(employee.pk, TODAY) == Decimal(-3)


@pytest.mark.parametrize(
    ("amount", "reason", "code"),
    [
        ("0", "Gerekçe", "amount_zero"),
        ("1.3", "Gerekçe", "amount_not_half_multiple"),
        ("100.5", "Gerekçe", "amount_too_large"),
        ("2", "   ", "reason_required"),
    ],
)
def test_invalid_adjustment_not_saved(
    employee: Employee, amount: str, reason: str, code: str
) -> None:
    with pytest.raises(AdjustmentError) as error:
        add_adjustment(employee.pk, Decimal(amount), reason, HR, TODAY)

    assert error.value.code == code
    assert not LedgerEntry.objects.exists()


def test_adjustment_writes_audit_record(employee: Employee) -> None:
    entry_id = add_adjustment(employee.pk, Decimal(5), "  Açılış bakiyesi ", HR, TODAY)

    [audit] = records_for(entry_id)

    assert (audit.actor_id, audit.action) == (HR, "balance.adjustment")
    # "when" (AC-20): stamped by the server at write time, in UTC (docs/security.md, Audit)
    assert audit.occurred_at.utcoffset() == datetime.timedelta(0)
    assert abs(timezone.now() - audit.occurred_at) < datetime.timedelta(minutes=1)
    assert audit.data == {
        "employee": str(employee.public_id),
        "amount": "5",
        "reason": "Açılış bakiyesi",
    }

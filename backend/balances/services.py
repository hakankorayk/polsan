"""Balance ledger use cases (spec 0003). Accruals are written when a balance is read (ADR 0004)."""

import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from audit.api import record
from balances.domain.accrual import Accrual, due_accruals, next_accrual
from balances.domain.amounts import validate_adjustment_amount, validate_reason
from balances.models import AccrualFloor, AccrualSettings, LedgerEntry, LedgerKind
from employees.api import EmploymentFacts, employment_facts

ADJUSTMENT_ACTION = "balance.adjustment"


class StartDateLockedError(Exception):
    code = "accrual_start_locked"
    message = "İlk otomatik hak ediş oluştuktan sonra başlangıç tarihi değiştirilemez."


class EmployeeNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class EntryView:
    public_id: uuid.UUID
    effective_date: datetime.date
    kind: str
    amount: Decimal
    reason: str


@dataclass(frozen=True)
class BalanceSummary:
    balance: Decimal
    next_accrual: Accrual | None
    entries: list[EntryView]


def start_date() -> datetime.date | None:
    settings = AccrualSettings.objects.first()
    return settings.start_date if settings else None


def start_date_locked() -> bool:
    return LedgerEntry.objects.filter(kind=LedgerKind.ACCRUAL).exists()


def set_start_date(value: datetime.date | None) -> None:
    with transaction.atomic():
        if start_date_locked() and value != start_date():
            raise StartDateLockedError(StartDateLockedError.message)
        AccrualSettings.objects.update_or_create(key=1, defaults={"start_date": value})


def _floor(employee_id: int) -> datetime.date | None:
    return (
        AccrualFloor.objects.filter(employee_id=employee_id).values_list("floor", flat=True).first()
    )


def materialize_accruals(employee_id: int, today: datetime.date) -> None:
    """Write the accruals due by ``today`` that the ledger lacks. Safe to call concurrently: the
    one-accrual-per-seniority-year constraint turns a racing duplicate into a no-op."""
    facts = employment_facts(employee_id)
    if facts is None or not facts.is_active:
        return
    years = LedgerEntry.objects.filter(
        employee_id=employee_id, kind=LedgerKind.ACCRUAL
    ).values_list("seniority_year", flat=True)
    existing = frozenset(year for year in years if year is not None)  # never None: DB check
    due = due_accruals(
        facts.hire_date, facts.birth_date, start_date(), _floor(employee_id), today, existing
    )
    LedgerEntry.objects.bulk_create(
        [
            LedgerEntry(
                employee_id=employee_id,
                kind=LedgerKind.ACCRUAL,
                amount=accrual.days,
                effective_date=accrual.date,
                seniority_year=accrual.seniority_year,
            )
            for accrual in due
        ],
        ignore_conflicts=True,
    )


def _sum(employee_id: int) -> Decimal:
    total = LedgerEntry.objects.filter(employee_id=employee_id).aggregate(total=Sum("amount"))
    return total["total"] or Decimal(0)


def balance_of(employee_id: int, today: datetime.date) -> Decimal:
    materialize_accruals(employee_id, today)
    return _sum(employee_id)


def summary_of(employee_id: int, today: datetime.date) -> BalanceSummary:
    facts = employment_facts(employee_id)
    if facts is None:
        raise EmployeeNotFoundError(employee_id)
    with transaction.atomic():
        materialize_accruals(employee_id, today)
        entries = [
            EntryView(e.public_id, e.effective_date, e.kind, e.amount, e.reason)
            for e in LedgerEntry.objects.filter(employee_id=employee_id).order_by(
                "-effective_date", "-created_at", "-pk"
            )
        ]
        balance = _sum(employee_id)
    upcoming = None
    if facts.is_active:
        upcoming = next_accrual(
            facts.hire_date, facts.birth_date, start_date(), _floor(employee_id), today
        )
    return BalanceSummary(balance, upcoming, entries)


def add_adjustment(
    employee_id: int, amount: Decimal, reason: str, actor_id: uuid.UUID, today: datetime.date
) -> uuid.UUID:
    """HR adjustment (BR-12): validated, dated today, audited in the same transaction. It may
    take the balance below zero — only HR can do that (spec 0003, Req 7)."""
    validate_adjustment_amount(amount)
    cleaned = validate_reason(reason)
    facts = employment_facts(employee_id)
    if facts is None:
        raise EmployeeNotFoundError(employee_id)
    with transaction.atomic():
        entry = LedgerEntry.objects.create(
            employee_id=employee_id,
            kind=LedgerKind.ADJUSTMENT,
            amount=amount,
            effective_date=today,
            reason=cleaned,
            created_by=actor_id,
        )
        record(
            actor_id,
            ADJUSTMENT_ACTION,
            entry.public_id,
            {"employee": str(facts.public_id), "amount": str(amount), "reason": cleaned},
        )
    return entry.public_id


def before_employee_change(employee_id: int, today: datetime.date) -> EmploymentFacts | None:
    """Call before HR saves an employee: accrues what the old data earned, returns the snapshot
    for ``after_employee_change`` (plan 0003, risk 2)."""
    materialize_accruals(employee_id, today)
    return employment_facts(employee_id)


def after_employee_change(
    employee_id: int, today: datetime.date, before: EmploymentFacts | None
) -> None:
    """Reactivation or a hire/birth date change: anniversaries before today no longer accrue."""
    after = employment_facts(employee_id)
    if before is None or after is None:
        return
    reactivated = after.is_active and not before.is_active
    dates_changed = (after.hire_date, after.birth_date) != (before.hire_date, before.birth_date)
    if reactivated or dates_changed:
        AccrualFloor.objects.update_or_create(employee_id=employee_id, defaults={"floor": today})

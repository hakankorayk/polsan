"""Balance ledger use cases (spec 0003). Accruals are written when a balance is read (ADR 0004)."""

import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.db import connection, transaction
from django.db.models import Sum

from audit.api import record
from balances.domain.accrual import Accrual, due_accruals, next_accrual
from balances.domain.amounts import validate_adjustment_amount, validate_reason
from balances.models import AccrualFloor, AccrualSettings, LedgerEntry, LedgerKind
from employees.api import EmploymentFacts, employment_facts

ADJUSTMENT_ACTION = "balance.adjustment"
# PostgreSQL advisory lock guarding the start date (review M1): every accrual write holds it
# shared, a start date change holds it exclusive. Raw SQL because the ORM has no shared row lock
# (FOR SHARE); FOR UPDATE on the settings row would serialise every balance read.
START_DATE_LOCK = 3_000_301


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


def _lock_start_date_shared() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock_shared(%s)", [START_DATE_LOCK])


def check_start_date_change(value: datetime.date | None) -> None:
    """Raise StartDateLockedError if ``value`` may not become the start date. Takes the exclusive
    lock until the end of the caller's transaction, so a concurrent read cannot write accruals
    with the old date between this check and the save (review M1). Call it inside a transaction."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [START_DATE_LOCK])
    if start_date_locked() and value != start_date():
        raise StartDateLockedError(StartDateLockedError.message)


def set_start_date(value: datetime.date | None) -> None:
    with transaction.atomic():
        check_start_date_change(value)
        AccrualSettings.objects.update_or_create(key=1, defaults={"start_date": value})


def _floor(employee_id: int) -> datetime.date | None:
    return (
        AccrualFloor.objects.filter(employee_id=employee_id).values_list("floor", flat=True).first()
    )


def materialize_accruals(employee_id: int, today: datetime.date) -> None:
    """Write the accruals due by ``today`` that the ledger lacks. Safe to call concurrently: the
    one-accrual-per-seniority-year constraint turns a racing duplicate into a no-op, and the
    shared start date lock keeps a concurrent start date change from interleaving."""
    facts = employment_facts(employee_id)
    if facts is None or not facts.is_active:
        return
    with transaction.atomic():
        _lock_start_date_shared()
        _write_due_accruals(employee_id, facts, today)


def _accrued_years(employee_id: int) -> frozenset[int]:
    years = LedgerEntry.objects.filter(
        employee_id=employee_id, kind=LedgerKind.ACCRUAL
    ).values_list("seniority_year", flat=True)
    return frozenset(year for year in years if year is not None)  # never None: DB check


def _write_due_accruals(employee_id: int, facts: EmploymentFacts, today: datetime.date) -> None:
    due = due_accruals(
        facts.hire_date,
        facts.birth_date,
        start_date(),
        _floor(employee_id),
        today,
        _accrued_years(employee_id),
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
            facts.hire_date,
            facts.birth_date,
            start_date(),
            _floor(employee_id),
            today,
            _accrued_years(employee_id),
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
    """Reactivation or a hire/birth date change: anniversaries before today no longer accrue.
    Only once the start date is set: during setup, before it, a past start date must apply to
    every employee alike (spec 0003, Req 4; review M3)."""
    after = employment_facts(employee_id)
    if before is None or after is None or start_date() is None:
        return
    reactivated = after.is_active and not before.is_active
    dates_changed = (after.hire_date, after.birth_date) != (before.hire_date, before.birth_date)
    if reactivated or dates_changed:
        AccrualFloor.objects.update_or_create(employee_id=employee_id, defaults={"floor": today})


def employee_created(employee_id: int, today: datetime.date) -> None:
    """A record added today: its earlier anniversaries are HR's opening adjustment, never
    automatic accruals (spec 0003, Req 4; review M3)."""
    AccrualFloor.objects.update_or_create(employee_id=employee_id, defaults={"floor": today})

"""Annual leave accrual rules (docs/domain.md BR-1, BR-2, BR-3, BR-15; spec 0003, Req 2-5).

Pure Python: dates are passed in, nothing reads a clock. Days are ``Decimal``, never ``float``.
"""

import datetime
from dataclasses import dataclass
from decimal import Decimal

YOUNG_MAX_AGE = 18
OLD_MIN_AGE = 50
AGE_FLOOR_DAYS = Decimal(20)


@dataclass(frozen=True)
class Accrual:
    seniority_year: int
    date: datetime.date
    days: Decimal


def anniversary(hire: datetime.date, year: int) -> datetime.date:
    """The ``year``-th anniversary of ``hire``; 29 February falls on 28 February in common years."""
    try:
        return hire.replace(year=hire.year + year)
    except ValueError:
        return datetime.date(hire.year + year, 2, 28)


def completed_years(start: datetime.date, on: datetime.date) -> int:
    """Full years from ``start`` to ``on``, for seniority and age alike: someone born or hired on
    29 February completes a year on 28 February in common years (spec 0003, Req 2; review L1)."""
    years = on.year - start.year
    return years - int(on < anniversary(start, years))


def entitlement(seniority_year: int, age: int) -> Decimal:
    """BR-1 tiers, raised to 20 days for employees aged 18 or younger or 50 or older (BR-2)."""
    if seniority_year < 1:
        raise ValueError("no entitlement before the first full year (BR-3)")
    if seniority_year <= 5:
        days = Decimal(14)
    elif seniority_year <= 14:
        days = Decimal(20)
    else:
        days = Decimal(26)
    if age <= YOUNG_MAX_AGE or age >= OLD_MIN_AGE:
        days = max(days, AGE_FLOOR_DAYS)
    return days


def _accrual(hire: datetime.date, birth: datetime.date, year: int) -> Accrual:
    on = anniversary(hire, year)
    return Accrual(year, on, entitlement(year, completed_years(birth, on)))


def _lower_bound(start: datetime.date, floor: datetime.date | None) -> datetime.date:
    return max(start, floor) if floor is not None else start


def due_accruals(
    hire: datetime.date,
    birth: datetime.date,
    start: datetime.date | None,
    floor: datetime.date | None,
    today: datetime.date,
    existing_years: frozenset[int] = frozenset(),
) -> list[Accrual]:
    """Accruals that must be in the ledger on ``today`` and are not there yet.

    Only anniversaries on or after the automatic accrual start date (and the employee's floor,
    if any) count; none at all while the start date is unset (spec 0003, Req 4-5).
    """
    if start is None:
        return []
    lower = _lower_bound(start, floor)
    due = []
    year = 1
    while (on := anniversary(hire, year)) <= today:
        if on >= lower and year not in existing_years:
            due.append(_accrual(hire, birth, year))
        year += 1
    return due


def next_accrual(
    hire: datetime.date,
    birth: datetime.date,
    start: datetime.date | None,
    floor: datetime.date | None,
    today: datetime.date,
    existing_years: frozenset[int] = frozenset(),
) -> Accrual | None:
    """The first accrual after ``today`` that will really be made, or None if it would not be made
    automatically. Seniority years already in the ledger are skipped: after HR moves the hire date
    forward, they never accrue again (spec 0003, Req 6 and 11; review M2)."""
    if start is None:
        return None
    year = max(completed_years(hire, today), 0) + 1
    while anniversary(hire, year) <= today or year in existing_years:
        year += 1
    upcoming = _accrual(hire, birth, year)
    return upcoming if upcoming.date >= _lower_bound(start, floor) else None

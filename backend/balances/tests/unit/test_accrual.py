"""Spec 0003 — accrual rules: AC-4 … AC-8, AC-10, AC-13, AC-21 (BR-1, BR-2, BR-3, BR-11)."""

import datetime
from decimal import Decimal

import pytest

from balances.domain.accrual import (
    Accrual,
    anniversary,
    completed_years,
    due_accruals,
    entitlement,
    next_accrual,
)

D = datetime.date
HIRE = D(2020, 3, 10)
BORN_30 = D(1990, 1, 1)  # 30-40 years old for every anniversary below: no age floor
START = D(2020, 1, 1)


def _days(accruals: list[Accrual]) -> list[tuple[int, Decimal]]:
    return [(a.seniority_year, a.days) for a in accruals]


def test_br3_no_accrual_before_first_anniversary() -> None:
    assert due_accruals(HIRE, BORN_30, START, None, D(2021, 3, 9)) == []


def test_br3_first_anniversary_adds_14() -> None:
    assert due_accruals(HIRE, BORN_30, START, None, D(2021, 3, 10)) == [
        Accrual(1, D(2021, 3, 10), Decimal(14))
    ]


@pytest.mark.parametrize(
    ("seniority_year", "days"),
    [(1, 14), (5, 14), (6, 20), (14, 20), (15, 26), (16, 26)],
)
def test_br1_tiers(seniority_year: int, days: int) -> None:
    assert entitlement(seniority_year, age=30) == Decimal(days)


@pytest.mark.parametrize(
    ("age", "days"),
    [(17, 20), (18, 20), (19, 14), (49, 14), (50, 20), (51, 20)],
)
def test_br2_age_floor_in_years_one_to_five(age: int, days: int) -> None:
    assert entitlement(3, age) == Decimal(days)


@pytest.mark.parametrize("age", [18, 50])
def test_br2_floor_never_lowers_higher_tiers(age: int) -> None:
    assert entitlement(6, age) == Decimal(20)
    assert entitlement(15, age) == Decimal(26)


def test_br3_no_entitlement_for_year_zero() -> None:
    with pytest.raises(ValueError):
        entitlement(0, 30)


def test_br2_age_on_anniversary_day() -> None:
    first_anniversary = D(2021, 3, 10)
    fifty_on_anniversary = D(1971, 3, 10)
    fifty_day_after = D(1971, 3, 11)

    [on_day] = due_accruals(HIRE, fifty_on_anniversary, START, None, first_anniversary)
    [day_after] = due_accruals(HIRE, fifty_day_after, START, None, first_anniversary)

    assert on_day.days == Decimal(20)
    assert day_after.days == Decimal(14)


def test_feb29_hire_anniversary_is_feb28_in_common_years() -> None:
    hire = D(2020, 2, 29)

    assert anniversary(hire, 1) == D(2021, 2, 28)
    assert anniversary(hire, 4) == D(2024, 2, 29)
    assert due_accruals(hire, BORN_30, START, None, D(2021, 2, 27)) == []
    assert _days(due_accruals(hire, BORN_30, START, None, D(2021, 2, 28))) == [(1, Decimal(14))]


def test_anniversaries_before_start_date_skipped() -> None:
    start = D(2023, 3, 10)  # the 3rd anniversary itself

    due = due_accruals(HIRE, BORN_30, start, None, D(2024, 6, 1))

    assert _days(due) == [(3, Decimal(14)), (4, Decimal(14))]


def test_no_accrual_without_start_date() -> None:
    assert due_accruals(HIRE, BORN_30, None, None, D(2030, 1, 1)) == []


def test_floor_skips_anniversaries_before_it() -> None:
    due = due_accruals(HIRE, BORN_30, START, D(2023, 3, 11), D(2024, 6, 1))

    assert _days(due) == [(4, Decimal(14))]


def test_existing_years_are_not_due_again() -> None:
    due = due_accruals(HIRE, BORN_30, START, None, D(2023, 6, 1), frozenset({1, 2}))

    assert _days(due) == [(3, Decimal(14))]


def test_multiple_missed_anniversaries_each_with_own_tier_and_age() -> None:
    hire = D(2010, 6, 1)
    born = D(1962, 6, 2)  # turns 50 on 2012-06-02: 49 at the 2nd anniversary, 50 at the 3rd

    due = due_accruals(hire, born, D(2010, 1, 1), None, D(2025, 6, 1))

    assert _days(due) == [
        (1, Decimal(14)),  # age 48
        (2, Decimal(14)),  # age 49
        (3, Decimal(20)),  # age 50: floor
        (4, Decimal(20)),
        (5, Decimal(20)),
        *[(year, Decimal(20)) for year in range(6, 15)],
        (15, Decimal(26)),
    ]


def test_br11_year_end_creates_nothing() -> None:
    dec31 = due_accruals(HIRE, BORN_30, START, None, D(2022, 12, 31))
    jan1 = due_accruals(HIRE, BORN_30, START, None, D(2023, 1, 1))

    assert dec31 == jan1


def test_next_accrual_date_and_days() -> None:
    assert next_accrual(HIRE, BORN_30, START, None, D(2026, 10, 21)) == Accrual(
        7, D(2027, 3, 10), Decimal(20)
    )


def test_next_accrual_on_anniversary_day_is_the_following_year() -> None:
    upcoming = next_accrual(HIRE, BORN_30, START, None, D(2021, 3, 10))

    assert upcoming is not None and upcoming.date == D(2022, 3, 10)


def test_next_accrual_for_feb29_hire_on_feb28() -> None:
    upcoming = next_accrual(D(2020, 2, 29), BORN_30, START, None, D(2021, 2, 28))

    assert upcoming == Accrual(2, D(2022, 2, 28), Decimal(14))


def test_next_accrual_before_first_year() -> None:
    upcoming = next_accrual(HIRE, BORN_30, START, None, D(2020, 5, 1))

    assert upcoming == Accrual(1, D(2021, 3, 10), Decimal(14))


def test_no_next_accrual_before_start_or_without_start() -> None:
    assert next_accrual(HIRE, BORN_30, None, None, D(2026, 10, 21)) is None
    assert next_accrual(HIRE, BORN_30, D(2027, 3, 11), None, D(2026, 10, 21)) is None
    assert next_accrual(HIRE, BORN_30, D(2027, 3, 10), None, D(2026, 10, 21)) is not None


def test_next_accrual_skips_years_already_in_ledger() -> None:
    """AC-36 (review M2): hired 2020-03-10, years 1-6 accrued, hire date moved to 2022-03-10.
    Years 5 and 6 of the new dates are in the ledger already: the next real accrual is year 7."""
    moved = D(2022, 3, 10)
    accrued = frozenset(range(1, 7))
    today = D(2026, 10, 21)

    upcoming = next_accrual(moved, BORN_30, START, today, today, accrued)

    assert upcoming == Accrual(7, D(2029, 3, 10), Decimal(20))
    assert due_accruals(moved, BORN_30, START, today, D(2027, 3, 10), accrued) == []
    assert _days(due_accruals(moved, BORN_30, START, today, D(2029, 3, 10), accrued)) == [
        (7, Decimal(20))
    ]


def test_br2_feb29_birthday_counts_on_feb28() -> None:
    """AC-33 (review L1): born 1976-02-29, the 2026-02-28 anniversary is the 50th birthday."""
    hire = D(2025, 2, 28)
    leap_born = D(1976, 2, 29)

    [accrual] = due_accruals(hire, leap_born, START, None, D(2026, 2, 28))

    assert accrual.days == Decimal(20)
    assert completed_years(leap_born, D(2026, 2, 27)) == 49
    assert completed_years(leap_born, D(2026, 2, 28)) == 50
    assert completed_years(leap_born, D(2028, 2, 28)) == 51  # leap year: birthday is 29 Feb
    assert completed_years(leap_born, D(2028, 2, 29)) == 52

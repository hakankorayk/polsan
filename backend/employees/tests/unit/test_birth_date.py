"""Spec 0003 — AC-2: birth date not in the future, strictly before the hire date."""

import datetime

import pytest

from employees.domain.dates import BirthDateError, validate_birth_date

TODAY = datetime.date(2026, 10, 21)
HIRE = datetime.date(2020, 3, 1)


def test_past_birth_date_before_hire_accepted() -> None:
    validate_birth_date(datetime.date(1990, 5, 17), HIRE, TODAY)


def test_birth_date_today_without_hire_is_not_in_future() -> None:
    validate_birth_date(TODAY, None, TODAY)


def test_birth_date_after_today_rejected() -> None:
    with pytest.raises(BirthDateError) as error:
        validate_birth_date(TODAY + datetime.timedelta(days=1), None, TODAY)

    assert error.value.code == "birth_date_in_future"


@pytest.mark.parametrize("birth", [HIRE, HIRE + datetime.timedelta(days=1)])
def test_birth_date_on_or_after_hire_rejected(birth: datetime.date) -> None:
    with pytest.raises(BirthDateError) as error:
        validate_birth_date(birth, HIRE, TODAY)

    assert error.value.code == "birth_date_not_before_hire"

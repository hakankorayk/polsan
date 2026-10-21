"""Spec 0003 — Req 4, AC-34 for the first HR account (review N2): the record created by
`create_first_hr` does not accrue for anniversaries before its creation day, like every employee
HR adds in the admin. Lives outside the modules: the command is in the composition root."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from balances import clock
from balances.api import balance_of, set_start_date

D = datetime.date
CREATED = D(2026, 10, 21)


def test_first_hr_accrues_only_from_creation_day(db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    set_start_date(D(2020, 1, 1))  # a past start date (AC-35)
    monkeypatch.setattr(clock, "today", lambda: CREATED)
    monkeypatch.setenv("FIRST_HR_PASSWORD", "Ilk-IK-Parola-2026!")

    call_command(
        "create_first_hr",
        "--username=ikadmin",
        "--first-name=İlk",
        "--last-name=İK",
        "--hire-date=2019-05-01",
        "--birth-date=1985-06-15",
    )
    employee_id = get_user_model().objects.get(username="ikadmin").employee_id

    assert balance_of(employee_id, CREATED) == Decimal(
        0
    )  # 2020…2026 anniversaries: opening balance
    assert balance_of(employee_id, D(2027, 5, 1)) == Decimal(20)  # 8th year, after creation

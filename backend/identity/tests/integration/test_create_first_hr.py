"""Spec 0002 — AC-24: the server command creates the first HR account with its employee."""

import pytest
from django.core.management import CommandError, call_command
from rest_framework.test import APIClient

from employees.api import get_employee
from identity.models import User
from identity.tests.integration.conftest import log_in

TEMP = "Ilk-IK-Parola-2026!"
ARGS = [
    "--username",
    "IKAdmin",
    "--first-name",
    "İlk",
    "--last-name",
    "İK",
    "--hire-date",
    "2019-05-01",
]


def test_command_creates_hr_with_forced_change(db, monkeypatch) -> None:
    monkeypatch.setenv("FIRST_HR_PASSWORD", TEMP)

    call_command("create_first_hr", *ARGS)
    user = User.objects.get(username="ikadmin")
    employee = get_employee(user.employee_id)
    login = log_in(APIClient(), "ikadmin", TEMP)

    assert user.is_hr and user.must_change_password
    assert employee is not None and (employee.first_name, employee.last_name) == ("İlk", "İK")
    assert login.json() == {"must_change_password": True}


def test_command_refuses_when_an_hr_exists(make_user, monkeypatch) -> None:
    make_user("mevcutik", is_hr=True)
    monkeypatch.setenv("FIRST_HR_PASSWORD", TEMP)

    with pytest.raises(CommandError):
        call_command("create_first_hr", *ARGS)
    assert not User.objects.filter(username="ikadmin").exists()


def test_command_rejects_weak_password(db, monkeypatch) -> None:
    monkeypatch.setenv("FIRST_HR_PASSWORD", "kisa")

    with pytest.raises(CommandError):
        call_command("create_first_hr", *ARGS)
    assert not User.objects.exists()

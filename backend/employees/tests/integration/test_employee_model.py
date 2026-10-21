"""Spec 0002 — AC-2 through the model form the admin uses; reports query used by AC-16.
Spec 0003 — AC-1, AC-2: birth date is required and validated by the same form."""

from __future__ import annotations

import datetime

import pytest
from django.forms import ModelForm, modelform_factory

from employees.api import active_direct_reports, has_active_direct_reports
from employees.models import Employee

HIRED = datetime.date(2020, 1, 1)
BORN = datetime.date(1990, 1, 1)
EmployeeForm = modelform_factory(
    Employee,
    fields=["first_name", "last_name", "hire_date", "birth_date", "manager", "is_active"],
)


def _employee(first: str, last: str, manager: Employee | None = None, active: bool = True):
    return Employee.objects.create(
        first_name=first,
        last_name=last,
        hire_date=HIRED,
        birth_date=BORN,
        manager=manager,
        is_active=active,
    )


def _form(instance: Employee, manager: Employee | None) -> ModelForm[Employee]:
    data = {
        "first_name": instance.first_name,
        "last_name": instance.last_name,
        "hire_date": HIRED.isoformat(),
        "birth_date": BORN.isoformat(),
        "manager": manager.pk if manager else "",
        "is_active": "on",
    }
    return EmployeeForm(data=data, instance=instance)


@pytest.mark.django_db
def test_cycle_not_saved_via_admin_form() -> None:
    a = _employee("Ali", "Aksoy")
    b = _employee("Banu", "Bal", manager=a)
    c = _employee("Cem", "Can", manager=b)

    self_form = _form(a, a)
    two_step = _form(a, b)
    three_step = _form(a, c)

    for form in (self_form, two_step, three_step):
        assert not form.is_valid()
        assert "manager" in form.errors
    a.refresh_from_db()
    assert a.manager is None


@pytest.mark.django_db
def test_valid_manager_saved() -> None:
    a = _employee("Ali", "Aksoy")
    b = _employee("Banu", "Bal")

    form = _form(b, a)

    assert form.is_valid(), form.errors
    form.save()
    b.refresh_from_db()
    assert b.manager == a


@pytest.mark.django_db
def test_active_direct_reports_sorted_direct_and_active_only() -> None:
    boss = _employee("Zeynep", "Yönetici")
    yilmaz = _employee("Ayşe", "Yılmaz", manager=boss)
    _employee("Mehmet", "Çelik", manager=boss)
    _employee("Can", "Şahin", manager=boss)
    _employee("Ece", "Demir", manager=boss)
    _employee("Pasif", "Akın", manager=boss, active=False)
    _employee("Dolaylı", "Arslan", manager=yilmaz)

    names = [r.last_name for r in active_direct_reports(boss.pk)]

    assert names == ["Çelik", "Demir", "Şahin", "Yılmaz"]
    assert has_active_direct_reports(boss.pk)
    assert not has_active_direct_reports(_employee("Yalnız", "Kişi").pk)


def _new_employee_form(birth_date: str) -> ModelForm[Employee]:
    data = {
        "first_name": "Ali",
        "last_name": "Aksoy",
        "hire_date": HIRED.isoformat(),
        "birth_date": birth_date,
        "is_active": "on",
    }
    return EmployeeForm(data=data)


@pytest.mark.django_db
def test_birth_date_required() -> None:
    form = _new_employee_form("")

    assert not form.is_valid()
    assert form.errors.as_data()["birth_date"][0].code == "required"
    assert not Employee.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("birth_date", "code"),
    [
        ((datetime.date.today() + datetime.timedelta(days=2)).isoformat(), "birth_date_in_future"),
        (HIRED.isoformat(), "birth_date_not_before_hire"),
        ("2020-06-01", "birth_date_not_before_hire"),
    ],
)
def test_invalid_birth_date_not_saved(birth_date: str, code: str) -> None:
    form = _new_employee_form(birth_date)

    assert not form.is_valid()
    assert form.errors.as_data()["birth_date"][0].code == code
    assert not Employee.objects.exists()

"""Spec 0002 — AC-1, AC-3, AC-5, AC-12, AC-25, AC-26 through the HR admin site."""

import pytest
from django.test import Client
from rest_framework.test import APIClient

from employees.api import get_employee
from identity.api import active_hr_count
from identity.models import User
from identity.tests.integration.conftest import PASSWORD, log_in
from tests.factories import find_employee

TEMP = "Gecici-Parola-2026!"


@pytest.fixture
def hr_client(make_user, make_employee) -> Client:
    hr = make_user("ik", employee=make_employee("İnsan", "Kaynakları"), is_hr=True)
    client = Client()
    client.force_login(hr)
    return client


def _employee_form(first: str, last: str, manager: str = "", active: bool = True) -> dict:
    data = {"first_name": first, "last_name": last, "hire_date": "2021-03-15", "manager": manager}
    if active:
        data["is_active"] = "on"
    return data


def test_hr_creates_and_edits_employee(hr_client, make_employee) -> None:
    boss = make_employee("Zeynep", "Yönetici")

    created = hr_client.post(
        "/admin/employees/employee/add/", _employee_form("Ali", "Veli", str(boss.pk))
    )
    ali = find_employee("Ali")
    edited = hr_client.post(
        f"/admin/employees/employee/{ali.pk}/change/", _employee_form("Ali", "Can", active=False)
    )
    ali.refresh_from_db()

    assert created.status_code == 302
    assert edited.status_code == 302
    assert (ali.last_name, ali.manager, ali.is_active) == ("Can", None, False)
    assert str(ali.hire_date) == "2021-03-15"


def test_hr_creates_account_with_temporary_password(hr_client, make_employee) -> None:
    person = make_employee("Ali", "Veli")

    response = hr_client.post(
        "/admin/identity/user/add/",
        {"username": "aveli", "employee": person.pk, "temporary_password": TEMP},
    )
    user = User.objects.get(username="aveli")

    assert response.status_code == 302
    assert user.must_change_password
    assert user.check_password(TEMP)
    assert log_in(APIClient(), "aveli", TEMP).json() == {"must_change_password": True}


def test_second_account_same_username_or_employee_rejected(hr_client, make_user, make_employee):
    taken = make_user("aveli", employee=make_employee("Ali", "Veli"))
    other = make_employee("Banu", "Bal")

    same_name = hr_client.post(
        "/admin/identity/user/add/",
        {"username": "aveli", "employee": other.pk, "temporary_password": TEMP},
    )
    same_employee = hr_client.post(
        "/admin/identity/user/add/",
        {"username": "baskasi", "employee": taken.employee_id, "temporary_password": TEMP},
    )

    assert same_name.status_code == 200  # form re-rendered with errors
    assert same_employee.status_code == 200
    assert User.objects.filter(employee=other).count() == 0
    assert not User.objects.filter(username="baskasi").exists()


def test_username_case_insensitive_unique(hr_client, make_user, make_employee) -> None:
    make_user("hkacar", employee=make_employee("Hakan", "Kaçar"))
    other = make_employee("Başka", "Biri")

    upper = hr_client.post(
        "/admin/identity/user/add/",
        {"username": "HKacar", "employee": other.pk, "temporary_password": TEMP},
    )
    turkish = hr_client.post(
        "/admin/identity/user/add/",
        {"username": "kaçar", "employee": other.pk, "temporary_password": TEMP},
    )

    assert upper.status_code == 200
    assert turkish.status_code == 200
    assert User.objects.count() == 2  # hr + hkacar


def test_non_hr_and_anonymous_denied_admin(make_user) -> None:
    employee_user = make_user("calisan")
    pending_hr = make_user("yeniik", is_hr=True, must_change=True)
    anonymous = Client()
    logged_in = Client()
    logged_in.force_login(employee_user)
    pending = Client()
    pending.force_login(pending_hr)

    for client in (anonymous, logged_in, pending):
        for url in ("/admin/", "/admin/identity/user/", "/admin/employees/employee/"):
            first = client.get(url)
            chain = client.get(url, follow=True).redirect_chain
            assert first.status_code == 302, url
            assert chain[-1] == ("/", 302), url  # ends at the application login, never a form


def test_hr_reaches_admin(hr_client) -> None:
    assert hr_client.get("/admin/").status_code == 200


def test_reset_to_temporary_forces_change_again(hr_client, make_user) -> None:
    user = make_user("kalici")

    response = hr_client.post(
        f"/admin/identity/user/{user.pk}/change/",
        {"username": "kalici", "is_active": "on", "temporary_password": TEMP},
    )
    user.refresh_from_db()

    assert response.status_code == 302
    assert user.must_change_password
    assert log_in(APIClient(), "kalici", PASSWORD).status_code == 400
    assert log_in(APIClient(), "kalici", TEMP).json() == {"must_change_password": True}


def _account_form(user: User, *, is_hr: bool, is_active: bool) -> dict:
    data: dict = {"username": user.username}
    if is_hr:
        data["is_hr"] = "on"
    if is_active:
        data["is_active"] = "on"
    return data


def test_last_hr_cannot_lose_role_or_be_deactivated(make_user, make_employee) -> None:
    hr = make_user("ik", employee=make_employee("Tek", "İK"), is_hr=True)
    client = Client()
    client.force_login(hr)

    drop_role = client.post(
        f"/admin/identity/user/{hr.pk}/change/", _account_form(hr, is_hr=False, is_active=True)
    )
    deactivate = client.post(
        f"/admin/identity/user/{hr.pk}/change/", _account_form(hr, is_hr=True, is_active=False)
    )
    deactivate_employee = client.post(
        f"/admin/employees/employee/{hr.employee_id}/change/",
        _employee_form("Tek", "İK", active=False),
    )
    hr.refresh_from_db()

    for response in (drop_role, deactivate, deactivate_employee):
        assert response.status_code == 200
        assert "Son aktif İK hesabı" in response.content.decode()
    assert hr.is_hr and hr.is_active
    info = get_employee(hr.employee_id)
    assert info is not None and info.is_active


def test_allowed_with_second_hr(make_user, make_employee) -> None:
    hr = make_user("ik", employee=make_employee("Bir", "İK"), is_hr=True)
    make_user("ik2", employee=make_employee("İki", "İK"), is_hr=True)
    client = Client()
    client.force_login(hr)

    response = client.post(
        f"/admin/identity/user/{hr.pk}/change/", _account_form(hr, is_hr=False, is_active=True)
    )
    hr.refresh_from_db()

    assert response.status_code == 302
    assert not hr.is_hr


def test_accounts_and_employees_cannot_be_deleted(hr_client, make_user) -> None:
    user = make_user("silinmez")

    for url in (
        f"/admin/identity/user/{user.pk}/delete/",
        f"/admin/employees/employee/{user.employee_id}/delete/",
    ):
        assert hr_client.post(url, {"post": "yes"}).status_code == 403
    assert User.objects.filter(pk=user.pk).exists()


def test_account_cannot_be_relinked_to_another_employee(make_user, make_employee) -> None:
    hr = make_user("ik", employee=make_employee("Tek", "İK"), is_hr=True)
    former = make_employee("Eski", "Çalışan", active=False)
    client = Client()
    client.force_login(hr)
    data = _account_form(hr, is_hr=True, is_active=True)
    data["employee"] = former.pk

    response = client.post(f"/admin/identity/user/{hr.pk}/change/", data)
    hr.refresh_from_db()

    assert response.status_code == 302  # saved, but the employee field is ignored (read-only)
    assert hr.employee_id != former.pk
    assert active_hr_count() == 1
    assert client.get("/admin/").status_code == 200

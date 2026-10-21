"""Spec 0002 — AC-4, AC-15, AC-16, AC-17: the home page data is the caller's own, nothing else."""

import uuid

from identity.tests.integration.conftest import log_in


def test_me_returns_name_and_roles(client, make_user, make_employee) -> None:
    make_user("ayilmaz", employee=make_employee("Ayşe", "Yılmaz"))
    log_in(client, "ayilmaz")

    response = client.get("/api/me/")

    assert response.status_code == 200
    assert response.json() == {
        "first_name": "Ayşe",
        "last_name": "Yılmaz",
        "roles": ["employee"],
        "team": None,
    }


def test_roles_derived_from_tree(client, make_user, make_employee) -> None:
    boss = make_employee("Zeynep", "Yönetici")
    make_employee("Ali", "Aktif", manager=boss)
    lonely = make_employee("Selin", "Yalnız")
    make_employee("Pasif", "Bağlı", manager=lonely, active=False)
    hr = make_employee("İnsan", "Kaynakları")
    make_user("boss", employee=boss)
    make_user("lonely", employee=lonely)
    make_user("hr", employee=hr, is_hr=True)

    roles = {}
    for username in ("boss", "lonely", "hr"):
        log_in(client, username)
        roles[username] = client.get("/api/me/").json()["roles"]
        client.post("/api/auth/logout/")

    assert roles == {
        "boss": ["employee", "manager"],
        "lonely": ["employee"],  # every report is inactive -> not a manager
        "hr": ["employee", "hr"],
    }


def test_team_only_direct_active_reports_sorted(client, make_user, make_employee) -> None:
    boss = make_employee("Zeynep", "Yönetici")
    yilmaz = make_employee("Ayşe", "Yılmaz", manager=boss)
    for first, last in (("Mehmet", "Çelik"), ("Can", "Şahin"), ("Ece", "Demir")):
        make_employee(first, last, manager=boss)
    make_employee("Pasif", "Akın", manager=boss, active=False)
    make_employee("Dolaylı", "Arslan", manager=yilmaz)
    make_user("boss", employee=boss)
    log_in(client, "boss")

    team = client.get("/api/me/").json()["team"]

    assert team == [
        {"first_name": "Mehmet", "last_name": "Çelik"},
        {"first_name": "Ece", "last_name": "Demir"},
        {"first_name": "Can", "last_name": "Şahin"},
        {"first_name": "Ayşe", "last_name": "Yılmaz"},
    ]


def test_me_contains_only_own_data(client, make_user, make_employee) -> None:
    other_boss = make_employee("Başka", "Yönetici")
    make_employee("Gizli", "Ekip", manager=other_boss)
    make_user("other", employee=other_boss)
    make_user("ayilmaz", employee=make_employee("Ayşe", "Yılmaz"))
    log_in(client, "ayilmaz")

    body = client.get("/api/me/").content.decode()

    for foreign in ("Başka", "Gizli", "Ekip", "other"):
        assert foreign not in body


def test_guessed_id_routes_return_404(client, make_user, make_employee) -> None:
    other = make_employee("Başka", "Kişi")
    make_user("ayilmaz")
    log_in(client, "ayilmaz")

    for route in (
        f"/api/employees/{other.public_id}/",
        f"/api/managers/{other.public_id}/team/",
        f"/api/employees/{uuid.uuid4()}/",
    ):
        assert client.get(route).status_code == 404, route

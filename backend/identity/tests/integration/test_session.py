"""Spec 0002 — AC-13 (30-minute idle timeout) and AC-28 (deactivation ends the session)."""

from datetime import timedelta

from django.contrib.sessions.models import Session
from django.utils import timezone

from identity.tests.integration.conftest import log_in


def _session_key(client) -> str:  # noqa: ANN001
    return client.cookies["sessionid"].value


def test_idle_30_minutes_expires(client, make_user) -> None:
    make_user("ayilmaz")
    log_in(client, "ayilmaz")
    Session.objects.filter(session_key=_session_key(client)).update(
        expire_date=timezone.now() - timedelta(seconds=1)
    )

    response = client.get("/api/me/")

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


def test_activity_keeps_session_alive(client, make_user) -> None:
    make_user("ayilmaz")
    log_in(client, "ayilmaz")
    session = Session.objects.get(session_key=_session_key(client))
    session.expire_date = timezone.now() + timedelta(minutes=1)  # almost idle for 30 minutes
    session.save()

    assert client.get("/api/me/").status_code == 200
    renewed = Session.objects.get(session_key=_session_key(client)).expire_date
    assert renewed > timezone.now() + timedelta(minutes=29)


def test_deactivated_account_or_employee_session_ends(client, make_user, make_employee) -> None:
    account = make_user("hesap", employee=make_employee("Hesap", "Pasif"))
    other_client = client.__class__()
    person = make_user("calisan", employee=make_employee("Çalışan", "Pasif"))
    log_in(client, "hesap")
    log_in(other_client, "calisan")

    account.is_active = False
    account.save()
    person.employee.is_active = False
    person.employee.save()

    for c in (client, other_client):
        response = c.get("/api/me/")
        assert response.status_code == 403
        assert response.json()["code"] == "not_authenticated"

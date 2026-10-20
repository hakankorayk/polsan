"""Spec 0002 — AC-6, AC-7, AC-8, AC-9, AC-14, AC-26 against the real API and database."""

from datetime import timedelta

from django.utils import timezone

from identity.models import LoginThrottle
from identity.tests.integration.conftest import PASSWORD, log_in

INVALID = "Kullanıcı adı veya parola hatalı."
LOCKED = "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin."


def test_valid_login_succeeds(client, make_user) -> None:
    make_user("ayilmaz")

    response = log_in(client, "ayilmaz")

    assert response.status_code == 200
    assert response.json() == {"must_change_password": False}
    assert client.get("/api/me/").status_code == 200


def test_wrong_password_unknown_user_and_inactive_get_identical_response(
    client, make_user, make_employee
) -> None:
    make_user("ayilmaz")
    make_user("pasifhesap", employee=make_employee("Pasif", "Hesap"), active=False)
    make_user("pasifcalisan", employee=make_employee("Pasif", "Çalışan", active=False))

    responses = [
        log_in(client, "ayilmaz", "yanlis-parola-123"),
        log_in(client, "boyle-biri-yok"),
        log_in(client, "pasifhesap"),
        log_in(client, "pasifcalisan"),
    ]

    bodies = {r.content for r in responses}
    assert {r.status_code for r in responses} == {400}
    assert len(bodies) == 1
    assert responses[0].json()["code"] == "invalid_credentials"
    assert responses[0].json()["detail"] == INVALID
    assert responses[0]["Content-Type"] == "application/problem+json"


def test_locked_rejects_correct_password(client, make_user) -> None:
    make_user("ayilmaz")
    for _ in range(4):
        assert log_in(client, "ayilmaz", "yanlis-parola-123").status_code == 400

    fifth = log_in(client, "ayilmaz", "yanlis-parola-123")
    correct_while_locked = log_in(client, "ayilmaz", PASSWORD)

    assert fifth.status_code == 429
    assert correct_while_locked.status_code == 429
    assert correct_while_locked.json()["code"] == "login_locked"
    assert correct_while_locked.json()["detail"] == LOCKED


def test_lock_expires_after_15_minutes(client, make_user) -> None:
    make_user("ayilmaz")
    for _ in range(5):
        log_in(client, "ayilmaz", "yanlis-parola-123")
    LoginThrottle.objects.filter(username="ayilmaz").update(
        locked_until=timezone.now() - timedelta(seconds=1)
    )

    assert log_in(client, "ayilmaz", PASSWORD).status_code == 200


def test_success_resets_counter(client, make_user) -> None:
    make_user("ayilmaz")
    for _ in range(4):
        assert log_in(client, "ayilmaz", "yanlis-parola-123").status_code == 400
    assert log_in(client, "ayilmaz").status_code == 200
    client.post("/api/auth/logout/")

    after_reset = [log_in(client, "ayilmaz", "yanlis-parola-123").status_code for _ in range(4)]
    fifth = log_in(client, "ayilmaz", "yanlis-parola-123")

    assert after_reset == [400, 400, 400, 400]  # without the reset the first of these would lock
    assert fifth.status_code == 429


def test_unknown_username_gets_lock_message(client, db) -> None:
    for _ in range(4):
        log_in(client, "boyle-biri-yok", "yanlis-parola-123")

    response = log_in(client, "boyle-biri-yok", "yanlis-parola-123")

    assert response.status_code == 429
    assert response.json()["detail"] == LOCKED


def test_login_case_insensitive(client, make_user) -> None:
    make_user("hkacar")

    assert log_in(client, "HKacar").status_code == 200


def test_logout_ends_session(client, make_user) -> None:
    make_user("ayilmaz")
    log_in(client, "ayilmaz")

    logout = client.post("/api/auth/logout/")
    after = client.get("/api/me/")

    assert logout.status_code == 204
    assert after.status_code == 403
    assert after.json()["code"] == "not_authenticated"


def test_success_creates_no_throttle_row(client, make_user) -> None:
    make_user("ayilmaz")

    assert log_in(client, "ayilmaz").status_code == 200
    assert not LoginThrottle.objects.exists()


def test_stale_throttle_rows_are_purged_on_the_next_failure(client, db) -> None:
    now = timezone.now()
    LoginThrottle.objects.create(username="eski", updated_at=now - timedelta(minutes=16))
    LoginThrottle.objects.create(
        username="eski-kilitli",
        updated_at=now - timedelta(minutes=20),
        locked_until=now + timedelta(minutes=1),  # a running lock is kept
    )
    LoginThrottle.objects.create(username="taze", updated_at=now - timedelta(minutes=5))

    log_in(client, "baskasi", "yanlis-parola-123")

    assert set(LoginThrottle.objects.values_list("username", flat=True)) == {
        "eski-kilitli",
        "taze",
        "baskasi",
    }

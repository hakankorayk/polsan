"""Spec 0003 — AC-12: concurrent first reads of a balance create each accrual exactly once."""

import threading
import time

import pytest
from django.db import connection

from balances import services
from balances.models import LedgerEntry, LedgerKind
from balances.tests.integration.conftest import D
from tests.factories import Employee

READERS = 4
TIMEOUT = 30  # seconds; a thread still alive after this is a hang, reported as such


@pytest.mark.django_db(transaction=True)
def test_concurrent_reads_create_one_entry(
    started: None, employee: Employee, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Every reader computes "what is missing" before any of them inserts: the worst interleaving.
    barrier = threading.Barrier(READERS, timeout=TIMEOUT)
    real_bulk_create = LedgerEntry.objects.bulk_create

    def racing_bulk_create(objs, **kwargs):  # noqa: ANN001, ANN003, ANN202
        barrier.wait()
        return real_bulk_create(objs, **kwargs)

    monkeypatch.setattr(LedgerEntry.objects, "bulk_create", racing_bulk_create)
    errors: list[BaseException] = []

    def read() -> None:
        try:
            services.summary_of(employee.pk, D(2023, 6, 1))
        except BaseException as error:  # noqa: BLE001 — collected and asserted below
            errors.append(error)
        finally:
            connection.close()

    threads = [threading.Thread(target=read) for _ in range(READERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(TIMEOUT)

    assert not any(thread.is_alive() for thread in threads)
    assert errors == []
    years = LedgerEntry.objects.filter(employee=employee, kind=LedgerKind.ACCRUAL).values_list(
        "seniority_year", flat=True
    )
    assert sorted(year for year in years if year is not None) == [1, 2, 3]


def _a_lock_is_awaited() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")
        row = cursor.fetchone()
    return bool(row and row[0])


@pytest.mark.django_db(transaction=True)
def test_start_date_change_waits_for_concurrent_read(
    started: None, employee: Employee, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-37 (review M1): a read has computed accruals with the old start date and is about to
    write them while HR changes the date. The change must wait for the read, then be refused —
    never leave the setting and the ledger disagreeing."""
    old_start = services.start_date()
    about_to_write = threading.Event()
    change_finished = threading.Event()
    real_bulk_create = LedgerEntry.objects.bulk_create

    def paused_bulk_create(objs, **kwargs):  # noqa: ANN001, ANN003, ANN202
        about_to_write.set()
        deadline = time.monotonic() + TIMEOUT
        # Hold until the change is blocked on the lock (fixed) or already done (the M1 race).
        while not (change_finished.is_set() or _a_lock_is_awaited()):
            if time.monotonic() > deadline:
                break
            time.sleep(0.02)
        return real_bulk_create(objs, **kwargs)

    monkeypatch.setattr(LedgerEntry.objects, "bulk_create", paused_bulk_create)
    outcome: list[object] = []

    def read() -> None:
        try:
            services.summary_of(employee.pk, D(2023, 6, 1))
        finally:
            connection.close()

    def change() -> None:
        about_to_write.wait(TIMEOUT)
        try:
            services.set_start_date(D(2024, 1, 1))
            outcome.append("saved")
        except services.StartDateLockedError as error:
            outcome.append(error)
        finally:
            change_finished.set()
            connection.close()

    threads = [threading.Thread(target=read), threading.Thread(target=change)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(TIMEOUT)

    assert not any(thread.is_alive() for thread in threads)
    assert len(outcome) == 1 and isinstance(outcome[0], services.StartDateLockedError)
    assert services.start_date() == old_start
    years = LedgerEntry.objects.filter(employee=employee, kind=LedgerKind.ACCRUAL).values_list(
        "seniority_year", flat=True
    )
    assert sorted(year for year in years if year is not None) == [1, 2, 3]

"""Spec 0003 — AC-20: audit records cannot be changed or deleted."""

import uuid

import pytest

from audit.api import ImmutableRecordError, record, records_for
from audit.models import AuditRecord

ACTOR = uuid.uuid4()
TARGET = uuid.uuid4()


@pytest.fixture
def stored(db: None) -> AuditRecord:
    record(ACTOR, "balance.adjustment", TARGET, {"amount": "2.0", "reason": "Açılış"})
    return AuditRecord.objects.get(target_id=TARGET)


def test_record_is_readable_by_target(stored: AuditRecord) -> None:
    [entry] = records_for(TARGET)

    assert (entry.actor_id, entry.action, entry.data) == (
        ACTOR,
        "balance.adjustment",
        {"amount": "2.0", "reason": "Açılış"},
    )


def test_saved_record_cannot_be_changed(stored: AuditRecord) -> None:
    stored.action = "something.else"

    with pytest.raises(ImmutableRecordError):
        stored.save()
    assert AuditRecord.objects.get(pk=stored.pk).action == "balance.adjustment"


def test_record_cannot_be_deleted(stored: AuditRecord) -> None:
    with pytest.raises(ImmutableRecordError):
        stored.delete()
    assert AuditRecord.objects.filter(pk=stored.pk).exists()


def test_queryset_update_and_delete_are_refused(stored: AuditRecord) -> None:
    with pytest.raises(ImmutableRecordError):
        AuditRecord.objects.filter(pk=stored.pk).update(action="x")
    with pytest.raises(ImmutableRecordError):
        AuditRecord.objects.filter(pk=stored.pk).delete()
    assert AuditRecord.objects.get(pk=stored.pk).action == "balance.adjustment"

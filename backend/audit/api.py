"""Public interface of the audit module.

Other modules may import only this module (docs/architecture.md, Forbidden dependencies 1).
"""

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from audit.models import AuditRecord, ImmutableRecordError

__all__ = ["AuditEntry", "ImmutableRecordError", "record", "records_for"]


@dataclass(frozen=True)
class AuditEntry:
    occurred_at: datetime.datetime
    actor_id: uuid.UUID
    action: str
    target_id: uuid.UUID
    data: dict[str, Any]


def record(actor_id: uuid.UUID, action: str, target_id: uuid.UUID, data: dict[str, Any]) -> None:
    """Append one audit record. Call it inside the transaction of the change it records."""
    AuditRecord.objects.create(actor_id=actor_id, action=action, target_id=target_id, data=data)


def records_for(target_id: uuid.UUID) -> list[AuditEntry]:
    return [
        AuditEntry(r.occurred_at, r.actor_id, r.action, r.target_id, r.data)
        for r in AuditRecord.objects.filter(target_id=target_id).order_by("occurred_at", "pk")
    ]

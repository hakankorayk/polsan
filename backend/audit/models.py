"""Models of the audit module. Internal: other modules never import this file."""

import uuid
from typing import Any, NoReturn

from django.db import models

IMMUTABLE = "Audit kayıtları değiştirilemez ve silinemez."


class ImmutableRecordError(Exception):
    """An attempt to change or delete an append-only record."""


class AppendOnlyQuerySet(models.QuerySet["AuditRecord"]):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ImmutableRecordError(IMMUTABLE)

    def delete(self) -> NoReturn:
        raise ImmutableRecordError(IMMUTABLE)


class AuditRecord(models.Model):
    """Who did what to which record, when (docs/security.md, Audit). Append-only."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    occurred_at = models.DateTimeField("zaman", auto_now_add=True)
    actor_id = models.UUIDField("yapan")
    action = models.CharField("işlem", max_length=64)
    target_id = models.UUIDField("kayıt")
    data = models.JSONField("ayrıntı", default=dict)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        verbose_name = "audit kaydı"
        verbose_name_plural = "audit kayıtları"
        indexes = [models.Index(fields=["target_id"])]

    def __str__(self) -> str:
        return f"{self.action} {self.target_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ImmutableRecordError(IMMUTABLE)
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ImmutableRecordError(IMMUTABLE)

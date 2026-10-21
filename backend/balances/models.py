"""Models of the balances module. Internal: other modules never import this file."""

import uuid
from typing import Any, NoReturn

from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Mod
from django.db.models.lookups import Exact

IMMUTABLE = "Bakiye hareketleri değiştirilemez ve silinemez."


class ImmutableEntryError(Exception):
    """An attempt to change or delete a ledger entry (docs/domain.md BR-12)."""


class LedgerKind(models.TextChoices):
    ACCRUAL = "ACCRUAL", "Hak ediş"
    ADJUSTMENT = "ADJUSTMENT", "Düzeltme"


class AppendOnlyQuerySet(models.QuerySet["LedgerEntry"]):
    def update(self, **kwargs: Any) -> NoReturn:
        raise ImmutableEntryError(IMMUTABLE)

    def delete(self) -> NoReturn:
        raise ImmutableEntryError(IMMUTABLE)


class LedgerEntry(models.Model):
    """One balance movement. The balance is the sum of these; nothing else stores it."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    employee = models.ForeignKey(
        "employees.Employee",
        verbose_name="çalışan",
        on_delete=models.PROTECT,
        related_name="+",
    )
    kind = models.CharField("tür", max_length=16, choices=LedgerKind.choices)
    amount = models.DecimalField("miktar (gün)", max_digits=5, decimal_places=1)
    effective_date = models.DateField("tarih")
    seniority_year = models.PositiveSmallIntegerField("kıdem yılı", null=True, blank=True)
    reason = models.TextField("gerekçe", blank=True)
    created_at = models.DateTimeField("kayıt zamanı", auto_now_add=True)
    created_by = models.UUIDField("kaydeden", null=True, blank=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        verbose_name = "bakiye hareketi"
        verbose_name_plural = "bakiye hareketleri"
        constraints = [
            # One accrual per seniority year, whatever reads race (spec 0003, AC-12; ADR 0004).
            models.UniqueConstraint(
                fields=["employee", "seniority_year"],
                condition=Q(kind=LedgerKind.ACCRUAL),
                name="balances_one_accrual_per_seniority_year",
            ),
            models.CheckConstraint(condition=~Q(amount=0), name="balances_entry_amount_not_zero"),
            models.CheckConstraint(
                condition=Exact(Mod(F("amount") * 2, Value(1)), 0),
                name="balances_entry_amount_half_multiple",
            ),
            models.CheckConstraint(
                condition=Q(kind=LedgerKind.ACCRUAL, seniority_year__isnull=False)
                | (Q(kind=LedgerKind.ADJUSTMENT, seniority_year__isnull=True) & ~Q(reason="")),
                name="balances_entry_kind_fields",
            ),
        ]
        indexes = [models.Index(fields=["employee", "effective_date"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.amount} ({self.effective_date})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ImmutableEntryError(IMMUTABLE)
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ImmutableEntryError(IMMUTABLE)


class AccrualSettings(models.Model):
    """The single row holding the automatic accrual start date (spec 0003, Req 5)."""

    key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    start_date = models.DateField("otomatik hak ediş başlangıç tarihi", null=True, blank=True)

    class Meta:
        verbose_name = "hak ediş ayarı"
        verbose_name_plural = "hak ediş ayarları"
        constraints = [models.CheckConstraint(condition=Q(key=1), name="balances_settings_single")]

    def __str__(self) -> str:
        return "Hak ediş ayarları"


class AccrualFloor(models.Model):
    """Anniversaries before ``floor`` no longer accrue for this employee: set when an inactive
    employee is reactivated or their hire/birth date changes (plan 0003, risk 2; ADR 0004)."""

    employee = models.OneToOneField(
        "employees.Employee", on_delete=models.PROTECT, related_name="+"
    )
    floor = models.DateField()

    def __str__(self) -> str:
        return f"{self.employee_id}: {self.floor}"

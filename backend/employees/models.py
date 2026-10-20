"""Models of the employees module. Internal: other modules never import this file."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from employees.domain.hierarchy import HierarchyError, validate_manager


class Employee(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    first_name = models.CharField("ad", max_length=100)
    last_name = models.CharField("soyad", max_length=100)
    hire_date = models.DateField("işe giriş tarihi")
    manager = models.ForeignKey(
        "self",
        verbose_name="yönetici",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="direct_reports",
    )
    is_active = models.BooleanField("aktif", default=True)

    class Meta:
        verbose_name = "çalışan"
        verbose_name_plural = "çalışanlar"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def clean(self) -> None:
        def manager_of(employee_id: int) -> int | None:
            return (
                Employee.objects.filter(pk=employee_id).values_list("manager_id", flat=True).first()
            )

        try:
            validate_manager(self.pk, self.manager_id, manager_of)
        except HierarchyError as error:
            raise ValidationError({"manager": error.message}, code=error.code) from error

"""Models of the identity module. Internal: other modules never import this file."""

from typing import Any, ClassVar

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from identity.domain.usernames import MAX_LENGTH, normalize_username, username_error


class UserManager(BaseUserManager["User"]):
    def get_by_natural_key(self, username: str | None) -> "User":
        return self.get(username=normalize_username(username or ""))

    def create_user(self, username: str, password: str, **fields: Any) -> "User":
        user = self.model(username=normalize_username(username), **fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """An account. Bound to exactly one employee (the only cross-module FK allowed, rule 4)."""

    username = models.CharField("kullanıcı adı", max_length=MAX_LENGTH, unique=True)
    employee = models.OneToOneField(
        "employees.Employee",
        verbose_name="çalışan",
        on_delete=models.PROTECT,
        related_name="account",
    )
    is_active = models.BooleanField("aktif", default=True)
    is_hr = models.BooleanField("İK yetkisi", default=False)
    must_change_password = models.BooleanField("ilk girişte parola değiştirmeli", default=True)
    date_joined = models.DateTimeField("oluşturulma", default=timezone.now)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        verbose_name = "hesap"
        verbose_name_plural = "hesaplar"

    def __str__(self) -> str:
        return self.username

    def clean(self) -> None:
        error = username_error(self.username)
        if error:
            raise ValidationError({"username": error}, code="invalid_username")
        self.username = normalize_username(self.username)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.username = normalize_username(self.username)
        super().save(*args, **kwargs)

    # The admin site asks these; only HR may use it (spec 0002, AC-5).
    @property
    def is_staff(self) -> bool:
        return self.is_active and self.is_hr and not self.must_change_password

    def has_perm(self, perm: str, obj: object = None) -> bool:
        return self.is_staff

    def has_module_perms(self, app_label: str) -> bool:
        return self.is_staff


class LoginThrottle(models.Model):
    """Throttle state per normalized username — also for usernames that do not exist."""

    username = models.CharField(max_length=MAX_LENGTH, unique=True)
    failures = models.JSONField(default=list)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self) -> str:
        return self.username

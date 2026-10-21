"""HR administration (spec 0002, AC-1, AC-3, AC-5, AC-12, AC-25; spec 0003, AC-1, AC-2, AC-11,
AC-14 … AC-20, AC-30).

Lives in the composition root: the "last active HR" rule needs both employees and identity, and
employees may not depend on identity (docs/architecture.md, dependency direction). Employee saves
also notify balances around the change (ADR 0004, accrual floor).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.auth.password_validation import validate_password
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from balances import api as balances
from balances.models import AccrualSettings, LedgerEntry
from employees.models import Employee
from identity.api import is_last_active_hr
from identity.models import User

LAST_HR = "Son aktif İK hesabı için bu değişiklik yapılamaz: önce başka bir İK hesabı açın."


class HRAdminSite(admin.AdminSite):
    site_header = "Polsan Leave Manager — İK yönetimi"
    site_title = "İK yönetimi"
    index_title = "Çalışanlar ve hesaplar"

    def has_permission(self, request: HttpRequest) -> bool:
        # User.is_staff = active account + HR grant + no pending forced password change.
        return bool(getattr(request.user, "is_staff", False))

    def login(self, request: HttpRequest, extra_context: Any = None) -> HttpResponse:
        # One login path only: the throttled application login (spec 0002, AC-8).
        return HttpResponseRedirect("/")


hr_admin_site = HRAdminSite(name="hr_admin")


class EmployeeAdminForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "hire_date", "birth_date", "manager", "is_active"]

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        deactivates = self.instance.pk and not data.get("is_active", True)
        if deactivates and is_last_active_hr(employee_id=self.instance.pk):
            raise forms.ValidationError(LAST_HR, code="last_hr")
        return data


class NoDeleteAdmin(admin.ModelAdmin):
    """Accounts and employees are deactivated, never deleted (audit trail, docs/security.md)."""

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


def format_days(value: Decimal) -> str:
    """Turkish day amounts in the admin: "12,5 gün" (spec 0003, Req 11)."""
    text = f"{value.normalize():f}" if value == value.to_integral() else f"{value:.1f}"
    return f"{text.replace('.', ',')} gün"


class EmployeeAdmin(NoDeleteAdmin):
    form = EmployeeAdminForm
    list_display = ("last_name", "first_name", "manager", "hire_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("first_name", "last_name")
    autocomplete_fields = ("manager",)
    readonly_fields = ("balance",)

    @admin.display(description="Bakiye")
    def balance(self, obj: Employee) -> str:
        if obj.pk is None:
            return "—"
        return format_days(balances.balance_of(obj.pk, balances.today()))

    def save_model(self, request: HttpRequest, obj: Employee, form: Any, change: bool) -> None:
        # Accrue with the old data first; a reactivation or date change then sets the floor.
        today = balances.today()
        before = balances.before_employee_change(obj.pk, today) if change else None
        super().save_model(request, obj, form, change)
        if change:
            balances.after_employee_change(obj.pk, today, before)
        else:
            balances.employee_created(obj.pk, today)


class AdjustmentForm(forms.ModelForm):
    class Meta:
        model = LedgerEntry
        fields = ["employee", "amount", "reason"]
        labels = {"amount": "Miktar (gün)", "reason": "Gerekçe"}
        help_texts = {
            "amount": "Artı veya eksi; 0,5'in katı, en fazla 100 gün.",
            "reason": "Zorunlu. Çalışan bu gerekçeyi kendi hareket geçmişinde görür.",
        }

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        try:
            if data.get("amount") is not None:
                balances.validate_adjustment_amount(data["amount"])
            data["reason"] = balances.validate_reason(data.get("reason", ""))
        except balances.AdjustmentError as error:
            self.add_error(error.field, forms.ValidationError(error.message, code=error.code))
        return data


class LedgerEntryAdmin(admin.ModelAdmin):
    """Adjustments are added here; no entry is ever changed or deleted (BR-12, AC-19)."""

    form = AdjustmentForm
    list_display = ("effective_date", "employee", "kind", "signed_amount", "reason")
    list_filter = (("employee", admin.RelatedOnlyFieldListFilter), "kind")
    search_fields = ("employee__first_name", "employee__last_name")
    autocomplete_fields = ("employee",)
    ordering = ("-effective_date", "-created_at")

    @admin.display(description="Miktar", ordering="amount")
    def signed_amount(self, obj: LedgerEntry) -> str:
        sign = "+" if obj.amount > 0 else "−"
        return f"{sign}{format_days(abs(obj.amount))}"

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def save_model(self, request: HttpRequest, obj: LedgerEntry, form: Any, change: bool) -> None:
        actor = request.user.employee.public_id  # type: ignore[union-attr]
        entry_id = balances.add_adjustment(
            obj.employee_id, obj.amount, obj.reason, actor, balances.today()
        )
        saved = LedgerEntry.objects.get(public_id=entry_id)
        obj.pk, obj.public_id, obj._state.adding = saved.pk, saved.public_id, False


class AccrualSettingsForm(forms.ModelForm):
    class Meta:
        model = AccrualSettings
        fields = ["start_date"]
        help_texts = {
            "start_date": "Bu tarihten önceki yıldönümleri otomatik hak ediş oluşturmaz. İlk "
            "otomatik hak ediş oluştuktan sonra değiştirilemez."
        }

    def clean_start_date(self) -> Any:
        value = self.cleaned_data.get("start_date")
        # The admin view runs in one transaction: the lock taken here holds until the save, so
        # the check cannot go stale and the save cannot fail with a 500 (review M1).
        try:
            balances.check_start_date_change(value)
        except balances.StartDateLockedError as error:
            raise forms.ValidationError(error.message, code=error.code) from error
        return value


class AccrualSettingsAdmin(admin.ModelAdmin):
    form = AccrualSettingsForm
    list_display = ("__str__", "start_date")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not AccrualSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: AccrualSettings, form: Any, change: bool
    ) -> None:
        balances.set_start_date(obj.start_date)
        saved = AccrualSettings.objects.get()
        obj.pk, obj._state.adding = saved.pk, False


class TemporaryPasswordMixin(forms.ModelForm):
    temporary_password = forms.CharField(
        label="Geçici parola",
        widget=forms.PasswordInput(render_value=False),
        strip=False,
        help_text="Kullanıcı ilk girişte bu parolayı değiştirmek zorunda kalır.",
    )

    def clean_temporary_password(self) -> str:
        password: str = self.cleaned_data.get("temporary_password", "")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        password = self.cleaned_data.get("temporary_password")
        if password:
            user.set_password(password)
            user.must_change_password = True
        if commit:
            user.save()
        return user


class AccountCreationForm(TemporaryPasswordMixin):
    class Meta:
        model = User
        fields = ["username", "employee", "is_hr"]


class AccountChangeForm(TemporaryPasswordMixin):
    # No "employee": an account stays bound to the same person for life (spec 0002, Req 3) —
    # re-linking it to an inactive employee would also bypass the last-HR guard (review M1).
    class Meta:
        model = User
        fields = ["username", "is_active", "is_hr"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        field = self.fields["temporary_password"]
        field.required = False
        field.label = "Yeni geçici parola"
        field.help_text = "Doldurulursa parola sıfırlanır ve ilk girişte değiştirilmesi istenir."

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        removes_hr = not data.get("is_hr", True) or not data.get("is_active", True)
        if self.instance.pk and removes_hr and is_last_active_hr(user_id=self.instance.pk):
            raise forms.ValidationError(LAST_HR, code="last_hr")
        return data


class AccountAdmin(NoDeleteAdmin):
    list_display = ("username", "employee", "is_active", "is_hr", "must_change_password")
    list_filter = ("is_active", "is_hr")
    search_fields = ("username",)
    readonly_fields = ("must_change_password", "last_login", "date_joined")

    def get_form(
        self, request: HttpRequest, obj: Any = None, change: bool = False, **kwargs: Any
    ) -> type[forms.ModelForm[Any]]:
        kwargs["form"] = AccountChangeForm if obj else AccountCreationForm
        return super().get_form(request, obj, change, **kwargs)

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> tuple[str, ...]:
        return ("employee", *self.readonly_fields) if obj else self.readonly_fields

    def get_fields(self, request: HttpRequest, obj: Any = None) -> tuple[str, ...]:
        if obj:
            return (
                "username",
                "is_hr",
                "temporary_password",
                "is_active",
                *self.get_readonly_fields(request, obj),
            )
        return ("username", "employee", "is_hr", "temporary_password")


hr_admin_site.register(Employee, EmployeeAdmin)
hr_admin_site.register(User, AccountAdmin)
hr_admin_site.register(LedgerEntry, LedgerEntryAdmin)
hr_admin_site.register(AccrualSettings, AccrualSettingsAdmin)

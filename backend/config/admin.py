"""HR administration (spec 0002, AC-1, AC-3, AC-5, AC-12, AC-25).

Lives in the composition root: the "last active HR" rule needs both employees and identity, and
employees may not depend on identity (docs/architecture.md, dependency direction).
"""

from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.auth.password_validation import validate_password
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

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
        fields = ["first_name", "last_name", "hire_date", "manager", "is_active"]

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


class EmployeeAdmin(NoDeleteAdmin):
    form = EmployeeAdminForm
    list_display = ("last_name", "first_name", "manager", "hire_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("first_name", "last_name")
    autocomplete_fields = ("manager",)


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

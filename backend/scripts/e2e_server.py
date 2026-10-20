"""E2E backend: migrate the throwaway database, seed the e2e users, then serve in ONE process (no
autoreloader child that could outlive the run — docs/testing.md, Resource hygiene). Started and
stopped by the Playwright webServer in frontend/playwright.config.ts.

Usage: python scripts/e2e_server.py 127.0.0.1:8001

Seeded accounts (one per scenario, so scenarios never share state) — keep in sync with
frontend/e2e/users.ts:
  yonetici  manager of Çelik and Demir (and of an inactive report), permanent password
  calisan   plain employee, permanent password
  gecici    temporary password (forced change)
  klavye    temporary password (keyboard-only flow)
  kilit     permanent password (lockout scenario)
  cikis     permanent password (logout / expired session scenarios)
"""

import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
from django.core.management import call_command  # noqa: E402

PASSWORD = "E2e-Parola-2026!"  # noqa: S105 — throwaway e2e database only
TEMPORARY = "E2e-Gecici-2026!"  # noqa: S105


def seed() -> None:
    from employees.models import Employee
    from identity.models import User

    def employee(first: str, last: str, manager: Employee | None = None, active: bool = True):
        return Employee.objects.create(
            first_name=first,
            last_name=last,
            hire_date=datetime.date(2020, 1, 1),
            manager=manager,
            is_active=active,
        )

    def account(username: str, person: Employee, password: str, must_change: bool) -> None:
        User.objects.create_user(
            username, password, employee=person, must_change_password=must_change
        )

    boss = employee("Zeynep", "Yönetici")
    account("yonetici", boss, PASSWORD, False)
    account("calisan", employee("Ece", "Demir", manager=boss), PASSWORD, False)
    employee("Mehmet", "Çelik", manager=boss)
    employee("Pasif", "Akın", manager=boss, active=False)
    account("gecici", employee("Geçici", "Kullanıcı"), TEMPORARY, True)
    account("klavye", employee("Klavye", "Kullanıcı"), TEMPORARY, True)
    account("kilit", employee("Kilit", "Kullanıcı"), PASSWORD, False)
    account("cikis", employee("Çıkış", "Kullanıcı"), PASSWORD, False)


def main() -> None:
    address = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8001"
    django.setup()
    call_command("migrate", interactive=False, verbosity=0)
    seed()
    call_command("runserver", address, use_reloader=False)


if __name__ == "__main__":
    main()

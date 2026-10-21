"""Create the first HR account with its employee (spec 0002, AC-24).

    python manage.py create_first_hr --username ikadmin --first-name Ayşe --last-name Yılmaz \
        --hire-date 2020-01-01 --birth-date 1985-06-15

The temporary password is read from FIRST_HR_PASSWORD or asked interactively; it is never a
command-line argument (it would land in shell history). The account must change it at first login.
"""

import datetime
import getpass
import os
from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from employees.api import create_employee
from identity.api import active_hr_count
from identity.models import User


class Command(BaseCommand):
    help = "İlk İK hesabını çalışan kaydıyla birlikte oluşturur."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--username", required=True)
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)
        parser.add_argument("--hire-date", required=True, type=datetime.date.fromisoformat)
        parser.add_argument("--birth-date", required=True, type=datetime.date.fromisoformat)

    def handle(self, *args: Any, **options: Any) -> None:
        if active_hr_count() > 0:
            raise CommandError("Zaten aktif bir İK hesabı var; yenileri yönetim panelinden açılır.")
        password = os.environ.get("FIRST_HR_PASSWORD") or self._ask_password()
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        with transaction.atomic():
            try:
                employee_id = create_employee(
                    options["first_name"],
                    options["last_name"],
                    options["hire_date"],
                    options["birth_date"],
                )
            except ValidationError as error:
                raise CommandError(" ".join(error.messages)) from error
            try:
                user = User.objects.create_user(
                    options["username"],
                    password,
                    employee_id=employee_id,
                    is_hr=True,
                    must_change_password=True,
                )
            except ValidationError as error:
                raise CommandError(" ".join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS(f"İK hesabı oluşturuldu: {user.username}"))

    def _ask_password(self) -> str:
        first = getpass.getpass("Geçici parola: ")
        if first != getpass.getpass("Geçici parola (tekrar): "):
            raise CommandError("Parolalar eşleşmiyor.")
        return first

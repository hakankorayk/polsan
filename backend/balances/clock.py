"""The one place balances reads "today" (Europe/Istanbul). Tests replace it with monkeypatch."""

import datetime

from django.utils import timezone


def today() -> datetime.date:
    return timezone.localdate()

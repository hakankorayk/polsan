"""Username rules (spec 0002, AC-26). Pure Python."""

import re

MAX_LENGTH = 150
_ALLOWED = re.compile(r"^[A-Za-z0-9._-]+$")


def normalize_username(raw: str) -> str:
    """Case-insensitive identity: every lookup and store goes through this."""
    return raw.strip().lower()


def username_error(raw: str) -> str | None:
    """Turkish error message for an invalid username, or None when it is valid."""
    value = raw.strip()
    if not value:
        return "Kullanıcı adı boş olamaz."
    if len(value) > MAX_LENGTH:
        return f"Kullanıcı adı en fazla {MAX_LENGTH} karakter olabilir."
    if not _ALLOWED.match(value):
        return (
            "Kullanıcı adı yalnızca İngilizce harf, rakam ve . _ - içerebilir "
            "(Türkçe karakter ve boşluk kullanılamaz)."
        )
    return None

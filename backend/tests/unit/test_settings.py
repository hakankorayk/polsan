"""AC-18: secrets come only from the environment."""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def _setup_django_without_secret_key(**extra_env: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"
    env.update(extra_env)

    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_production_settings_refuse_missing_secret_key() -> None:
    result = _setup_django_without_secret_key()

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "DJANGO_SECRET_KEY" in result.stderr


def test_debug_settings_refuse_missing_secret_key_too() -> None:
    result = _setup_django_without_secret_key(DJANGO_DEBUG="true")

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "DJANGO_SECRET_KEY" in result.stderr


def test_env_example_has_no_real_secret() -> None:
    values = dict(
        line.split("=", 1)
        for line in (BACKEND / ".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )

    assert values["DJANGO_SECRET_KEY"] == ""
    assert values["POSTGRES_PASSWORD"].startswith("change-me")


def test_production_hasher_is_argon2() -> None:
    import config.settings as production  # settings_test already imported it with the test key

    assert production.PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.Argon2PasswordHasher"
    min_length = next(
        v
        for v in production.AUTH_PASSWORD_VALIDATORS
        if v["NAME"].endswith("MinimumLengthValidator")
    )
    assert min_length["OPTIONS"] == {"min_length": 12}


def test_production_cookies_secure() -> None:
    import config.settings as production

    assert not production.DEBUG
    assert production.SESSION_COOKIE_SECURE
    assert production.CSRF_COOKIE_SECURE
    assert production.SESSION_COOKIE_HTTPONLY
    assert production.SESSION_COOKIE_SAMESITE == "Lax"

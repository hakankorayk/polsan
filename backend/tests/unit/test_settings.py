"""AC-18: secrets come only from the environment."""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_production_settings_refuse_missing_secret_key() -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"

    result = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

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

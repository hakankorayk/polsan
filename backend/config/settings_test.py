"""Test settings: a fixed, test-only secret key (docs/security.md allows it here only).
The database host/port are injected by the Testcontainers fixture in conftest.py."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-secret")

from config.settings import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # speed; test-only

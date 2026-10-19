"""E2E backend: migrate the throwaway database, then serve in ONE process (no autoreloader child
that could outlive the run — docs/testing.md, Resource hygiene). Started and stopped by the
Playwright webServer in frontend/playwright.config.ts.

Usage: python scripts/e2e_server.py 127.0.0.1:8001
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
from django.core.management import call_command  # noqa: E402


def main() -> None:
    address = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8001"
    django.setup()
    call_command("migrate", interactive=False, verbosity=0)
    call_command("runserver", address, use_reloader=False)


if __name__ == "__main__":
    main()

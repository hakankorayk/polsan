"""Spec 0002 — AC-26: case-insensitive usernames, ASCII letters, digits and . _ - only."""

import pytest

from identity.domain.usernames import normalize_username, username_error


def test_normalization_is_case_insensitive() -> None:
    assert normalize_username("HKacar") == normalize_username("hkacar") == "hkacar"
    assert normalize_username("  h.kacar ") == "h.kacar"


@pytest.mark.parametrize("valid", ["hkacar", "h.kacar", "h_kacar-2", "HKacar"])
def test_valid_usernames(valid: str) -> None:
    assert username_error(valid) is None


@pytest.mark.parametrize(
    "invalid", ["", "   ", "hakan kacar", "kaçar", "İnci", "ışık", "h@kacar", "a" * 151]
)
def test_invalid_usernames(invalid: str) -> None:
    assert username_error(invalid) is not None

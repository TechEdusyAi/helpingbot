from __future__ import annotations

import pytest

from utils.validation import (
    ensure_non_empty_string,
    ensure_positive_number,
    ensure_type,
    ensure_within_range,
)


def test_ensure_positive_number_rejects_zero():
    with pytest.raises(ValueError):
        ensure_positive_number(0, "error")


def test_ensure_positive_number_accepts_positive():
    ensure_positive_number(1, "should not raise")


def test_ensure_non_empty_string_rejects_blank():
    with pytest.raises(ValueError):
        ensure_non_empty_string("  ", "error")


def test_ensure_within_range_validates_bounds():
    ensure_within_range(0.5, minimum=0.0, maximum=1.0, message="ok")
    with pytest.raises(ValueError):
        ensure_within_range(1.5, minimum=0.0, maximum=1.0, message="error")


def test_ensure_type_matches_expected():
    ensure_type("value", str, "ok")
    with pytest.raises(TypeError):
        ensure_type(123, str, "error")

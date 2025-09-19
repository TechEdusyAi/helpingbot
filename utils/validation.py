"""Validation helpers used across the application."""
from __future__ import annotations

from typing import Any


def ensure_positive_number(value: float, message: str) -> None:
    """Ensure a numeric value is strictly positive."""

    if value is None or value <= 0:
        raise ValueError(message)


def ensure_non_empty_string(value: str, message: str) -> None:
    """Ensure a string has meaningful content."""

    if value is None or not str(value).strip():
        raise ValueError(message)


def ensure_within_range(value: float, *, minimum: float, maximum: float, message: str) -> None:
    """Ensure a value falls within a given inclusive range."""

    if value < minimum or value > maximum:
        raise ValueError(message)


def ensure_type(value: Any, expected_type: type, message: str) -> None:
    """Ensure a value is an instance of ``expected_type``."""

    if not isinstance(value, expected_type):
        raise TypeError(message)

"""Configuration loading utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml

from config.settings import DEFAULT_CONFIG_PATH, DEFAULT_ENV_PREFIX, TradingBotSettings, update_dataclass


class ConfigLoader:
    """Load configuration from YAML files and environment variables."""

    def __init__(self, *, env_prefix: str = DEFAULT_ENV_PREFIX) -> None:
        self.env_prefix = env_prefix

    def load(self, path: Path | None = None) -> TradingBotSettings:
        """Load configuration into a :class:`TradingBotSettings` instance."""

        settings = TradingBotSettings(instruments=["EURUSD"])
        path = path or DEFAULT_CONFIG_PATH
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            update_dataclass(settings, data)
        env_overrides = self._load_env_overrides()
        if env_overrides:
            update_dataclass(settings, env_overrides)
        return settings

    def _load_env_overrides(self) -> Mapping[str, Any]:
        """Return configuration overrides defined in environment variables."""

        overrides: dict[str, Any] = {}
        prefix_len = len(self.env_prefix)
        for key, value in os.environ.items():
            if not key.startswith(self.env_prefix):
                continue
            normalized = key[prefix_len:].lower()
            path = normalized.split("__")
            self._assign_override(overrides, path, value)
        return overrides

    def _assign_override(self, container: dict[str, Any], path: list[str], value: str) -> None:
        current = container
        for part in path[:-1]:
            current = current.setdefault(part, {})
        current[path[-1]] = self._coerce(value)

    @staticmethod
    def _coerce(value: str) -> Any:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

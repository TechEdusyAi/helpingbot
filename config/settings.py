"""Configuration models for the trading bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import MutableSequence
from typing import Any, Mapping

from utils.validation import ensure_positive_number, ensure_within_range


@dataclass
class DataSourceSettings:
    """Configuration for the market data provider."""

    base_url: str
    timeout_seconds: float = 5.0
    retries: int = 3

    def __post_init__(self) -> None:
        ensure_positive_number(self.timeout_seconds, "Timeout must be positive")
        ensure_positive_number(self.retries, "Retries must be positive")


@dataclass
class StrategySettings:
    """Configuration for the SMA crossover strategy."""

    short_window: int = 5
    long_window: int = 20

    def __post_init__(self) -> None:
        ensure_positive_number(self.short_window, "Short window must be positive")
        ensure_positive_number(self.long_window, "Long window must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("Short window must be less than long window")


@dataclass
class RiskSettings:
    """Configuration parameters for the risk manager."""

    max_position_size: float = 1.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04

    def __post_init__(self) -> None:
        ensure_positive_number(self.max_position_size, "Max position size must be positive")
        ensure_within_range(self.stop_loss_pct, minimum=0.0, maximum=1.0, message="Stop loss pct must be between 0 and 1")
        ensure_within_range(self.take_profit_pct, minimum=0.0, maximum=1.0, message="Take profit pct must be between 0 and 1")


@dataclass
class TradingBotSettings:
    """Top-level configuration for running the trading bot."""

    instruments: list[str]
    poll_interval_seconds: float = 60.0
    history_limit: int = 50
    data_source: DataSourceSettings = field(default_factory=lambda: DataSourceSettings(base_url="http://localhost"))
    strategy: StrategySettings = field(default_factory=StrategySettings)
    risk: RiskSettings = field(default_factory=RiskSettings)

    def __post_init__(self) -> None:
        if not self.instruments:
            raise ValueError("At least one instrument must be configured")
        ensure_positive_number(self.poll_interval_seconds, "Poll interval must be positive")
        ensure_positive_number(self.history_limit, "History limit must be positive")


DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_ENV_PREFIX = "TRADING_BOT_"


def update_dataclass(instance: Any, values: Mapping[str, Any]) -> Any:
    """Recursively update a dataclass instance from a mapping."""

    for key, value in values.items():
        if not hasattr(instance, key):
            continue
        attr = getattr(instance, key)
        if isinstance(attr, MutableSequence):
            _apply_sequence_override(attr, value)
        elif hasattr(attr, "__dataclass_fields__") and isinstance(value, Mapping):
            update_dataclass(attr, value)
        else:
            setattr(instance, key, value)
    return instance


def _apply_sequence_override(sequence: MutableSequence[Any], value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            index = int(key)
            while len(sequence) <= index:
                sequence.append(None)
            sequence[index] = item
    elif isinstance(value, (list, tuple)):
        sequence[:] = list(value)
    else:
        sequence[:] = [value]

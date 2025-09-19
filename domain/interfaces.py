"""Domain interfaces defining contracts between layers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Protocol

from domain.models import Candle, Instrument, Order, TradingSignal


class MarketDataProvider(ABC):
    """Provides access to market data required by strategies."""

    @abstractmethod
    def stream_candles(self, instrument: Instrument) -> Iterable[Candle]:
        """Return an iterable of candles for the given instrument."""

    @abstractmethod
    def get_latest_candle(self, instrument: Instrument) -> Candle:
        """Return the most recent candle for the given instrument."""

    @abstractmethod
    def get_historical_candles(
        self, instrument: Instrument, *, start: datetime, end: datetime, limit: int
    ) -> Sequence[Candle]:
        """Return historical candles for the given instrument within a time range."""


class Strategy(ABC):
    """Generates trading signals based on a collection of candles."""

    @abstractmethod
    def generate_signal(self, candles: Sequence[Candle]) -> TradingSignal:
        """Generate a trading signal from the provided candles."""


class RiskAssessment(Protocol):
    """Represents the outcome of a risk validation."""

    approved: bool
    reason: str | None
    order: Order | None


class RiskManager(ABC):
    """Validates trading signals and resulting orders against risk controls."""

    @abstractmethod
    def assess(self, signal: TradingSignal, candles: Sequence[Candle]) -> RiskAssessment:
        """Return a risk assessment for an order derived from the supplied signal."""


class OrderExecutor(ABC):
    """Executes approved orders via an exchange or broker."""

    @abstractmethod
    def execute(self, order: Order) -> str:
        """Execute the provided order and return an execution identifier."""

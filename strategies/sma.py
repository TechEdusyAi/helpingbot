"""Strategy implementations."""
from __future__ import annotations

from collections.abc import Sequence
from statistics import mean

from domain.interfaces import Strategy
from domain.models import Candle, SignalType, TradingSignal


class SMACrossoverStrategy(Strategy):
    """Generates trading signals based on simple moving average crossovers."""

    def __init__(self, *, short_window: int, long_window: int) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("Window sizes must be positive")
        if short_window >= long_window:
            raise ValueError("Short window must be smaller than long window")
        self._short_window = short_window
        self._long_window = long_window

    def generate_signal(self, candles: Sequence[Candle]) -> TradingSignal:
        """Return a trading signal based on the latest crossover state."""

        if len(candles) < self._long_window:
            return TradingSignal(instrument=candles[-1].instrument, signal_type=SignalType.HOLD)
        short_avg = self._moving_average(candles[-self._short_window :])
        long_avg = self._moving_average(candles[-self._long_window :])
        if short_avg > long_avg:
            signal_type = SignalType.BUY
        elif short_avg < long_avg:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        return TradingSignal(instrument=candles[-1].instrument, signal_type=signal_type)

    @staticmethod
    def _moving_average(window: Sequence[Candle]) -> float:
        return mean(candle.close for candle in window)

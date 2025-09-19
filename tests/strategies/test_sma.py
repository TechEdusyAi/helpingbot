from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.models import Candle, Instrument, SignalType
from strategies.sma import SMACrossoverStrategy


def _build_candles(prices: list[float]) -> list[Candle]:
    instrument = Instrument(symbol="EURUSD")
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            instrument=instrument,
            timestamp=base_time + timedelta(minutes=index),
            open=price,
            high=price + 0.1,
            low=price - 0.1,
            close=price,
        )
        for index, price in enumerate(prices)
    ]


def test_generate_signal_requires_sufficient_history():
    strategy = SMACrossoverStrategy(short_window=2, long_window=4)
    candles = _build_candles([1, 2, 3])
    signal = strategy.generate_signal(candles)
    assert signal.signal_type == SignalType.HOLD


def test_generate_signal_buy_when_short_above_long():
    strategy = SMACrossoverStrategy(short_window=2, long_window=4)
    candles = _build_candles([1, 2, 3, 4, 5])
    signal = strategy.generate_signal(candles)
    assert signal.signal_type == SignalType.BUY


def test_generate_signal_sell_when_short_below_long():
    strategy = SMACrossoverStrategy(short_window=2, long_window=4)
    candles = _build_candles([5, 4, 3, 2, 1])
    signal = strategy.generate_signal(candles)
    assert signal.signal_type == SignalType.SELL


def test_invalid_window_configuration():
    with pytest.raises(ValueError):
        SMACrossoverStrategy(short_window=5, long_window=5)

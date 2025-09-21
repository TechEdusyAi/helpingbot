from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.models import Candle, Instrument, Order, OrderSide, SignalType, TradingSignal


def test_instrument_requires_symbol():
    with pytest.raises(ValueError):
        Instrument(symbol=" ")


def test_candle_validates_bounds(sample_instrument: Instrument) -> None:
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        Candle(
            instrument=sample_instrument,
            timestamp=timestamp,
            open=1.0,
            high=0.8,
            low=0.9,
            close=1.0,
        )


def test_trading_signal_strength_must_be_in_range(sample_instrument: Instrument) -> None:
    with pytest.raises(ValueError):
        TradingSignal(instrument=sample_instrument, signal_type=SignalType.BUY, strength=2)


def test_order_validates_stop_levels(sample_instrument: Instrument) -> None:
    with pytest.raises(ValueError):
        Order(
            instrument=sample_instrument,
            side=OrderSide.BUY,
            quantity=1,
            price=1.0,
            stop_loss=2.0,
            take_profit=1.5,
        )

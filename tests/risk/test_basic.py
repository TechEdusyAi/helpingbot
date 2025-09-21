from __future__ import annotations

from datetime import datetime, timezone

import pytest

from config.settings import RiskSettings
from domain.models import Candle, Instrument, SignalType, TradingSignal
from risk.basic import BasicRiskManager


def _candles(price: float) -> list[Candle]:
    instrument = Instrument(symbol="EURUSD")
    return [
        Candle(
            instrument=instrument,
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=price,
            high=price + 0.1,
            low=price - 0.1,
            close=price,
        )
    ]


def test_hold_signal_is_rejected():
    manager = BasicRiskManager(RiskSettings())
    signal = TradingSignal(instrument=Instrument(symbol="EURUSD"), signal_type=SignalType.HOLD)
    assessment = manager.assess(signal, _candles(1.2))
    assert not assessment.approved
    assert assessment.reason == "Hold signal"


def test_buy_signal_creates_order():
    settings = RiskSettings(max_position_size=2, stop_loss_pct=0.05, take_profit_pct=0.1)
    manager = BasicRiskManager(settings)
    signal = TradingSignal(instrument=Instrument(symbol="EURUSD"), signal_type=SignalType.BUY, strength=0.5)
    assessment = manager.assess(signal, _candles(1.2))
    assert assessment.approved
    order = assessment.order
    assert order is not None
    assert order.quantity == pytest.approx(1.0)
    assert order.stop_loss == pytest.approx(1.2 * (1 - 0.05))
    assert order.take_profit == pytest.approx(1.2 * (1 + 0.1))

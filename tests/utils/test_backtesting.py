from __future__ import annotations

from datetime import datetime, timezone

from domain.models import Candle, Instrument, Order, OrderSide, SignalType, TradingSignal
from risk.basic import BasicRiskAssessment
from utils.backtesting import BacktestResult, run_backtest


class DummyStrategy:
    def generate_signal(self, candles):  # noqa: D401 - part of protocol
        price = candles[-1].close
        if price > 1.0:
            return TradingSignal(instrument=candles[-1].instrument, signal_type=SignalType.BUY)
        return TradingSignal(instrument=candles[-1].instrument, signal_type=SignalType.HOLD)


class DummyRiskManager:
    def assess(self, signal, candles):  # noqa: D401 - part of protocol
        if signal.signal_type == SignalType.HOLD:
            return BasicRiskAssessment(approved=False, reason="hold", order=None)
        order = Order(
            instrument=signal.instrument,
            side=OrderSide.BUY,
            quantity=1,
            price=candles[-1].close,
        )
        return BasicRiskAssessment(approved=True, reason=None, order=order)


class Collector:
    def __init__(self) -> None:
        self.orders: list[Order] = []

    def submit(self, order: Order) -> None:
        self.orders.append(order)


def _candles() -> list[Candle]:
    instrument = Instrument(symbol="EURUSD")
    return [
        Candle(
            instrument=instrument,
            timestamp=datetime(2024, 1, 1, 0, minute, tzinfo=timezone.utc),
            open=price,
            high=price + 0.1,
            low=price - 0.1,
            close=price,
        )
        for minute, price in enumerate([0.9, 1.1, 1.2])
    ]


def test_run_backtest_collects_trades():
    collector = Collector()
    result = run_backtest(_candles(), DummyStrategy(), DummyRiskManager(), collector)
    assert isinstance(result, BacktestResult)
    assert result.trades == 2
    assert result.rejected == 1
    assert len(collector.orders) == 2

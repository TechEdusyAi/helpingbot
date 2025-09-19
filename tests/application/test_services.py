from __future__ import annotations

from datetime import datetime, timezone

from application.services import TradingBotService
from config.settings import TradingBotSettings
from domain.interfaces import RiskAssessment
from domain.models import Candle, Instrument, Order, OrderSide, SignalType, TradingSignal
from risk.basic import BasicRiskAssessment


class StubMarketData:
    def __init__(self) -> None:
        self.latest = Candle(
            instrument=Instrument(symbol="EURUSD"),
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=1.0,
            high=1.1,
            low=0.9,
            close=1.05,
        )

    def stream_candles(self, instrument):  # pragma: no cover - not used
        yield self.latest

    def get_latest_candle(self, instrument):
        return self.latest

    def get_historical_candles(self, instrument, *, start, end, limit):
        return [self.latest]


class StubStrategy:
    def generate_signal(self, candles):
        return TradingSignal(instrument=candles[-1].instrument, signal_type=SignalType.BUY)


class StubRiskManager:
    def assess(self, signal, candles) -> RiskAssessment:
        order = Order(
            instrument=signal.instrument,
            side=OrderSide.BUY,
            quantity=1,
            price=candles[-1].close,
        )
        return BasicRiskAssessment(approved=True, reason=None, order=order)


class StubOrderExecutor:
    def __init__(self) -> None:
        self.orders: list[Order] = []

    def execute(self, order: Order) -> str:
        self.orders.append(order)
        return "exec-1"


def test_run_once_executes_order():
    executor = StubOrderExecutor()
    recorded: list[tuple[Order, str]] = []

    def callback(order: Order, execution_id: str) -> None:
        recorded.append((order, execution_id))

    service = TradingBotService(
        settings=TradingBotSettings(instruments=["EURUSD"], history_limit=1, poll_interval_seconds=1),
        market_data=StubMarketData(),
        strategy=StubStrategy(),
        risk_manager=StubRiskManager(),
        order_executor=executor,
        execution_callback=callback,
    )
    service.run_once()
    assert len(executor.orders) == 1
    assert recorded[0][1] == "exec-1"


def test_run_once_rejects_signal():
    class RejectingRiskManager:
        def assess(self, signal, candles) -> RiskAssessment:
            return BasicRiskAssessment(approved=False, reason="risk", order=None)

    executor = StubOrderExecutor()
    service = TradingBotService(
        settings=TradingBotSettings(instruments=["EURUSD"], history_limit=1, poll_interval_seconds=1),
        market_data=StubMarketData(),
        strategy=StubStrategy(),
        risk_manager=RejectingRiskManager(),
        order_executor=executor,
    )
    service.run_once()
    assert not executor.orders


def test_run_cycle_handles_strategy_error(caplog):
    class FaultyStrategy:
        def generate_signal(self, candles):
            raise RuntimeError("boom")

    executor = StubOrderExecutor()
    service = TradingBotService(
        settings=TradingBotSettings(instruments=["EURUSD"], history_limit=1, poll_interval_seconds=1),
        market_data=StubMarketData(),
        strategy=FaultyStrategy(),
        risk_manager=StubRiskManager(),
        order_executor=executor,
    )
    service.run_once()
    assert not executor.orders
    assert any("failed" in message for message in caplog.text.splitlines())

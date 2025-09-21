from __future__ import annotations

from datetime import datetime, timedelta, timezone

from config.settings import DataSourceSettings, RiskSettings, StrategySettings, TradingBotSettings
from domain.models import Candle, Instrument
from presentation.cli import build_service


def test_build_service_run_once(monkeypatch):
    records: list[tuple] = []

    class DummyLogger:
        def __init__(self, *_args, **_kwargs):
            pass

        def record(self, order, execution_id):
            records.append((order, execution_id))

    monkeypatch.setattr("presentation.cli.ExecutionLogger", lambda writer: DummyLogger())

    settings = TradingBotSettings(
        instruments=["EURUSD"],
        poll_interval_seconds=1,
        history_limit=3,
        data_source=DataSourceSettings(base_url="http://test"),
        strategy=StrategySettings(short_window=2, long_window=3),
        risk=RiskSettings(max_position_size=1, stop_loss_pct=0.01, take_profit_pct=0.02),
    )
    service = build_service(settings)

    instrument = Instrument(symbol="EURUSD")
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    history = [
        Candle(instrument=instrument, timestamp=base_time + timedelta(minutes=i), open=1.0 + i * 0.01,
               high=1.1 + i * 0.01, low=0.9 + i * 0.01, close=1.0 + i * 0.01)
        for i in range(3)
    ]
    latest = Candle(
        instrument=instrument,
        timestamp=base_time + timedelta(minutes=4),
        open=1.03,
        high=1.08,
        low=1.01,
        close=1.06,
    )

    monkeypatch.setattr(service._market_data, "get_historical_candles", lambda *args, **kwargs: history)
    monkeypatch.setattr(service._market_data, "get_latest_candle", lambda *_: latest)

    executions: list = []

    def fake_execute(order):
        executions.append(order)
        return "exec-123"

    monkeypatch.setattr(service._order_executor, "execute", fake_execute)

    service.run_once()

    assert len(executions) == 1
    assert executions[0].instrument.symbol == "EURUSD"
    assert records[0][1] == "exec-123"

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from config.settings import DataSourceSettings
from domain.models import Instrument
from infrastructure.market_data import ConfigurableMarketDataClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):  # noqa: D401 - compatibility shim
        return None

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def request(self, method, url, params=None, timeout=None, **kwargs):
        self.calls.append({"method": method, "url": url, "params": params, "timeout": timeout})
        return DummyResponse(self.payloads.pop(0))


def test_get_latest_candle_parses_payload():
    session = DummySession([
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
            "volume": 100,
        }
    ])
    client = ConfigurableMarketDataClient(DataSourceSettings(base_url="http://test"), session=session)
    candle = client.get_latest_candle(Instrument(symbol="EURUSD"))
    assert candle.close == pytest.approx(1.05)
    assert session.calls[0]["params"]["symbol"] == "EURUSD"


def test_get_historical_candles_handles_list_payload():
    payload = [
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
        }
    ]
    session = DummySession([payload])
    client = ConfigurableMarketDataClient(DataSourceSettings(base_url="http://test"), session=session)
    candles = client.get_historical_candles(
        Instrument(symbol="EURUSD"),
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=datetime(2024, 1, 2, tzinfo=timezone.utc),
        limit=10,
    )
    assert len(candles) == 1


def test_stream_candles_requires_source():
    client = ConfigurableMarketDataClient(DataSourceSettings(base_url="http://test"))
    with pytest.raises(NotImplementedError):
        next(iter(client.stream_candles(Instrument(symbol="EURUSD"))))


def test_stream_candles_uses_source():
    instrument = Instrument(symbol="EURUSD")

    def generator(_instrument):
        yield {
            "timestamp": "2024-01-01T00:00:00Z",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
        }

    client = ConfigurableMarketDataClient(
        DataSourceSettings(base_url="http://test"),
        stream_source=lambda _: generator(instrument),
    )
    candle = next(iter(client.stream_candles(instrument)))
    assert candle.instrument.symbol == "EURUSD"

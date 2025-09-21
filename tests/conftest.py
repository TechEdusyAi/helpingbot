from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.models import Candle, Instrument


@pytest.fixture
def sample_instrument() -> Instrument:
    return Instrument(symbol="EURUSD", name="Euro/USD")


@pytest.fixture
def sample_candle(sample_instrument: Instrument) -> Candle:
    return Candle(
        instrument=sample_instrument,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=1.0,
        high=1.2,
        low=0.9,
        close=1.1,
        volume=1000,
    )

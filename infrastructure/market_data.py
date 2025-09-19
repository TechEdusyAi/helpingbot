"""Infrastructure adapters for retrieving market data."""
from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Callable

import requests

from config.settings import DataSourceSettings
from domain.interfaces import MarketDataProvider
from domain.models import Candle, Instrument


class ConfigurableMarketDataClient(MarketDataProvider):
    """Market data provider backed by an HTTP API."""

    def __init__(
        self,
        settings: DataSourceSettings,
        *,
        session: requests.Session | None = None,
        stream_source: Callable[[Instrument], Iterable[dict[str, Any]]] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._stream_source = stream_source
        self._logger = logger or logging.getLogger(__name__)

    def stream_candles(self, instrument: Instrument) -> Iterable[Candle]:
        """Yield candles provided by a configurable streaming source."""

        if self._stream_source is None:
            raise NotImplementedError("No streaming source configured")
        for payload in self._stream_source(instrument):
            yield self._parse_candle(payload, instrument)

    def get_latest_candle(self, instrument: Instrument) -> Candle:
        """Return the latest candle using the configured REST endpoint."""

        endpoint = f"{self._settings.base_url.rstrip('/')}/candles/latest"
        params = {"symbol": instrument.symbol}
        payload = self._request_with_retries("GET", endpoint, params=params)
        return self._parse_candle(payload, instrument)

    def get_historical_candles(
        self, instrument: Instrument, *, start: datetime, end: datetime, limit: int
    ) -> list[Candle]:
        """Return historical candles from the configured REST endpoint."""

        endpoint = f"{self._settings.base_url.rstrip('/')}/candles"
        params = {
            "symbol": instrument.symbol,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": limit,
        }
        payload = self._request_with_retries("GET", endpoint, params=params)
        candles_payload = payload if isinstance(payload, list) else payload.get("candles", [])
        return [self._parse_candle(item, instrument) for item in candles_payload]

    def _request_with_retries(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        last_exc: Exception | None = None
        for attempt in range(1, self._settings.retries + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    params=params,
                    timeout=self._settings.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:  # pragma: no cover - network errors are mocked
                last_exc = exc
                self._logger.warning(
                    "Attempt %s failed for %s %s: %s", attempt, method, url, exc
                )
                time.sleep(min(2 ** attempt * 0.1, 2))
        assert last_exc is not None
        raise last_exc

    def _parse_candle(self, payload: dict[str, Any], instrument: Instrument) -> Candle:
        timestamp = self._parse_timestamp(payload.get("timestamp"))
        return Candle(
            instrument=instrument,
            timestamp=timestamp,
            open=float(payload["open"]),
            high=float(payload["high"]),
            low=float(payload["low"]),
            close=float(payload["close"]),
            volume=float(payload.get("volume")) if payload.get("volume") is not None else None,
        )

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime:
        if value is None:
            raise ValueError("Candle payload missing timestamp")
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)

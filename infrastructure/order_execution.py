"""Infrastructure adapter for executing orders."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config.settings import DataSourceSettings
from domain.interfaces import OrderExecutor
from domain.models import Order


class OrderExecutionClient(OrderExecutor):
    """HTTP-based order execution client with retry and logging support."""

    def __init__(
        self,
        settings: DataSourceSettings,
        *,
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._logger = logger or logging.getLogger(__name__)

    def execute(self, order: Order) -> str:
        """Submit an order to the execution endpoint."""

        endpoint = f"{self._settings.base_url.rstrip('/')}/orders"
        payload = self._serialize_order(order)
        response = self._request_with_retries("POST", endpoint, json=payload)
        execution_id = str(response.get("id"))
        self._logger.debug("Order executed: %s", execution_id)
        return execution_id

    def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(1, self._settings.retries + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    timeout=self._settings.timeout_seconds,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:  # pragma: no cover - network errors mocked
                last_exc = exc
                self._logger.warning(
                    "Order request attempt %s failed: %s", attempt, exc,
                    extra={"payload": kwargs.get("json")},
                )
                time.sleep(min(2 ** attempt * 0.1, 2))
        assert last_exc is not None
        raise last_exc

    def _serialize_order(self, order: Order) -> dict[str, Any]:
        return {
            "symbol": order.instrument.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": order.price,
            "stopLoss": order.stop_loss,
            "takeProfit": order.take_profit,
            "metadata": order.metadata,
        }

from __future__ import annotations

from config.settings import DataSourceSettings
from domain.models import Instrument, Order, OrderSide
from infrastructure.order_execution import OrderExecutionClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):  # noqa: D401
        return None

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, timeout=None, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return DummyResponse(self.response)


def test_execute_posts_order_payload():
    session = DummySession({"id": "abc123"})
    client = OrderExecutionClient(DataSourceSettings(base_url="http://test"), session=session)
    order = Order(instrument=Instrument(symbol="EURUSD"), side=OrderSide.BUY, quantity=1)
    execution_id = client.execute(order)
    assert execution_id == "abc123"
    payload = session.calls[0]["kwargs"]["json"]
    assert payload["symbol"] == "EURUSD"
    assert payload["side"] == "buy"

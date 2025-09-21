from __future__ import annotations

import json
from pathlib import Path

from domain.models import Instrument, Order, OrderSide
from infrastructure.persistence import ExecutionLogger, FileExecutionWriter


def test_execution_logger_writes_file(tmp_path: Path) -> None:
    path = tmp_path / "executions.jsonl"
    logger = ExecutionLogger(FileExecutionWriter(path))
    order = Order(instrument=Instrument(symbol="EURUSD"), side=OrderSide.BUY, quantity=1)
    logger.record(order, "abc")
    data = [json.loads(line) for line in path.read_text().splitlines()]
    assert data[0]["execution_id"] == "abc"
    assert data[0]["order"]["side"] == "buy"

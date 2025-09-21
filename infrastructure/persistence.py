"""Persistence and logging utilities for executed trades."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from domain.models import Order


class ExecutionRecordWriter(Protocol):
    """Protocol describing how execution records are written."""

    def write(self, record: dict) -> None:
        """Persist the supplied execution record."""


@dataclass
class FileExecutionWriter:
    """Writes execution records to a JSON-lines file."""

    path: Path

    def write(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")


class ExecutionLogger:
    """Coordinates logging and persistence of order executions."""

    def __init__(self, writer: ExecutionRecordWriter, *, logger: logging.Logger | None = None) -> None:
        self._writer = writer
        self._logger = logger or logging.getLogger(__name__)

    def record(self, order: Order, execution_id: str) -> None:
        """Persist an order execution event."""

        order_dict = asdict(order)
        order_dict["side"] = order.side.value
        order_dict["instrument"]["symbol"] = order.instrument.symbol
        record = {"execution_id": execution_id, "order": order_dict}
        self._logger.info("Recording order execution %s", execution_id)
        self._writer.write(record)

"""Utilities for backtesting strategies using historical data."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from domain.models import Candle, Order, TradingSignal
from domain.interfaces import RiskManager, Strategy


class OrderExecutorStub(Protocol):
    """Protocol describing the functionality required by the backtester."""

    def submit(self, order: Order) -> None:
        """Submit an order produced during backtesting."""


@dataclass
class BacktestResult:
    """Aggregated results returned from a backtesting run."""

    trades: int
    signals: int
    rejected: int


def run_backtest(
    candles: Sequence[Candle],
    strategy: Strategy,
    risk_manager: RiskManager,
    executor: OrderExecutorStub,
) -> BacktestResult:
    """Execute a basic backtest by replaying candles through the strategy."""

    signals = 0
    trades = 0
    rejected = 0
    window: list[Candle] = []
    for candle in candles:
        window.append(candle)
        signal = strategy.generate_signal(tuple(window))
        signals += 1
        assessment = risk_manager.assess(signal, tuple(window))
        if not assessment.approved or assessment.order is None:
            rejected += 1
            continue
        executor.submit(assessment.order)
        trades += 1
    return BacktestResult(trades=trades, signals=signals, rejected=rejected)

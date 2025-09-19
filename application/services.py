"""Application services orchestrating the trading workflow."""
from __future__ import annotations

import logging
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Deque

from config.settings import TradingBotSettings
from domain.interfaces import MarketDataProvider, OrderExecutor, RiskManager, Strategy
from domain.models import Candle, Instrument, Order
from utils.time import IntervalScheduler, utc_now


@dataclass
class TradingContext:
    """State maintained by the trading bot for each instrument."""

    candles: Deque[Candle]


class TradingBotService:
    """Coordinates market data retrieval, strategy evaluation and order execution."""

    def __init__(
        self,
        *,
        settings: TradingBotSettings,
        market_data: MarketDataProvider,
        strategy: Strategy,
        risk_manager: RiskManager,
        order_executor: OrderExecutor,
        scheduler_factory: Callable[[float], IntervalScheduler] = IntervalScheduler,
        execution_callback: Callable[[Order, str], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._market_data = market_data
        self._strategy = strategy
        self._risk_manager = risk_manager
        self._order_executor = order_executor
        self._scheduler = scheduler_factory(settings.poll_interval_seconds)
        self._contexts: dict[str, TradingContext] = defaultdict(
            lambda: TradingContext(candles=deque(maxlen=settings.history_limit))
        )
        self._execution_callback = execution_callback
        self._logger = logger or logging.getLogger(__name__)

    def start(self) -> None:
        """Start the trading loop."""

        self._logger.info("Starting trading bot")
        self._bootstrap_history()
        self._scheduler.run(self._run_cycle)

    def stop(self) -> None:
        """Stop the trading loop."""

        self._logger.info("Stopping trading bot")
        self._scheduler.stop()

    def _bootstrap_history(self) -> None:
        now = utc_now()
        start = now - timedelta(minutes=self._settings.history_limit)
        for symbol in self._settings.instruments:
            instrument = Instrument(symbol=symbol)
            candles = self._market_data.get_historical_candles(
                instrument, start=start, end=now, limit=self._settings.history_limit
            )
            context = self._contexts[symbol]
            context.candles.extend(candles)
            self._logger.debug("Bootstrapped %s candles for %s", len(context.candles), symbol)

    def _run_cycle(self) -> None:
        for symbol in self._settings.instruments:
            instrument = Instrument(symbol=symbol)
            try:
                candle = self._market_data.get_latest_candle(instrument)
            except Exception as exc:  # noqa: BLE001 - propagate with logging
                self._logger.exception("Failed to fetch candle for %s: %s", symbol, exc)
                continue
            context = self._contexts[symbol]
            context.candles.append(candle)
            self._logger.debug("Appended candle for %s at %s", symbol, candle.timestamp.isoformat())
            try:
                signal = self._strategy.generate_signal(tuple(context.candles))
                assessment = self._risk_manager.assess(signal, tuple(context.candles))
            except Exception as exc:  # noqa: BLE001
                self._logger.exception("Strategy or risk manager failed for %s: %s", symbol, exc)
                continue
            if not assessment.approved or assessment.order is None:
                self._logger.info("Signal rejected for %s: %s", symbol, assessment.reason)
                continue
            try:
                execution_id = self._order_executor.execute(assessment.order)
                self._logger.info("Order executed for %s with id %s", symbol, execution_id)
                if self._execution_callback is not None:
                    self._execution_callback(assessment.order, execution_id)
            except Exception as exc:  # noqa: BLE001
                self._logger.exception("Order execution failed for %s: %s", symbol, exc)

    def run_once(self) -> None:
        """Execute a single trading cycle. Useful for tests and manual runs."""

        self._bootstrap_history()
        self._run_cycle()

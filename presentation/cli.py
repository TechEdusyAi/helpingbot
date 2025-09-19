"""Command line interface for running the trading bot."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from application.services import TradingBotService
from config.loader import ConfigLoader
from config.settings import TradingBotSettings
from infrastructure.market_data import ConfigurableMarketDataClient
from infrastructure.order_execution import OrderExecutionClient
from infrastructure.persistence import ExecutionLogger, FileExecutionWriter
from risk.basic import BasicRiskManager
from strategies.sma import SMACrossoverStrategy
from utils.time import graceful_interrupt


def build_service(settings: TradingBotSettings) -> TradingBotService:
    """Wire dependencies to construct a :class:`TradingBotService`."""

    market_client = ConfigurableMarketDataClient(settings.data_source)
    order_client = OrderExecutionClient(settings.data_source)
    strategy = SMACrossoverStrategy(
        short_window=settings.strategy.short_window,
        long_window=settings.strategy.long_window,
    )
    risk_manager = BasicRiskManager(settings.risk)
    execution_logger = ExecutionLogger(FileExecutionWriter(Path("data/executions.log")))

    return TradingBotService(
        settings=settings,
        market_data=market_client,
        strategy=strategy,
        risk_manager=risk_manager,
        order_executor=order_client,
        execution_callback=execution_logger.record,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the trading bot")
    parser.add_argument("--config", type=Path, default=None, help="Path to YAML configuration file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    loader = ConfigLoader()
    settings = loader.load(args.config)
    service = build_service(settings)

    if args.once:
        service.run_once()
        return 0

    def _handle_interrupt(signum, frame):  # noqa: D401, ANN001 - signature defined by signal
        del signum, frame
        service.stop()

    with graceful_interrupt(_handle_interrupt):
        try:
            service.start()
        except KeyboardInterrupt:  # pragma: no cover - handled via signal
            service.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())

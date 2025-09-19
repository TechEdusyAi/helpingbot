from __future__ import annotations

from types import SimpleNamespace

from config.settings import TradingBotSettings
from contextlib import contextmanager

import presentation.cli as cli


def test_main_runs_once(monkeypatch):
    settings = TradingBotSettings(instruments=["EURUSD"], poll_interval_seconds=1)
    monkeypatch.setattr(cli, "ConfigLoader", lambda: SimpleNamespace(load=lambda path: settings))

    class DummyService:
        def __init__(self) -> None:
            self.run_once_called = False

        def run_once(self) -> None:
            self.run_once_called = True

        def start(self) -> None:  # pragma: no cover - not used
            raise AssertionError("Should not start")

    dummy_service = DummyService()
    monkeypatch.setattr(cli, "build_service", lambda _settings: dummy_service)

    exit_code = cli.main(["--once"])
    assert exit_code == 0
    assert dummy_service.run_once_called


def test_main_handles_interrupt(monkeypatch):
    settings = TradingBotSettings(instruments=["EURUSD"], poll_interval_seconds=1)
    monkeypatch.setattr(cli, "ConfigLoader", lambda: SimpleNamespace(load=lambda path: settings))

    class DummyService:
        def __init__(self) -> None:
            self.stop_called = False

        def run_once(self) -> None:  # pragma: no cover - not used
            raise AssertionError

        def start(self) -> None:
            raise KeyboardInterrupt

        def stop(self) -> None:
            self.stop_called = True

    dummy_service = DummyService()
    monkeypatch.setattr(cli, "build_service", lambda _settings: dummy_service)

    @contextmanager
    def fake_graceful(handler):
        handler(0, None)
        yield

    monkeypatch.setattr(cli, "graceful_interrupt", fake_graceful)

    exit_code = cli.main([])
    assert exit_code == 0
    assert dummy_service.stop_called

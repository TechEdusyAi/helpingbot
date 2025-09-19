from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from config.loader import ConfigLoader
from config.settings import TradingBotSettings, update_dataclass


def test_loader_reads_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({
            "instruments": ["GBPUSD"],
            "strategy": {"short_window": 3, "long_window": 8},
        })
    )
    loader = ConfigLoader()
    settings = loader.load(config_path)
    assert settings.instruments == ["GBPUSD"]
    assert settings.strategy.short_window == 3


def test_loader_applies_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADING_BOT_INSTRUMENTS__0", "USDJPY")
    loader = ConfigLoader()
    settings = loader.load(None)
    assert settings.instruments[0] == "USDJPY"


def test_update_dataclass_handles_nested():
    settings = TradingBotSettings(instruments=["EURUSD"])
    update_dataclass(settings, {"strategy": {"short_window": 4}})
    assert settings.strategy.short_window == 4

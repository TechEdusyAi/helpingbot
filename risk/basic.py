"""Risk management implementations."""

from collections.abc import Sequence
from dataclasses import dataclass

from config.settings import RiskSettings
from domain.interfaces import RiskAssessment, RiskManager
from domain.models import Candle, Order, OrderSide, SignalType, TradingSignal
from utils.validation import ensure_positive_number


@dataclass
class BasicRiskAssessment:
    """Concrete risk assessment structure used within the application."""

    approved: bool
    reason: str | None
    order: Order | None


class BasicRiskManager(RiskManager):
    """Applies simple risk rules such as position sizing and stop levels."""

    def __init__(self, settings: RiskSettings) -> None:
        ensure_positive_number(settings.max_position_size, "Max position size must be positive")
        self._settings = settings

    def assess(self, signal: TradingSignal, candles: Sequence[Candle]) -> RiskAssessment:
        """Evaluate a signal and return an executable order if allowed."""

        if signal.signal_type == SignalType.HOLD:
            return BasicRiskAssessment(approved=False, reason="Hold signal", order=None)
        last_candle = candles[-1]
        price = last_candle.close
        quantity = min(self._settings.max_position_size, self._settings.max_position_size * (signal.strength or 1.0))
        side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
        stop_loss, take_profit = self._derive_protection_levels(price, side)
        order = Order(
            instrument=signal.instrument,
            side=side,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return BasicRiskAssessment(approved=True, reason=None, order=order)

    def _derive_protection_levels(self, price: float, side: OrderSide) -> tuple[float | None, float | None]:
        if side == OrderSide.BUY:
            stop_loss = price * (1 - self._settings.stop_loss_pct)
            take_profit = price * (1 + self._settings.take_profit_pct)
        else:
            stop_loss = price * (1 + self._settings.stop_loss_pct)
            take_profit = price * (1 - self._settings.take_profit_pct)
        return stop_loss, take_profit

"""
Paper Trading Simulator.
Simula operaciones basadas en scoring, calcula P&L, trackea estadísticas.

Parámetros:
  Capital inicial: 10,000€
  Risk per trade: 2% del capital
  Stop loss: -3%
  Take profit: +5%
  Max hold: 30 días
  Exit por: stop/target/score bajo (<50) / timeout
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class OperationStatus(Enum):
    OPEN = "open"
    CLOSED_PROFIT = "closed_profit"
    CLOSED_LOSS = "closed_loss"
    CLOSED_TIMEOUT = "closed_timeout"
    CLOSED_SCORE = "closed_score"


@dataclass
class Trade:
    """Representa una operación simulada."""
    ticker: str
    entry_price: float
    entry_score: float
    entry_date: datetime
    quantity: int = 0

    exit_price: float | None = None
    exit_date: datetime | None = None
    exit_reason: str | None = None
    status: OperationStatus = OperationStatus.OPEN

    pnl_usd: float = 0.0
    pnl_pct: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.status == OperationStatus.OPEN

    @property
    def days_held(self) -> int:
        if self.is_open:
            return (datetime.now() - self.entry_date).days
        else:
            return (self.exit_date - self.entry_date).days if self.exit_date else 0

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "entry_price": round(self.entry_price, 2),
            "entry_score": round(self.entry_score, 1),
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "quantity": self.quantity,
            "exit_price": round(self.exit_price, 2) if self.exit_price else None,
            "exit_date": self.exit_date.isoformat() if self.exit_date else None,
            "exit_reason": self.exit_reason,
            "status": self.status.value,
            "pnl_usd": round(self.pnl_usd, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "days_held": self.days_held,
        }


@dataclass
class Portfolio:
    """Portfolio simulado."""
    initial_capital: float = 10000.0
    risk_per_trade: float = 0.02  # 2%
    stop_loss_pct: float = -0.03  # -3%
    take_profit_pct: float = 0.05  # +5%
    max_hold_days: int = 30

    current_capital: float = field(default_factory=lambda: 10000.0)
    trades: list[Trade] = field(default_factory=list)

    def __post_init__(self):
        self.current_capital = self.initial_capital

    @property
    def total_pnl(self) -> float:
        """P&L total acumulado."""
        return sum(t.pnl_usd for t in self.trades if not t.is_open)

    @property
    def total_pnl_pct(self) -> float:
        """P&L % sobre capital inicial."""
        return (self.total_pnl / self.initial_capital * 100) if self.initial_capital else 0.0

    @property
    def open_positions(self) -> list[Trade]:
        return [t for t in self.trades if t.is_open]

    @property
    def closed_trades(self) -> list[Trade]:
        return [t for t in self.trades if not t.is_open]

    @property
    def win_rate(self) -> float:
        """% de trades ganadores."""
        if not self.closed_trades:
            return 0.0
        wins = len([t for t in self.closed_trades if t.pnl_usd > 0])
        return (wins / len(self.closed_trades) * 100) if self.closed_trades else 0.0

    @property
    def avg_win(self) -> float:
        """P&L promedio en trades ganadores."""
        wins = [t.pnl_usd for t in self.closed_trades if t.pnl_usd > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        """P&L promedio en trades perdedores."""
        losses = [t.pnl_usd for t in self.closed_trades if t.pnl_usd < 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def risk_reward_ratio(self) -> float:
        """Ratio de riesgo/recompensa."""
        if not self.avg_loss or self.avg_loss >= 0:
            return 0.0
        return abs(self.avg_win / self.avg_loss) if self.avg_loss else 0.0

    @property
    def max_drawdown(self) -> float:
        """Máxima caída desde peak."""
        if not self.closed_trades:
            return 0.0

        cumsum = 0.0
        peak = 0.0
        max_dd = 0.0

        for t in self.closed_trades:
            cumsum += t.pnl_usd
            if cumsum > peak:
                peak = cumsum
            dd = peak - cumsum
            max_dd = max(max_dd, dd)

        return max_dd

    def enter_position(self, ticker: str, price: float, score: float) -> Trade:
        """
        Abre una nueva posición.
        Cantidad = (capital * risk_per_trade) / stop_loss_pct
        """
        risk_amount = self.current_capital * self.risk_per_trade
        stop_distance = price * abs(self.stop_loss_pct)
        quantity = int(risk_amount / stop_distance) if stop_distance > 0 else 0

        if quantity <= 0:
            return None

        trade = Trade(
            ticker=ticker,
            entry_price=price,
            entry_score=score,
            entry_date=datetime.now(),
            quantity=quantity,
        )

        self.trades.append(trade)
        self.current_capital -= quantity * price

        return trade

    def exit_position(self, trade: Trade, exit_price: float,
                      reason: str = "manual", status: OperationStatus = None) -> Trade:
        """Cierra una posición abierta."""
        if not trade.is_open:
            return trade

        trade.exit_price = exit_price
        trade.exit_date = datetime.now()
        trade.exit_reason = reason

        # Calcular P&L
        gross_pnl = (exit_price - trade.entry_price) * trade.quantity
        trade.pnl_usd = gross_pnl
        trade.pnl_pct = ((exit_price / trade.entry_price) - 1) * 100

        # Asignar status si no se proporciona
        if status is None:
            if trade.pnl_usd > 0:
                trade.status = OperationStatus.CLOSED_PROFIT
            else:
                trade.status = OperationStatus.CLOSED_LOSS
        else:
            trade.status = status

        # Actualizar capital
        self.current_capital += exit_price * trade.quantity

        return trade

    def check_and_close_positions(self, prices: dict[str, float], scores: dict[str, float]):
        """
        Revisa todas las posiciones abiertas y cierra si se cumplen condiciones:
        - Stop loss alcanzado
        - Target (take profit) alcanzado
        - Score < 50
        - Max hold days superado
        """
        for trade in self.open_positions:
            ticker = trade.ticker
            current_price = prices.get(ticker)
            current_score = scores.get(ticker)

            if current_price is None:
                continue

            # 1. Stop loss
            if current_price <= trade.entry_price * (1 + self.stop_loss_pct):
                self.exit_position(trade, current_price, "stop_loss",
                                 OperationStatus.CLOSED_LOSS)
                continue

            # 2. Take profit
            if current_price >= trade.entry_price * (1 + self.take_profit_pct):
                self.exit_position(trade, current_price, "target",
                                 OperationStatus.CLOSED_PROFIT)
                continue

            # 3. Score bajó mucho (<50)
            if current_score is not None and current_score < 50:
                self.exit_position(trade, current_price, "score_drop",
                                 OperationStatus.CLOSED_SCORE)
                continue

            # 4. Max hold days
            if trade.days_held >= self.max_hold_days:
                self.exit_position(trade, current_price, "timeout",
                                 OperationStatus.CLOSED_TIMEOUT)
                continue

    def get_portfolio_summary(self) -> dict:
        """Resumen del portfolio."""
        return {
            "initial_capital": round(self.initial_capital, 2),
            "current_capital": round(self.current_capital, 2),
            "total_pnl": round(self.total_pnl, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 2),
            "num_open_positions": len(self.open_positions),
            "num_closed_trades": len(self.closed_trades),
            "win_rate_pct": round(self.win_rate, 1),
            "avg_win": round(self.avg_win, 2),
            "avg_loss": round(self.avg_loss, 2),
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "max_drawdown": round(self.max_drawdown, 2),
        }

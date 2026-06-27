"""
Paper Trading Simulator.
Simula operaciones basadas en scoring, calcula P&L, trackea estadísticas.

Parámetros por defecto:
  Capital inicial:    $10,000
  Risk per trade:     2% del capital
  Max posición:       15% del capital por trade
  Max posiciones:     8 simultáneas
  Stop loss:          -8%  (revisión diaria — acomoda gaps overnight)
  Take profit:        +15%
  Max hold:           30 días
  Cooldown post-stop: 5 días sin re-entrar en el mismo ticker
  Límite sector:      2 posiciones abiertas por sector
  Exit por: stop / target / score bajo (<50) / timeout
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
    sector: str = "otros"

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
            "sector": self.sector,
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
    risk_per_trade: float = 0.02       # 2% de riesgo por trade
    max_position_pct: float = 0.15     # máx 15% del capital en una posición
    max_open_positions: int = 8        # máx posiciones simultáneas
    stop_loss_pct: float = -0.08       # -8% stop (revisión diaria)
    take_profit_pct: float = 0.15      # +15% take profit
    max_hold_days: int = 30
    cooldown_days: int = 3             # días de espera tras stop-out en el mismo ticker
    max_sector_positions: int = 2      # máx posiciones abiertas por sector

    current_capital: float = field(default_factory=lambda: 10000.0)
    trades: list[Trade] = field(default_factory=list)

    def __post_init__(self):
        self.current_capital = self.initial_capital

    # ── Propiedades ──────────────────────────────────────────────

    @property
    def total_pnl(self) -> float:
        """P&L realizado (trades cerrados)."""
        return sum(t.pnl_usd for t in self.trades if not t.is_open)

    @property
    def total_pnl_pct(self) -> float:
        return (self.total_pnl / self.initial_capital * 100) if self.initial_capital else 0.0

    def equity(self, current_prices: dict[str, float] | None = None) -> float:
        """
        Valor total de la cartera = capital líquido + valor de mercado de posiciones abiertas.
        Si no se pasan precios actuales, usa los precios de entrada como aproximación.
        """
        open_value = sum(
            t.quantity * (current_prices.get(t.ticker, t.entry_price) if current_prices else t.entry_price)
            for t in self.open_positions
        )
        return round(self.current_capital + open_value, 2)

    def unrealized_pnl(self, current_prices: dict[str, float]) -> float:
        """P&L latente de posiciones abiertas."""
        return round(sum(
            (current_prices.get(t.ticker, t.entry_price) - t.entry_price) * t.quantity
            for t in self.open_positions
        ), 2)

    def total_pnl_combined(self, current_prices: dict[str, float]) -> float:
        """P&L realizado + latente."""
        return round(self.total_pnl + self.unrealized_pnl(current_prices), 2)

    @property
    def open_positions(self) -> list[Trade]:
        return [t for t in self.trades if t.is_open]

    @property
    def closed_trades(self) -> list[Trade]:
        return [t for t in self.trades if not t.is_open]

    @property
    def win_rate(self) -> float:
        if not self.closed_trades:
            return 0.0
        wins = len([t for t in self.closed_trades if t.pnl_usd > 0])
        return (wins / len(self.closed_trades) * 100)

    @property
    def avg_win(self) -> float:
        wins = [t.pnl_usd for t in self.closed_trades if t.pnl_usd > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t.pnl_usd for t in self.closed_trades if t.pnl_usd < 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def risk_reward_ratio(self) -> float:
        if not self.avg_loss or self.avg_loss >= 0:
            return 0.0
        return abs(self.avg_win / self.avg_loss)

    @property
    def max_drawdown(self) -> float:
        if not self.closed_trades:
            return 0.0
        cumsum = peak = max_dd = 0.0
        for t in self.closed_trades:
            cumsum += t.pnl_usd
            if cumsum > peak:
                peak = cumsum
            max_dd = max(max_dd, peak - cumsum)
        return max_dd

    # ── Checks de entrada ────────────────────────────────────────

    def _in_cooldown(self, ticker: str) -> bool:
        """True si este ticker tuvo un stop-out en los últimos cooldown_days."""
        cutoff = datetime.now() - timedelta(days=self.cooldown_days)
        return any(
            t.ticker == ticker
            and t.exit_reason == "stop_loss"
            and t.exit_date is not None
            and t.exit_date >= cutoff
            for t in self.closed_trades
        )

    def _sector_count(self, sector: str) -> int:
        """Número de posiciones abiertas en un sector."""
        return sum(1 for t in self.open_positions if t.sector == sector)

    def can_enter(self, ticker: str, sector: str) -> tuple[bool, str]:
        """Retorna (puede_entrar, motivo_si_no)."""
        if any(t.ticker == ticker for t in self.open_positions):
            return False, "Ya hay posición abierta en este ticker"
        if len(self.open_positions) >= self.max_open_positions:
            return False, f"Máximo de posiciones alcanzado ({self.max_open_positions})"
        if self._in_cooldown(ticker):
            return False, f"Cooldown activo ({self.cooldown_days}d tras stop-out)"
        if sector and sector != "otros" and self._sector_count(sector) >= self.max_sector_positions:
            return False, f"Límite de sector '{sector}' alcanzado ({self.max_sector_positions} posiciones)"
        return True, ""

    # ── Operaciones ──────────────────────────────────────────────

    def enter_position(self, ticker: str, price: float, score: float,
                       sector: str = "otros") -> Trade | None:
        """
        Abre una nueva posición respetando todos los límites.

        Sizing: risk_amount / stop_distance, pero capeado al max_position_pct del capital.
        """
        ok, reason = self.can_enter(ticker, sector)
        if not ok:
            return None

        if price <= 0:
            return None

        # Cantidad basada en riesgo
        risk_amount = self.current_capital * self.risk_per_trade
        stop_distance_per_share = price * abs(self.stop_loss_pct)
        qty_by_risk = int(risk_amount / stop_distance_per_share) if stop_distance_per_share > 0 else 0

        # Cap por máximo de posición
        max_qty_by_size = int((self.current_capital * self.max_position_pct) / price)

        quantity = min(qty_by_risk, max_qty_by_size)

        if quantity <= 0:
            return None

        # Verificar que hay capital suficiente
        cost = quantity * price
        if cost > self.current_capital:
            quantity = int(self.current_capital / price)
        if quantity <= 0:
            return None

        trade = Trade(
            ticker=ticker,
            entry_price=price,
            entry_score=score,
            entry_date=datetime.now(),
            quantity=quantity,
            sector=sector,
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
        trade.pnl_usd = (exit_price - trade.entry_price) * trade.quantity
        trade.pnl_pct = ((exit_price / trade.entry_price) - 1) * 100

        if status is None:
            trade.status = OperationStatus.CLOSED_PROFIT if trade.pnl_usd > 0 else OperationStatus.CLOSED_LOSS
        else:
            trade.status = status

        self.current_capital += exit_price * trade.quantity
        return trade

    def check_and_close_positions(self, prices: dict[str, float], scores: dict[str, float]):
        """Revisa posiciones abiertas y cierra las que cumplen condiciones de salida."""
        for trade in list(self.open_positions):
            current_price = prices.get(trade.ticker)
            if current_price is None:
                continue

            stop_threshold = trade.entry_price * (1 + self.stop_loss_pct)

            if current_price <= stop_threshold:
                self.exit_position(trade, current_price, "stop_loss", OperationStatus.CLOSED_LOSS)
                continue

            if current_price >= trade.entry_price * (1 + self.take_profit_pct):
                self.exit_position(trade, current_price, "target", OperationStatus.CLOSED_PROFIT)
                continue

            current_score = scores.get(trade.ticker)
            if current_score is not None and current_score < 50:
                self.exit_position(trade, current_price, "score_drop", OperationStatus.CLOSED_SCORE)
                continue

            if trade.days_held >= self.max_hold_days:
                self.exit_position(trade, current_price, "timeout", OperationStatus.CLOSED_TIMEOUT)

    def get_portfolio_summary(self) -> dict:
        return {
            "initial_capital":    round(self.initial_capital, 2),
            "current_capital":    round(self.current_capital, 2),
            "total_pnl":          round(self.total_pnl, 2),
            "total_pnl_pct":      round(self.total_pnl_pct, 2),
            "num_open_positions": len(self.open_positions),
            "num_closed_trades":  len(self.closed_trades),
            "win_rate_pct":       round(self.win_rate, 1),
            "avg_win":            round(self.avg_win, 2),
            "avg_loss":           round(self.avg_loss, 2),
            "risk_reward_ratio":  round(self.risk_reward_ratio, 2),
            "max_drawdown":       round(self.max_drawdown, 2),
        }

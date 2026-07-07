"""Configuración del bot Polymarket BTC Up/Down (paper trading)."""
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Config:
    # Mercado
    window_seconds: int = 300          # ventanas de 5 minutos
    tick_seconds: float = 5.0          # frecuencia del loop principal

    # Capital y riesgo
    bankroll_start: float = 1000.0     # USD virtuales
    min_edge: float = 0.08             # v2.3 (autopsia 2026-07-07, n=84): banda 0.05-0.08
                                       # perdía (39% winrate vs 43% breakeven, -$120); la banda
                                       # 0.08-0.12 ganaba con significancia (54.3%, z=+2.2, +$244)
    max_edge: float = 0.12             # edge mayor = bandera roja (el mercado sabe algo), no operar
    max_stake_pct: float = 0.02        # máximo 2% del bankroll por operación
    kelly_fraction: float = 0.25       # fracción de Kelly (conservador)
    max_open_per_window: int = 1       # operaciones máximas por ventana
    min_book_size: float = 50.0        # tamaño mínimo (shares) en el mejor ask
    fee: float = 0.0                   # comisión por lado (Polymarket: 0 actualmente)
    stop_after_losses: int = 5         # kill-switch: sin trades nuevos tras N pérdidas seguidas
    killswitch_cooldown_sec: int = 1800  # pausa tras saltar el kill-switch; luego retoma solo
    market_prior_weight: float = 0.3   # peso del precio del mercado como prior en la probabilidad

    # Modelo
    vol_lookback_min: int = 120        # minutos de histórico para volatilidad realizada
    vol_refresh_sec: int = 60          # recalcular sigma/drift cada X segundos
    drift_lookback_min: int = 30       # minutos para estimar la tendencia (drift)
    drift_weight: float = 0.0          # v2.2: desactivado — autopsia 2026-07-02 mostró sesgo
                                        # sistemático a favor de "Up" (26% winrate, -$153.76 en
                                        # 19 trades) vs "Down" (56%, +$63.03 en 16); el momentum
                                        # de 30min no se sostenía a 5min vista

    # Timing de ventana
    open_capture_max_delay: int = 12   # s máx tras inicio de ventana para fijar precio open
    no_trade_last_sec: int = 45        # no abrir en los últimos X s de la ventana

    # Resolución
    settle_poll_sec: int = 30          # cada cuánto consultar liquidación oficial en Gamma
    settle_timeout_sec: int = 900      # tras 15 min sin liquidación oficial, resolver con proxy

    # Persistencia
    db_path: str = str(PROJECT_ROOT / "paper_trades.db")

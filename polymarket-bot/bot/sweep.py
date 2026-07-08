"""Simulación de barrido de beneficios en máximos históricos (high-water mark).

Política candidata para la fase real (2026-07-07, acordada con Luis): capital
de trabajo fijo + barrido de un % de cada ganancia nueva en cada máximo
histórico, a una reserva que el bot nunca vuelve a arriesgar. Aquí se calcula
en modo SOMBRA sobre el histórico de paper trading: no toca el bankroll ni el
sizing real del bot, solo lo muestra para poder evaluar la política con datos
antes de aplicarla de verdad.

Importante: el sizing real de cada operación es un % del bankroll (ver
Config.max_stake_pct / kelly_fraction), así que si esta política se aplicase
en real, las apuestas futuras usarían el capital EXPUESTO (menor), no el
bankroll libre. Esta simulación no reproduce ese efecto de segundo orden.
"""
from dataclasses import dataclass


@dataclass
class SweepPoint:
    resolved_ts: float
    pnl: float
    equity_free: float      # bankroll sin barrido (lo que el bot ya reporta)
    equity_exposed: float   # capital que seguiría expuesto al bot con barrido
    reserve: float          # ganancia ya asegurada, fuera de riesgo
    peak_free: float
    peak_exposed: float


def compute_sweep_curve(
    trades: list[tuple[float, float]],
    bankroll_start: float,
    sweep_fraction: float = 0.5,
) -> list[SweepPoint]:
    """trades: lista de (resolved_ts, pnl) ordenada cronológicamente."""
    equity_free = bankroll_start
    peak_free = bankroll_start
    equity_exposed = bankroll_start
    peak_exposed = bankroll_start
    reserve = 0.0
    out = []
    for ts, pnl in trades:
        equity_free += pnl
        peak_free = max(peak_free, equity_free)

        equity_exposed += pnl
        if equity_exposed > peak_exposed:
            ganancia_nueva = equity_exposed - peak_exposed
            barrido = ganancia_nueva * sweep_fraction
            reserve += barrido
            equity_exposed -= barrido
            peak_exposed = equity_exposed

        out.append(SweepPoint(ts, pnl, equity_free, equity_exposed, reserve,
                              peak_free, peak_exposed))
    return out

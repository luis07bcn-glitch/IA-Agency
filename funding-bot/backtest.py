"""Backtest honesto de cash-and-carry sobre el histórico de funding de Kraken.

Posición simulada: long spot + short perpetuo, notional constante 1.0.
Cada hora en posición se acumula relative_rate (si es negativo, se paga).
Sin fill-model que inventar: el funding es un dato publicado, no una hipótesis.

Estrategias comparadas:
  - always-on: siempre en posición (referencia)
  - umbral con histéresis: entra si la media móvil de --window-hours horas
    anualizada supera --enter-ann; sale si cae por debajo de --exit-ann.

Costes (conservadores, tier base de Kraken, todo taker):
  spot 0.40% + futuros 0.05% por lado => 0.45% por lado, 0.90% ida y vuelta.

Aproximaciones asumidas (documentadas en README): ignora el ruido mark-to-market
de la base perp-spot (pequeña y mean-reverting en perpetuos, converge al salir)
y el coste de margen del short. El PnL aquí es SOLO funding menos costes.

Gate de la Fase 0 (escrito antes de mirar los datos, 2026-07-12):
  retorno neto anualizado > 8% con drawdown máximo < 3% => pasa a paper.
"""

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

HOURS_YEAR = 24 * 365


@dataclass
class Result:
    name: str
    hours_total: int
    hours_in_position: int
    round_trips: int
    gross_return: float      # funding acumulado (fracción del notional)
    cost_drag: float         # costes totales de entrada/salida
    max_drawdown: float      # sobre la curva de equity neta

    @property
    def net_return(self) -> float:
        return self.gross_return - self.cost_drag

    def annualized(self, value: float) -> float:
        years = self.hours_total / HOURS_YEAR
        return value / years if years > 0 else 0.0


def load_series(db: Path, symbol: str) -> list[tuple[datetime, float]]:
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT ts, relative_rate FROM funding_rates "
        "WHERE symbol=? AND relative_rate IS NOT NULL ORDER BY ts",
        (symbol,),
    ).fetchall()
    conn.close()
    out = []
    for ts, rate in rows:
        ts_clean = ts.split(".")[0].rstrip("Z")
        out.append((datetime.strptime(ts_clean, "%Y-%m-%dT%H:%M:%S"), float(rate)))
    return out


def simulate(series: list[tuple[datetime, float]], window: int,
             enter_ann: float, exit_ann: float, cost_side: float,
             always_on: bool) -> Result:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    gross = 0.0
    costs = 0.0
    # cost_side = coste de UN evento (entrada O salida) con sus dos patas
    # (spot 0.40% + perp 0.05% = 0.45%); ida y vuelta completa = 2 eventos.
    in_pos = always_on
    hours_in = 0
    round_trips = 1 if always_on else 0
    if always_on:
        costs += cost_side  # entrada al inicio; la salida se carga al final
        equity -= cost_side
    window_sum = 0.0
    rates_window: list[float] = []

    for i, (_, rate) in enumerate(series):
        rates_window.append(rate)
        window_sum += rate
        if len(rates_window) > window:
            window_sum -= rates_window.pop(0)
        trailing_ann = (window_sum / len(rates_window)) * HOURS_YEAR

        if not always_on and len(rates_window) == window:
            if not in_pos and trailing_ann > enter_ann:
                in_pos = True
                round_trips += 1
                equity -= cost_side
                costs += cost_side
            elif in_pos and trailing_ann < exit_ann:
                in_pos = False
                equity -= cost_side
                costs += cost_side

        if in_pos:
            equity += rate
            gross += rate
            hours_in += 1

        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    if in_pos:  # cierre al final de la muestra: la salida también cuesta
        equity -= cost_side
        costs += cost_side
        max_dd = max(max_dd, peak - equity)

    return Result(
        name="always-on" if always_on else
             f"umbral(entrada>{enter_ann:.0%}, salida<{exit_ann:.0%}, ventana {window}h)",
        hours_total=len(series),
        hours_in_position=hours_in,
        round_trips=round_trips,
        gross_return=gross,
        cost_drag=costs,
        max_drawdown=max_dd,
    )


def describe(series: list[tuple[datetime, float]]) -> None:
    n = len(series)
    first, last = series[0][0], series[-1][0]
    days = (last - first).total_seconds() / 86400
    positive = sum(1 for _, r in series if r > 0)
    mean_ann = sum(r for _, r in series) / n * HOURS_YEAR
    # huecos: entradas que no son consecutivas a 1h
    gaps = sum(1 for i in range(1, n)
               if series[i][0] - series[i - 1][0] != timedelta(hours=1))
    # mejor y peor tramo de 30 días (720h)
    win = 24 * 30
    best = worst = None
    if n > win:
        cumsum = [0.0]
        for _, r in series:
            cumsum.append(cumsum[-1] + r)
        sums30 = [cumsum[i + win] - cumsum[i] for i in range(n - win)]
        best, worst = max(sums30), min(sums30)
    print(f"  muestra: {n} horas ({days:.0f} días, {first:%Y-%m-%d} .. {last:%Y-%m-%d}), "
          f"{gaps} huecos")
    print(f"  funding positivo el {positive / n:.1%} de las horas; "
          f"media anualizada {mean_ann:+.2%}")
    if best is not None:
        print(f"  mejor tramo 30d: {best:+.2%} | peor tramo 30d: {worst:+.2%}")


def report(res: Result, gate_return: float, gate_dd: float) -> None:
    net_ann = res.annualized(res.net_return)
    gross_ann = res.annualized(res.gross_return)
    verdict = ("PASA el gate" if net_ann > gate_return and res.max_drawdown < gate_dd
               else "NO pasa el gate")
    pct_in = res.hours_in_position / res.hours_total if res.hours_total else 0
    print(f"  [{res.name}]")
    print(f"    bruto anualizado {gross_ann:+.2%} | costes totales {res.cost_drag:.2%} "
          f"({res.round_trips} entradas, en posición {pct_in:.0%} del tiempo)")
    print(f"    NETO anualizado {net_ann:+.2%} | drawdown máx {res.max_drawdown:.2%} "
          f"=> {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(Path(__file__).parent / "funding.db"))
    ap.add_argument("--symbols", default="PF_XBTUSD,PF_ETHUSD")
    ap.add_argument("--window-hours", type=int, default=168,
                    help="ventana de la media móvil (defecto 168h = 7 días)")
    ap.add_argument("--enter-ann", type=float, default=0.05,
                    help="entra si la media anualizada supera esto (defecto 0.05)")
    ap.add_argument("--exit-ann", type=float, default=0.0,
                    help="sale si cae por debajo (defecto 0.0)")
    ap.add_argument("--cost-side", type=float, default=0.0045,
                    help="coste por lado spot+perp (defecto 0.0045 = 0.45%%)")
    ap.add_argument("--gate-return", type=float, default=0.08)
    ap.add_argument("--gate-dd", type=float, default=0.03)
    args = ap.parse_args()

    for symbol in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        series = load_series(Path(args.db), symbol)
        print(f"\n=== {symbol} ===")
        if len(series) < args.window_hours * 2:
            print("  datos insuficientes — ejecuta collector.py --backfill")
            continue
        describe(series)
        report(simulate(series, args.window_hours, args.enter_ann, args.exit_ann,
                        args.cost_side, always_on=True),
               args.gate_return, args.gate_dd)
        report(simulate(series, args.window_hours, args.enter_ann, args.exit_ann,
                        args.cost_side, always_on=False),
               args.gate_return, args.gate_dd)


if __name__ == "__main__":
    main()

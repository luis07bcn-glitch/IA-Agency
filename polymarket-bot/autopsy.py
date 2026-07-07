"""Autopsia automática del bot: calibración, sesgos y propuestas de mejora.

Analiza trades resueltos y señales registradas (tabla signals) y solo
PROPONE cambios cuando hay muestra suficiente (n >= MIN_N y |z| >= 2).
Nunca aplica nada: el protocolo sigue siendo un cambio por iteración,
decidido por un humano.

Uso:
    venv\\Scripts\\python.exe polymarket-bot\\autopsy.py
    venv\\Scripts\\python.exe polymarket-bot\\autopsy.py --since 1783322786
"""
import argparse
import math
import sqlite3
import sys
from pathlib import Path

# la consola de Windows suele ser cp1252; evitar UnicodeEncodeError
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = Path(__file__).resolve().parent / "paper_trades.db"
MIN_N = 30      # observaciones mínimas para proponer nada
Z_FLAG = 2.0    # |z| mínimo para considerar una desviación real y no ruido
SLIPPAGE = 0.01  # céntimos por share que asumimos de ejecución peor que el ask visto


def z_vs(wins: int, n: int, p0: float) -> float:
    """Z-score del winrate observado frente a la referencia p0."""
    if n == 0 or not 0 < p0 < 1:
        return 0.0
    se = math.sqrt(p0 * (1 - p0) / n)
    return ((wins / n) - p0) / se


def fmt_group(label: str, rows: list[dict]) -> str:
    n = len(rows)
    if n == 0:
        return f"  {label:<22} n=0"
    wins = sum(1 for r in rows if r["won"])
    pnl = sum(r.get("pnl") or 0.0 for r in rows)
    avg_price = sum(r["price"] for r in rows) / n
    z = z_vs(wins, n, avg_price)  # breakeven de comprar a ese precio medio
    return (f"  {label:<22} n={n:<4} winrate={wins / n:5.1%} "
            f"breakeven={avg_price:5.1%} z={z:+.1f} pnl={pnl:+9.2f}")


def brier(rows: list[dict], key: str) -> float:
    return sum((r[key] - (1.0 if r["won"] else 0.0)) ** 2 for r in rows) / len(rows)


def pnl_with_slippage(price: float, stake: float, won: bool) -> float:
    """PnL recalculado asumiendo ejecución SLIPPAGE peor que el ask visto."""
    eff = min(price + SLIPPAGE, 0.999)
    return stake * (1.0 / eff - 1.0) if won else -stake


def load_trades(conn, since: float) -> list[dict]:
    cur = conn.execute(
        "SELECT side, price, model_p, edge, pnl, status, stake FROM trades"
        " WHERE status != 'open' AND ts >= ? ORDER BY ts", (since,))
    return [
        {"side": s, "price": p, "model_p": mp, "edge": e, "pnl": pnl,
         "won": st == "won",
         "pnl_adj": pnl_with_slippage(p, stake, st == "won")}
        for s, p, mp, e, pnl, st, stake in cur.fetchall()
    ]


def load_signals(conn, since: float) -> list[dict]:
    """Primera señal por (ventana, acción), solo de ventanas ya resueltas."""
    cur = conn.execute(
        "SELECT s.window_start, s.side, s.model_p, s.ask, s.edge, s.action,"
        " w.outcome FROM signals s"
        " JOIN windows w ON w.window_start = s.window_start"
        " WHERE w.outcome IS NOT NULL AND s.ts >= ? ORDER BY s.ts", (since,))
    first: dict[tuple, dict] = {}
    for ws, side, mp, ask, e, action, outcome in cur.fetchall():
        first.setdefault((ws, action), {
            "side": side, "price": ask, "model_p": mp, "edge": e,
            "action": action, "won": side == outcome,
        })
    return list(first.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, default=0.0,
                    help="timestamp unix: analizar solo desde ahí (p.ej. inicio de una versión)")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    trades = load_trades(conn, args.since)
    signals = load_signals(conn, args.since)
    proposals: list[str] = []

    print("=" * 70)
    print("AUTOPSIA POLYMARKET BOT")
    print("=" * 70)

    if not trades:
        print("Sin trades resueltos en el rango pedido.")
        return

    n = len(trades)
    wins = sum(1 for t in trades if t["won"])
    pnl = sum(t["pnl"] for t in trades)
    pnl_adj = sum(t["pnl_adj"] for t in trades)
    print(f"\nGLOBAL: n={n} winrate={wins / n:.1%} pnl={pnl:+.2f}"
          f" | pnl tras slippage {SLIPPAGE:.2f}: {pnl_adj:+.2f}"
          f" ({'sobrevive' if pnl_adj > 0 else 'NO sobrevive'})")

    print("\nPOR LADO:")
    for side in ("Up", "Down"):
        sub = [t for t in trades if t["side"] == side]
        print(fmt_group(side, sub))
        if len(sub) >= MIN_N:
            z = z_vs(sum(1 for t in sub if t["won"]), len(sub),
                     sum(t["price"] for t in sub) / len(sub))
            if z <= -Z_FLAG:
                proposals.append(
                    f"El lado {side} pierde de forma significativa (z={z:+.1f}, "
                    f"n={len(sub)}): revisar el modelo para ese lado o dejar de operarlo.")

    print("\nPOR BANDA DE EDGE:")
    bands = [(0.05, 0.08), (0.08, 0.12)]
    for lo, hi in bands:
        sub = [t for t in trades if lo <= t["edge"] < hi]
        print(fmt_group(f"edge {lo:.2f}-{hi:.2f}", sub))
        if len(sub) >= MIN_N:
            z = z_vs(sum(1 for t in sub if t["won"]), len(sub),
                     sum(t["price"] for t in sub) / len(sub))
            if z <= -Z_FLAG:
                proposals.append(
                    f"La banda de edge {lo:.2f}-{hi:.2f} pierde (z={z:+.1f}, "
                    f"n={len(sub)}): plantear estrechar la banda.")

    print("\nCALIBRACIÓN (¿el modelo aporta sobre el precio del mercado?):")
    b_model = brier(trades, "model_p")
    b_market = brier(trades, "price")
    verdict = "el modelo APORTA" if b_model < b_market else "el modelo NO aporta"
    print(f"  Brier modelo={b_model:.4f} vs Brier mercado={b_market:.4f} -> {verdict}")
    if n >= MIN_N and b_model >= b_market:
        proposals.append(
            f"Con n={n}, el Brier del modelo ({b_model:.4f}) no mejora al del "
            f"mercado ({b_market:.4f}): sin ventaja real, plantear parar o rediseñar.")

    if signals:
        print("\nCONTRAFACTUAL DE SEÑALES RECHAZADAS (1ª señal por ventana):")
        for action in ("above_max_edge", "below_min_edge", "killswitch",
                       "stake_too_small", "trade"):
            sub = [s for s in signals if s["action"] == action]
            if sub:
                print(fmt_group(action, sub))
        rejected = [s for s in signals if s["action"] == "above_max_edge"]
        if len(rejected) >= MIN_N:
            z = z_vs(sum(1 for s in rejected if s["won"]), len(rejected),
                     sum(s["price"] for s in rejected) / len(rejected))
            if z >= Z_FLAG:
                proposals.append(
                    f"Las señales de bandera roja (edge>max) HABRÍAN ganado "
                    f"(z={z:+.1f}, n={len(rejected)}): plantear subir max_edge.")
    else:
        print("\nCONTRAFACTUAL: aún sin señales registradas (tabla nueva, "
              "se llena a partir de ahora).")

    print("\n" + "=" * 70)
    if proposals:
        print(f"PROPUESTAS (n>={MIN_N}, |z|>={Z_FLAG:.0f} — aplicar UNA por iteración):")
        for i, p in enumerate(proposals, 1):
            print(f"  {i}. {p}")
    else:
        print("PROPUESTAS: sin datos suficientes o sin desviaciones significativas.")
        print("Seguir acumulando trades antes de tocar nada (protocolo).")
    print("=" * 70)


if __name__ == "__main__":
    main()

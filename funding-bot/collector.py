"""Recolector de funding rates de Kraken Futures (perpetuos PF_*).

Fase 0 del proyecto funding-bot (2026-07-12): medir antes de operar.

Modos:
  --backfill      descarga el histórico completo de funding (endpoint v4) a funding.db
                  (idempotente: INSERT OR IGNORE, se puede relanzar a diario)
  --once          un snapshot de tickers (funding actual + predicción) + precio spot
  (por defecto)   bucle de snapshots cada --interval segundos (para VPS/systemd)

Sin dependencias fuera de la stdlib. Lanzar con venv\\Scripts\\python.exe.
Convención de signo: funding POSITIVO = los longs pagan a los shorts
(el cash-and-carry corto en perp COBRA cuando relative_rate > 0).
"""

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

FUTURES_API = "https://futures.kraken.com/derivatives/api"
SPOT_API = "https://api.kraken.com/0/public/Ticker"
USER_AGENT = "merakia-funding-bot/0.1"

# perpetuo lineal -> par spot de Kraken para seguir la base
SPOT_PAIR = {"PF_XBTUSD": "XBTUSD", "PF_ETHUSD": "ETHUSD"}
DEFAULT_SYMBOLS = ["PF_XBTUSD", "PF_ETHUSD"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS funding_rates (
    symbol        TEXT NOT NULL,
    ts            TEXT NOT NULL,   -- ISO UTC tal cual lo da el endpoint v4 (1 entrada/hora)
    funding_rate  REAL,            -- USD por contrato y hora (absoluto)
    relative_rate REAL,            -- adimensional por hora (funding_rate / precio)
    PRIMARY KEY (symbol, ts)
);
CREATE TABLE IF NOT EXISTS ticker_snapshots (
    ts                 INTEGER NOT NULL,  -- epoch segundos de la captura
    symbol             TEXT NOT NULL,
    mark_price         REAL,
    last               REAL,
    funding_rate       REAL,              -- funding de la hora en curso (absoluto)
    funding_prediction REAL,              -- predicción de la siguiente hora
    spot_price         REAL,              -- last del par spot equivalente
    PRIMARY KEY (symbol, ts)
);
"""


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def init_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def backfill(conn: sqlite3.Connection, symbol: str) -> None:
    data = get_json(f"{FUTURES_API}/v4/historicalfundingrates?symbol={symbol}")
    rates = data.get("rates", [])
    if not rates:
        print(f"[backfill] {symbol}: el endpoint no devolvió datos", file=sys.stderr)
        return
    before = conn.execute(
        "SELECT COUNT(*) FROM funding_rates WHERE symbol=?", (symbol,)
    ).fetchone()[0]
    conn.executemany(
        "INSERT OR IGNORE INTO funding_rates VALUES (?,?,?,?)",
        [(symbol, r["timestamp"], r.get("fundingRate"), r.get("relativeFundingRate"))
         for r in rates],
    )
    conn.commit()
    after = conn.execute(
        "SELECT COUNT(*) FROM funding_rates WHERE symbol=?", (symbol,)
    ).fetchone()[0]
    print(f"[backfill] {symbol}: {len(rates)} recibidas, {after - before} nuevas, "
          f"{after} totales ({rates[0]['timestamp']} .. {rates[-1]['timestamp']})")


def fetch_spot_prices(pairs: list[str]) -> dict[str, float]:
    # una petición por par: Kraken renombra las claves (XBTUSD -> XXBTZUSD),
    # así que pedimos de uno en uno y tomamos la única clave del resultado
    prices: dict[str, float] = {}
    for wanted in pairs:
        try:
            result = get_json(f"{SPOT_API}?pair={wanted}").get("result", {})
            if result:
                prices[wanted] = float(next(iter(result.values()))["c"][0])
        except Exception as exc:
            print(f"[spot] {wanted}: {exc}", file=sys.stderr)
    return prices


def snapshot(conn: sqlite3.Connection, symbols: list[str]) -> None:
    now = int(time.time())
    tickers = {t["symbol"]: t for t in get_json(f"{FUTURES_API}/v3/tickers")["tickers"]}
    spots = fetch_spot_prices([SPOT_PAIR[s] for s in symbols if s in SPOT_PAIR])
    for sym in symbols:
        t = tickers.get(sym)
        if not t:
            print(f"[snapshot] {sym}: no aparece en tickers", file=sys.stderr)
            continue
        conn.execute(
            "INSERT OR IGNORE INTO ticker_snapshots VALUES (?,?,?,?,?,?,?)",
            (now, sym, t.get("markPrice"), t.get("last"), t.get("fundingRate"),
             t.get("fundingRatePrediction"), spots.get(SPOT_PAIR.get(sym, ""))),
        )
        mark = t.get("markPrice") or 0
        rel_ann = (t.get("fundingRate") or 0) / mark * 24 * 365 * 100 if mark else 0
        print(f"[snapshot] {sym}: mark={mark:.1f} funding_ann={rel_ann:+.2f}% "
              f"spot={spots.get(SPOT_PAIR.get(sym, ''), '-')}")
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(Path(__file__).parent / "funding.db"))
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--backfill", action="store_true",
                    help="descarga el histórico de funding y termina")
    ap.add_argument("--once", action="store_true",
                    help="un snapshot de tickers y termina")
    ap.add_argument("--interval", type=int, default=300,
                    help="segundos entre snapshots en modo bucle (defecto 300)")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    conn = init_db(Path(args.db))

    if args.backfill:
        for sym in symbols:
            backfill(conn, sym)
        return
    if args.once:
        snapshot(conn, symbols)
        return
    print(f"bucle de snapshots cada {args.interval}s (Ctrl+C para parar)")
    while True:
        try:
            snapshot(conn, symbols)
        except Exception as exc:  # red caída no debe tumbar el recolector
            print(f"[snapshot] error: {exc}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

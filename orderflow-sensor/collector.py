# -*- coding: utf-8 -*-
"""Sensor de order flow en Kraken spot (BTC/EUR) — Fase 0: medir antes de operar.

Websocket v2 (canales book depth 25 + trade). Mantiene el libro L2 en memoria
(validado con el checksum CRC32 oficial) y cada segundo escribe un snapshot de
features en SQLite: imbalance del libro (obi1/5/10), OFI de Cont-Kukanov-
Stoikov al mejor nivel, delta/CVD del tape y distancia al VPOC intradía.
Los trades se guardan crudos (dedup por trade_id) para la futura Fase 1.

El gate de decisión está escrito en README.md ANTES de recoger datos.

Uso:
    venv\\Scripts\\python.exe orderflow-sensor\\collector.py                # indefinido (servicio)
    venv\\Scripts\\python.exe orderflow-sensor\\collector.py --duration 90  # prueba de 90s
"""
import argparse
import asyncio
import json
import sqlite3
import sys
import time
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

import websockets

if hasattr(sys.stdout, "reconfigure"):      # consola Windows cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS_URL = "wss://ws.kraken.com/v2"
REST_PAIRS = "https://api.kraken.com/0/public/AssetPairs"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    ts        REAL PRIMARY KEY,  -- epoch al escribir (alineado a segundo entero)
    mid       REAL, spread REAL, best_bid REAL, best_ask REAL,
    bid_qty1  REAL, ask_qty1 REAL, bid_qty5 REAL, ask_qty5 REAL,
    bid_qty10 REAL, ask_qty10 REAL,
    obi1      REAL, obi5 REAL, obi10 REAL,
    ofi       REAL,               -- OFI acumulado desde el snapshot anterior
    buy_vol   REAL, sell_vol REAL, delta REAL, n_trades INTEGER, max_trade REAL,
    cvd_day   REAL,               -- delta acumulado desde medianoche UTC
    vpoc      REAL, dist_vpoc REAL
);
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY, -- único por libro según Kraken (dedup natural)
    ts REAL, price REAL, qty REAL, side TEXT, ord_type TEXT
);
"""


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_ts(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def fetch_decimals(symbol: str) -> tuple[int, int]:
    """Precisión de precio/cantidad del par (para el checksum del libro)."""
    rest_pair = symbol.replace("BTC", "XBT").replace("/", "")
    try:
        req = urllib.request.Request(f"{REST_PAIRS}?pair={rest_pair}",
                                     headers={"User-Agent": "merakia-orderflow/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            info = next(iter(json.loads(resp.read())["result"].values()))
        return int(info["pair_decimals"]), int(info["lot_decimals"])
    except Exception as exc:
        log(f"AVISO: no pude leer precisiones del par ({exc}); uso 1/8 por defecto")
        return 1, 8


class BookDesync(Exception):
    """El libro local ya no es fiable: reconstruir desde snapshot nuevo."""


class State:
    def __init__(self, depth: int, bucket: float, price_dec: int, qty_dec: int):
        self.depth = depth
        self.bucket = bucket
        self.price_dec = price_dec
        self.qty_dec = qty_dec
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.book_ready = False
        self.last_book_ts = 0.0
        self.checksum_enabled = True
        self.checksum_fails = 0        # consecutivos en la conexión actual
        self.checksum_reconnects = 0
        self.started = time.time()
        # acumuladores del intervalo de snapshot
        self.ofi_accum = 0.0
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.n_trades = 0
        self.max_trade = 0.0
        # estado del día UTC
        self.day = datetime.now(timezone.utc).date()
        self.cvd_day = 0.0
        self.hist: dict[float, float] = {}   # bucket de precio -> volumen
        # contadores para el log de estado
        self.snap_count = 0
        self.total_trades = 0

    def best(self):
        if not self.bids or not self.asks:
            return None
        pb = max(self.bids)
        pa = min(self.asks)
        return pb, self.bids[pb], pa, self.asks[pa]

    def reset_interval(self):
        self.ofi_accum = 0.0
        self.buy_vol = self.sell_vol = self.max_trade = 0.0
        self.n_trades = 0


def book_checksum(state: State) -> int:
    """CRC32 oficial de Kraken v2: top 10 asks (asc) + top 10 bids (desc)."""
    def fmt(v: float, dec: int) -> str:
        return f"{v:.{dec}f}".replace(".", "").lstrip("0")
    parts = [fmt(p, state.price_dec) + fmt(q, state.qty_dec)
             for p, q in sorted(state.asks.items())[:10]]
    parts += [fmt(p, state.price_dec) + fmt(q, state.qty_dec)
              for p, q in sorted(state.bids.items(), reverse=True)[:10]]
    return zlib.crc32("".join(parts).encode())


def ofi_contribution(prev, cur) -> float:
    """OFI de Cont-Kukanov-Stoikov al mejor nivel (positivo = presión compradora)."""
    pb0, qb0, pa0, qa0 = prev
    pb1, qb1, pa1, qa1 = cur
    if pb1 > pb0:
        e_bid = qb1
    elif pb1 == pb0:
        e_bid = qb1 - qb0
    else:
        e_bid = -qb0
    if pa1 < pa0:
        e_ask = qa1
    elif pa1 == pa0:
        e_ask = qa1 - qa0
    else:
        e_ask = -qa0
    return e_bid - e_ask


def apply_book(state: State, item: dict, is_snapshot: bool):
    if is_snapshot:
        state.bids = {l["price"]: l["qty"] for l in item.get("bids", [])}
        state.asks = {l["price"]: l["qty"] for l in item.get("asks", [])}
        state.book_ready = True
    else:
        for side_key, book in (("bids", state.bids), ("asks", state.asks)):
            for l in item.get(side_key, []):
                if l["qty"] == 0:
                    book.pop(l["price"], None)
                else:
                    book[l["price"]] = l["qty"]
        # truncar al depth suscrito (los niveles que salen del top-N caducan)
        if len(state.bids) > state.depth:
            for p in sorted(state.bids)[:-state.depth]:
                del state.bids[p]
        if len(state.asks) > state.depth:
            for p in sorted(state.asks)[state.depth:]:
                del state.asks[p]
    state.last_book_ts = time.time()


def verify_book(state: State, expected):
    b = state.best()
    if b and b[0] >= b[2]:
        raise BookDesync(f"libro cruzado (bid {b[0]} >= ask {b[2]})")
    if not (state.checksum_enabled and state.book_ready and expected is not None):
        return
    if book_checksum(state) != expected:
        state.checksum_fails += 1
        if state.checksum_fails >= 3:
            raise BookDesync("checksum CRC32 discrepante 3 veces seguidas")
    else:
        state.checksum_fails = 0


def on_trades(state: State, conn: sqlite3.Connection, trades: list, is_snapshot: bool):
    rows = []
    for t in trades:
        rows.append((t.get("trade_id"), parse_ts(t["timestamp"]),
                     t["price"], t["qty"], t["side"], t.get("ord_type")))
        if is_snapshot:      # histórico de la suscripción: solo a BD, no al buffer
            continue
        qty = t["qty"]
        if t["side"] == "buy":
            state.buy_vol += qty
            state.cvd_day += qty
        else:
            state.sell_vol += qty
            state.cvd_day -= qty
        state.n_trades += 1
        state.total_trades += 1
        state.max_trade = max(state.max_trade, qty)
        bucket = round(t["price"] / state.bucket) * state.bucket
        state.hist[bucket] = state.hist.get(bucket, 0.0) + qty
    if rows:
        conn.executemany("INSERT OR IGNORE INTO trades VALUES (?,?,?,?,?,?)", rows)
        conn.commit()


def rebuild_day(state: State, conn: sqlite3.Connection):
    """Al arrancar, reconstruye CVD y VPOC del día UTC desde los trades guardados."""
    midnight = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0).timestamp()
    n = 0
    for price, qty, side in conn.execute(
            "SELECT price, qty, side FROM trades WHERE ts >= ?", (midnight,)):
        state.cvd_day += qty if side == "buy" else -qty
        bucket = round(price / state.bucket) * state.bucket
        state.hist[bucket] = state.hist.get(bucket, 0.0) + qty
        n += 1
    if n:
        log(f"día UTC reconstruido desde BD: {n} trades, cvd={state.cvd_day:+.4f}")


def write_snapshot(state: State, conn: sqlite3.Connection):
    today = datetime.now(timezone.utc).date()
    if today != state.day:      # medianoche UTC: VPOC y CVD empiezan de cero
        state.day = today
        state.cvd_day = 0.0
        state.hist = {}
        log("nuevo día UTC: VPOC y CVD reiniciados")

    b = state.best()
    stale = time.time() - state.last_book_ts > 15
    if not state.book_ready or b is None or b[0] >= b[2] or stale:
        state.reset_interval()  # sin libro fiable el intervalo no vale: hueco honesto
        return

    pb, _, pa, _ = b
    mid = (pb + pa) / 2
    bids_sorted = sorted(state.bids.items(), reverse=True)
    asks_sorted = sorted(state.asks.items())

    def qsum(levels, k):
        return sum(q for _, q in levels[:k])

    def obi(k):
        bq, aq = qsum(bids_sorted, k), qsum(asks_sorted, k)
        return (bq - aq) / (bq + aq) if bq + aq > 0 else None

    vpoc = max(state.hist.items(), key=lambda kv: kv[1])[0] if state.hist else None
    conn.execute(
        "INSERT OR REPLACE INTO snapshots VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (round(time.time()), mid, pa - pb, pb, pa,
         qsum(bids_sorted, 1), qsum(asks_sorted, 1),
         qsum(bids_sorted, 5), qsum(asks_sorted, 5),
         qsum(bids_sorted, 10), qsum(asks_sorted, 10),
         obi(1), obi(5), obi(10),
         state.ofi_accum,
         state.buy_vol, state.sell_vol, state.buy_vol - state.sell_vol,
         state.n_trades, state.max_trade,
         state.cvd_day,
         vpoc, (mid - vpoc) if vpoc is not None else None),
    )
    conn.commit()
    state.reset_interval()
    state.snap_count += 1
    if state.snap_count % 60 == 0:
        spread_bps = (pa - pb) / mid * 1e4
        log(f"mid={mid:.1f} spread={spread_bps:.2f}bps snapshots={state.snap_count} "
            f"trades={state.total_trades} cvd_día={state.cvd_day:+.4f}")


async def snapshot_loop(state: State, conn: sqlite3.Connection, interval: float):
    while True:
        await asyncio.sleep(interval - (time.time() % interval))
        try:
            write_snapshot(state, conn)
        except Exception as exc:   # un snapshot fallido no debe tumbar el sensor
            log(f"snapshot error: {exc}")


async def ws_session(state: State, conn: sqlite3.Connection, symbol: str):
    async with websockets.connect(WS_URL, ping_interval=20, close_timeout=5) as ws:
        await ws.send(json.dumps({"method": "subscribe", "params": {
            "channel": "book", "symbol": [symbol], "depth": state.depth}}))
        await ws.send(json.dumps({"method": "subscribe", "params": {
            "channel": "trade", "symbol": [symbol], "snapshot": True}}))
        async for raw in ws:
            msg = json.loads(raw)
            ch = msg.get("channel")
            if ch == "book":
                is_snap = msg.get("type") == "snapshot"
                for item in msg.get("data", []):
                    prev = state.best()
                    apply_book(state, item, is_snap)
                    if not is_snap and prev is not None:
                        cur = state.best()
                        if cur is not None:
                            state.ofi_accum += ofi_contribution(prev, cur)
                    verify_book(state, item.get("checksum"))
                if is_snap:
                    log(f"libro sincronizado ({len(state.bids)}x{len(state.asks)} niveles)")
            elif ch == "trade":
                on_trades(state, conn, msg.get("data", []),
                          msg.get("type") == "snapshot")
            elif ch in ("heartbeat", "status"):
                pass
            elif msg.get("method") in ("subscribe", "unsubscribe"):
                if not msg.get("success", True):
                    log(f"suscripción rechazada: {msg.get('error')}")


async def run(args):
    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA)
    price_dec, qty_dec = fetch_decimals(args.symbol)
    state = State(args.depth, args.bucket, price_dec, qty_dec)
    rebuild_day(state, conn)
    log(f"sensor iniciado: {args.symbol} depth={args.depth} "
        f"precisión={price_dec}/{qty_dec} BD={args.db}")

    snap_task = asyncio.create_task(snapshot_loop(state, conn, args.interval))
    backoff = 2
    try:
        while True:
            session_start = time.time()
            try:
                await ws_session(state, conn, args.symbol)
                log("websocket cerrado por el servidor, reconectando")
            except BookDesync as exc:
                state.checksum_reconnects += 1
                log(f"desincronización del libro ({exc}), reconstruyendo")
                if (state.checksum_enabled and state.checksum_reconnects >= 3
                        and time.time() - state.started < 600):
                    # si falla nada más arrancar y en bucle, el algoritmo del
                    # checksum ya no coincide con Kraken: mejor sin él que en bucle
                    state.checksum_enabled = False
                    log("AVISO: checksum desactivado (falla sistemáticamente); "
                        "queda la comprobación de libro cruzado")
            except Exception as exc:
                log(f"ws caído ({type(exc).__name__}: {exc}), reconectando")
            state.book_ready = False
            state.bids, state.asks = {}, {}
            state.checksum_fails = 0
            backoff = 2 if time.time() - session_start > 60 else min(backoff * 2, 30)
            await asyncio.sleep(backoff)
    finally:
        snap_task.cancel()
        conn.commit()
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(Path(__file__).parent / "orderflow.db"))
    ap.add_argument("--symbol", default="BTC/EUR")
    ap.add_argument("--depth", type=int, default=25,
                    help="niveles del libro suscritos (10/25/100...)")
    ap.add_argument("--interval", type=float, default=1.0,
                    help="segundos entre snapshots de features")
    ap.add_argument("--bucket", type=float, default=10.0,
                    help="tamaño del bucket de precio del VPOC (EUR)")
    ap.add_argument("--duration", type=float, default=0,
                    help="segundos de recolección (0 = indefinido)")
    args = ap.parse_args()
    try:
        if args.duration:
            asyncio.run(asyncio.wait_for(run(args), timeout=args.duration))
        else:
            asyncio.run(run(args))
    except TimeoutError:
        log(f"duración alcanzada ({args.duration:.0f}s), sensor parado")
    except KeyboardInterrupt:
        log("sensor parado (Ctrl+C)")


if __name__ == "__main__":
    main()

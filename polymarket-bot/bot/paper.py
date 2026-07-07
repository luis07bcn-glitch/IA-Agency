"""Broker de paper trading con persistencia SQLite.

Contabilidad: al abrir, el stake sale del bankroll; al ganar, entran
shares * $1. Cada share comprada a precio p paga $1 si acierta.
"""
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value REAL
);
CREATE TABLE IF NOT EXISTS windows (
    window_start INTEGER PRIMARY KEY,
    btc_open REAL,
    btc_close REAL,
    outcome TEXT,            -- 'Up' | 'Down' | NULL
    settle_method TEXT       -- 'gamma' | 'proxy' | NULL
);
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    window_start INTEGER NOT NULL,
    side TEXT NOT NULL,      -- 'Up' | 'Down'
    token_id TEXT,
    price REAL NOT NULL,     -- precio de compra (ask)
    stake REAL NOT NULL,     -- USD arriesgados
    shares REAL NOT NULL,
    model_p REAL,            -- probabilidad del modelo para este lado
    edge REAL,               -- model_p - price en el momento de la compra
    btc_open REAL,
    btc_spot REAL,
    status TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'won' | 'lost'
    pnl REAL,
    resolved_ts REAL
);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    window_start INTEGER NOT NULL,
    side TEXT NOT NULL,      -- 'Up' | 'Down'
    model_p REAL,
    ask REAL,
    edge REAL,
    btc_open REAL,
    btc_spot REAL,
    action TEXT NOT NULL     -- 'trade' | 'below_min_edge' | 'above_max_edge'
                             --  | 'killswitch' | 'stake_too_small'
);
CREATE INDEX IF NOT EXISTS idx_signals_window ON signals (window_start);
CREATE TABLE IF NOT EXISTS window_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    window_start INTEGER NOT NULL,
    seconds_left REAL,
    btc_open REAL,
    spot REAL,
    -- features de precio reciente (velas 1m + histórico de spots propio)
    ret_30s REAL,
    ret_1m REAL,
    ret_3m REAL,
    ret_5m REAL,
    accel REAL,
    vol_hf REAL,
    crosses INTEGER,
    sigma_1m REAL,
    mu_1m REAL,
    -- microestructura del orderbook (lado Up como canónico)
    up_bid REAL,
    up_ask REAL,
    up_bid_size REAL,
    up_ask_size REAL,
    up_imb1 REAL,
    up_imb3 REAL,
    up_spread REAL,
    down_ask REAL,
    down_ask_size REAL,
    -- probabilidades del modelo en ese instante
    p_up_model REAL,     -- cruda, antes del prior de mercado
    p_up_final REAL      -- tras mezclar con el prior
);
CREATE INDEX IF NOT EXISTS idx_snapshots_window ON window_snapshots (window_start);
"""


class PaperBroker:
    def __init__(self, db_path: str, bankroll_start: float):
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(SCHEMA)
        cur = self.conn.execute("SELECT value FROM meta WHERE key='bankroll'")
        if cur.fetchone() is None:
            self.conn.execute(
                "INSERT INTO meta (key, value) VALUES ('bankroll', ?)",
                (bankroll_start,),
            )
        self.conn.commit()

    # --- bankroll ---
    def bankroll(self) -> float:
        return self.conn.execute(
            "SELECT value FROM meta WHERE key='bankroll'"
        ).fetchone()[0]

    def _adjust_bankroll(self, delta: float):
        self.conn.execute(
            "UPDATE meta SET value = value + ? WHERE key='bankroll'", (delta,)
        )

    # --- ventanas ---
    def window(self, start: int):
        row = self.conn.execute(
            "SELECT window_start, btc_open, btc_close, outcome FROM windows"
            " WHERE window_start=?", (start,),
        ).fetchone()
        if row is None:
            return None
        return {"start": row[0], "open": row[1], "close": row[2], "outcome": row[3]}

    def create_window(self, start: int, btc_open):
        self.conn.execute(
            "INSERT OR IGNORE INTO windows (window_start, btc_open) VALUES (?, ?)",
            (start, btc_open),
        )
        self.conn.commit()

    def set_close(self, start: int, btc_close: float):
        self.conn.execute(
            "UPDATE windows SET btc_close=? WHERE window_start=? AND btc_close IS NULL",
            (btc_close, start),
        )
        self.conn.commit()

    def windows_needing_close(self, now: float, window_seconds: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT window_start FROM windows WHERE btc_close IS NULL"
            " AND window_start + ? <= ?", (window_seconds, now),
        ).fetchall()
        return [r[0] for r in rows]

    def unresolved_windows(self, now: float, window_seconds: int) -> list[int]:
        """Ventanas terminadas sin outcome y con al menos una operación abierta."""
        rows = self.conn.execute(
            "SELECT DISTINCT w.window_start FROM windows w"
            " JOIN trades t ON t.window_start = w.window_start AND t.status='open'"
            " WHERE w.outcome IS NULL AND w.window_start + ? <= ?",
            (window_seconds, now),
        ).fetchall()
        return [r[0] for r in rows]

    # --- operaciones ---
    def trades_in_window(self, start: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM trades WHERE window_start=?", (start,)
        ).fetchone()[0]

    def open_trade(self, window_start: int, side: str, token_id: str, price: float,
                   stake: float, model_p: float, edge: float,
                   btc_open: float, btc_spot: float) -> int:
        shares = stake / price
        self.conn.execute(
            "INSERT INTO trades (ts, window_start, side, token_id, price, stake,"
            " shares, model_p, edge, btc_open, btc_spot)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (time.time(), window_start, side, token_id, price, stake, shares,
             model_p, edge, btc_open, btc_spot),
        )
        self._adjust_bankroll(-stake)
        self.conn.commit()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def log_signal(self, window_start: int, side: str, model_p: float, ask: float,
                   edge: float, btc_open: float, btc_spot: float, action: str):
        """Registra toda señal evaluada, se opere o no.

        Cada ventana acaba teniendo outcome, así que las señales rechazadas
        permiten análisis contrafactual (¿qué habría pasado con otra banda?).
        """
        self.conn.execute(
            "INSERT INTO signals (ts, window_start, side, model_p, ask, edge,"
            " btc_open, btc_spot, action) VALUES (?,?,?,?,?,?,?,?,?)",
            (time.time(), window_start, side, model_p, ask, edge,
             btc_open, btc_spot, action),
        )
        self.conn.commit()

    def log_snapshot(self, row: dict):
        """Guarda una foto de features de la ventana (dataset de entrenamiento).

        Cada ventana resuelta etiqueta después todas sus fotos vía JOIN con
        windows.outcome: son muestras de entrenamiento aunque no se opere.
        """
        cols = ("ts", "window_start", "seconds_left", "btc_open", "spot",
                "ret_30s", "ret_1m", "ret_3m", "ret_5m", "accel", "vol_hf",
                "crosses", "sigma_1m", "mu_1m", "up_bid", "up_ask",
                "up_bid_size", "up_ask_size", "up_imb1", "up_imb3",
                "up_spread", "down_ask", "down_ask_size", "p_up_model",
                "p_up_final")
        self.conn.execute(
            f"INSERT INTO window_snapshots ({','.join(cols)})"
            f" VALUES ({','.join('?' * len(cols))})",
            tuple(row.get(c) for c in cols),
        )
        self.conn.commit()

    def resolve_window(self, window_start: int, outcome: str, method: str):
        """Marca outcome de la ventana y liquida todas sus operaciones abiertas."""
        self.conn.execute(
            "UPDATE windows SET outcome=?, settle_method=? WHERE window_start=?",
            (outcome, method, window_start),
        )
        rows = self.conn.execute(
            "SELECT id, side, stake, shares FROM trades"
            " WHERE window_start=? AND status='open'", (window_start,),
        ).fetchall()
        now = time.time()
        for trade_id, side, stake, shares in rows:
            if side == outcome:
                payout = shares  # $1 por share
                pnl = payout - stake
                self._adjust_bankroll(payout)
                status = "won"
            else:
                pnl = -stake
                status = "lost"
            self.conn.execute(
                "UPDATE trades SET status=?, pnl=?, resolved_ts=? WHERE id=?",
                (status, pnl, now, trade_id),
            )
        self.conn.commit()

    def consecutive_losses(self, since_ts: float = 0.0) -> int:
        """Pérdidas seguidas desde la operación resuelta más reciente.

        since_ts limita el conteo a la sesión actual: así el kill-switch se
        reinicia al relanzar el bot en vez de bloquearlo para siempre.
        """
        rows = self.conn.execute(
            "SELECT status FROM trades WHERE status != 'open'"
            " AND resolved_ts >= ? ORDER BY resolved_ts DESC", (since_ts,),
        ).fetchall()
        n = 0
        for (status,) in rows:
            if status != "lost":
                break
            n += 1
        return n

    # --- métricas ---
    def summary(self) -> dict:
        total, wins, losses, pnl = self.conn.execute(
            "SELECT COUNT(*),"
            " SUM(CASE WHEN status='won' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN status='lost' THEN 1 ELSE 0 END),"
            " COALESCE(SUM(pnl), 0)"
            " FROM trades WHERE status != 'open'"
        ).fetchone()
        open_count = self.conn.execute(
            "SELECT COUNT(*) FROM trades WHERE status='open'"
        ).fetchone()[0]
        resolved = (wins or 0) + (losses or 0)
        return {
            "bankroll": self.bankroll(),
            "resolved": resolved,
            "open": open_count,
            "wins": wins or 0,
            "losses": losses or 0,
            "winrate": (wins or 0) / resolved if resolved else None,
            "pnl": pnl or 0.0,
        }

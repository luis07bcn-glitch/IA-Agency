"""Loop principal: captura de aperturas, señales, paper trades y resolución."""
import math
import time
from collections import deque
from datetime import datetime

from . import btc, clob, gamma, model
from .config import Config
from .paper import PaperBroker


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(msg: str):
    print(f"[{_ts()}] {msg}", flush=True)


class Runner:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.broker = PaperBroker(cfg.db_path, cfg.bankroll_start)
        self._market_cache: dict[int, dict | None] = {}
        self._state: dict | None = None
        self._state_ts: float = 0.0
        self._last_settle_poll: dict[int, float] = {}
        self._session_start = time.time()
        self._streak_since = self._session_start
        self._killswitch_until = 0.0
        self._spot_history: deque[tuple[float, float]] = deque(maxlen=120)

    # --- helpers ---
    def market_state(self) -> dict:
        now = time.time()
        if self._state is None or now - self._state_ts > self.cfg.vol_refresh_sec:
            self._state = btc.market_state(
                self.cfg.vol_lookback_min, self.cfg.drift_lookback_min
            )
            self._state_ts = now
        return self._state

    def ret_30s(self, now: float, spot: float):
        """Retorno log del spot frente a la observación propia de hace ~30 s."""
        ref = None
        for ts, s in self._spot_history:
            if ts <= now - 25:
                ref = s
            else:
                break
        return math.log(spot / ref) if ref else None

    def market_for(self, window_start: int) -> dict | None:
        if window_start not in self._market_cache:
            try:
                self._market_cache[window_start] = gamma.get_window_market(window_start)
            except Exception as e:
                log(f"gamma error ({window_start}): {e}")
                return None
        return self._market_cache[window_start]

    # --- fases del tick ---
    def capture_open(self, now: float, w: int):
        if self.broker.window(w) is not None:
            return
        if now - w <= self.cfg.open_capture_max_delay:
            try:
                price = btc.spot()
                self.broker.create_window(w, price)
                log(f"ventana {w}: open BTC = {price:,.2f}")
            except Exception as e:
                log(f"sin open para ventana {w}: {e}")
        else:
            # llegamos tarde: ventana registrada sin open -> no operable
            self.broker.create_window(w, None)
            log(f"ventana {w}: sin open (inicio perdido), no se opera")

    def capture_closes(self, now: float):
        for w in self.broker.windows_needing_close(now, self.cfg.window_seconds):
            try:
                price = btc.spot()
                self.broker.set_close(w, price)
                log(f"ventana {w}: close BTC = {price:,.2f}")
            except Exception as e:
                log(f"sin close para ventana {w}: {e}")

    def settle(self, now: float):
        for w in self.broker.unresolved_windows(now, self.cfg.window_seconds):
            last = self._last_settle_poll.get(w, 0)
            if now - last < self.cfg.settle_poll_sec:
                continue
            self._last_settle_poll[w] = now
            outcome = gamma.get_settlement(w)
            method = "gamma"
            if outcome is None and now > w + self.cfg.window_seconds + self.cfg.settle_timeout_sec:
                win = self.broker.window(w)
                if win and win["open"] is not None and win["close"] is not None:
                    outcome = "Up" if win["close"] >= win["open"] else "Down"
                    method = "proxy"
            if outcome:
                self.broker.resolve_window(w, outcome, method)
                s = self.broker.summary()
                wr = f" | winrate {s['winrate']:.1%}" if s["winrate"] is not None else ""
                log(f"ventana {w} resuelta: {outcome} ({method}) | "
                    f"bankroll {s['bankroll']:,.2f}{wr}")

    def evaluate(self, now: float, w: int) -> dict | None:
        """Captura la foto de features de la ventana y devuelve la mejor
        oportunidad operable, o None.

        La foto (window_snapshot) se guarda SIEMPRE que hay datos, aunque
        después no se opere: cada ventana resuelta es muestra de
        entrenamiento etiquetada (P0 del roadmap).
        """
        win = self.broker.window(w)
        if not win or win["open"] is None:
            return None
        seconds_left = w + self.cfg.window_seconds - now
        if seconds_left <= 5:
            return None
        mkt = self.market_for(w)
        if not mkt or not mkt["accepting"]:
            return None

        spot = btc.spot()
        self._spot_history.append((now, spot))
        state = self.market_state()
        p_up_raw = model.prob_up(spot, win["open"], state["sigma"],
                                 seconds_left / 60, mu_1m=state["mu"],
                                 drift_weight=self.cfg.drift_weight)

        books = {}
        for side in ("Up", "Down"):
            token = mkt["tokens"].get(side)
            if not token:
                continue
            try:
                books[side] = clob.top_of_book(token)
            except Exception:
                continue

        # prior de mercado: el mid del lado Up encoge desacuerdos extremos
        pw = self.cfg.market_prior_weight
        p_up = p_up_raw
        tob_up = books.get("Up")
        if pw > 0 and tob_up and tob_up["bid"] is not None and tob_up["ask"] is not None:
            mid_up = (tob_up["bid"] + tob_up["ask"]) / 2
            p_up = (1 - pw) * p_up_raw + pw * mid_up

        tob_down = books.get("Down") or {}
        try:
            self.broker.log_snapshot({
                "ts": now, "window_start": w, "seconds_left": seconds_left,
                "btc_open": win["open"], "spot": spot,
                "ret_30s": self.ret_30s(now, spot),
                "ret_1m": state["ret_1m"], "ret_3m": state["ret_3m"],
                "ret_5m": state["ret_5m"], "accel": state["accel"],
                "vol_hf": state["vol_hf"], "crosses": state["crosses"],
                "sigma_1m": state["sigma"], "mu_1m": state["mu"],
                "up_bid": tob_up.get("bid") if tob_up else None,
                "up_ask": tob_up.get("ask") if tob_up else None,
                "up_bid_size": tob_up.get("bid_size") if tob_up else None,
                "up_ask_size": tob_up.get("ask_size") if tob_up else None,
                "up_imb1": tob_up.get("imb1") if tob_up else None,
                "up_imb3": tob_up.get("imb3") if tob_up else None,
                "up_spread": tob_up.get("spread") if tob_up else None,
                "down_ask": tob_down.get("ask"),
                "down_ask_size": tob_down.get("ask_size"),
                "p_up_model": p_up_raw, "p_up_final": p_up,
            })
        except Exception as e:
            log(f"error guardando snapshot: {e}")

        # condiciones de operativa (la foto ya está guardada)
        if seconds_left <= self.cfg.no_trade_last_sec:
            return None
        if self.broker.trades_in_window(w) >= self.cfg.max_open_per_window:
            return None

        best = None
        for side, tob in books.items():
            if tob["ask"] is None or tob["ask_size"] < self.cfg.min_book_size:
                continue
            p_model = p_up if side == "Up" else 1.0 - p_up
            edge = p_model - tob["ask"] - self.cfg.fee
            if best is None or edge > best["edge"]:
                best = {"side": side, "token": mkt["tokens"][side], "ask": tob["ask"],
                        "p_model": p_model, "edge": edge, "spot": spot,
                        "open": win["open"]}
        return best

    def maybe_trade(self, w: int, sig: dict) -> str:
        """Decide si operar y devuelve la acción tomada (para la tabla signals)."""
        if sig["edge"] < self.cfg.min_edge:
            return "below_min_edge"
        if sig["edge"] > self.cfg.max_edge:
            log(f"edge {sig['edge']:+.3f} > {self.cfg.max_edge}: bandera roja "
                f"(el mercado sabe algo), no se opera")
            return "above_max_edge"
        now = time.time()
        if now < self._killswitch_until:
            return "killswitch"
        losses = self.broker.consecutive_losses(self._streak_since)
        if losses >= self.cfg.stop_after_losses:
            self._killswitch_until = now + self.cfg.killswitch_cooldown_sec
            self._streak_since = self._killswitch_until  # racha nueva tras el enfriamiento
            log(f"KILL-SWITCH: {losses} pérdidas seguidas, en pausa "
                f"{self.cfg.killswitch_cooldown_sec / 60:.0f} min")
            return "killswitch"
        price, q = sig["ask"], sig["p_model"]
        kelly = max((q - price) / (1.0 - price), 0.0) if price < 1.0 else 0.0
        fraction = min(self.cfg.max_stake_pct, self.cfg.kelly_fraction * kelly)
        stake = self.broker.bankroll() * fraction
        if stake < 1.0:
            return "stake_too_small"
        self.broker.open_trade(
            w, sig["side"], sig["token"], price, stake,
            sig["p_model"], sig["edge"], sig["open"], sig["spot"],
        )
        log(f"TRADE {sig['side']} @ {price:.3f} | stake ${stake:,.2f} | "
            f"p_modelo {q:.3f} | edge {sig['edge']:+.3f} | "
            f"spot {sig['spot']:,.2f} vs open {sig['open']:,.2f}")
        return "trade"

    # --- loop ---
    def tick(self):
        now = time.time()
        w = int(now // self.cfg.window_seconds * self.cfg.window_seconds)
        self.capture_open(now, w)
        self.capture_closes(now)
        self.settle(now)
        try:
            sig = self.evaluate(now, w)
        except Exception as e:
            log(f"error evaluando señal: {e}")
            return
        if sig:
            log(f"señal {sig['side']}: p_modelo {sig['p_model']:.3f} vs ask "
                f"{sig['ask']:.3f} (edge {sig['edge']:+.3f})")
            action = self.maybe_trade(w, sig)
            self.broker.log_signal(
                w, sig["side"], sig["p_model"], sig["ask"], sig["edge"],
                sig["open"], sig["spot"], action,
            )

    def run(self, duration_sec: float | None = None):
        s = self.broker.summary()
        log(f"Bot iniciado (PAPER). Bankroll: ${s['bankroll']:,.2f} | "
            f"min_edge {self.cfg.min_edge} | stake máx {self.cfg.max_stake_pct:.0%}")
        start = time.time()
        try:
            while True:
                t0 = time.time()
                try:
                    self.tick()
                except Exception as e:
                    log(f"error en tick: {e}")
                if duration_sec and time.time() - start >= duration_sec:
                    break
                elapsed = time.time() - t0
                time.sleep(max(self.cfg.tick_seconds - elapsed, 0.5))
        except KeyboardInterrupt:
            pass
        s = self.broker.summary()
        log(f"Bot detenido. Bankroll: ${s['bankroll']:,.2f} | resueltas: "
            f"{s['resolved']} | abiertas: {s['open']} | PnL: {s['pnl']:+,.2f}")

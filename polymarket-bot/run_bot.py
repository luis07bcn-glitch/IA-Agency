"""Bot Polymarket BTC Up/Down — paper trading.

Uso:
    python run_bot.py                 # loop indefinido (Ctrl+C para parar)
    python run_bot.py --minutes 60    # correr 60 minutos
    python run_bot.py --diagnose      # una pasada de diagnóstico, sin operar
    python run_bot.py --min-edge 0.07 --bankroll 500
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot import btc, clob, gamma, model  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.runner import Runner  # noqa: E402


def diagnose(cfg: Config):
    now = time.time()
    w = int(now // cfg.window_seconds * cfg.window_seconds)
    print(f"Ventana actual: {w} (quedan {w + cfg.window_seconds - now:.0f}s)")

    spot = btc.spot()
    mu, sigma = btc.drift_vol_1m(cfg.vol_lookback_min, cfg.drift_lookback_min)
    print(f"BTC spot (mediana 3 fuentes): {spot:,.2f}")
    print(f"Vol realizada 1m: {sigma:.6f} ({sigma * 100:.4f}% por minuto)")
    trend = "alcista" if mu > 0 else "bajista"
    print(f"Drift {cfg.drift_lookback_min}min: {mu * 100:+.4f}%/min ({trend}, "
          f"peso {cfg.drift_weight})")

    mkt = gamma.get_window_market(w)
    if not mkt:
        print("Mercado de la ventana actual no encontrado en Gamma.")
        return
    print(f"Mercado: {mkt['question']} | accepting={mkt['accepting']}")

    # sin open capturado usamos spot como proxy (solo diagnóstico)
    minutes_left = (w + cfg.window_seconds - now) / 60
    p_up = model.prob_up(spot, spot, sigma, minutes_left,
                         mu_1m=mu, drift_weight=cfg.drift_weight)
    print(f"p_up (con open=spot, solo referencia): {p_up:.3f}")

    for side, token in mkt["tokens"].items():
        tob = clob.top_of_book(token)
        p = p_up if side == "Up" else 1 - p_up
        edge = (p - tob["ask"]) if tob["ask"] is not None else None
        edge_s = f"{edge:+.3f}" if edge is not None else "n/a"
        print(f"  {side:5s} bid {tob['bid']} ({tob['bid_size']:.0f})  "
              f"ask {tob['ask']} ({tob['ask_size']:.0f})  "
              f"p_modelo {p:.3f}  edge {edge_s}")


def main():
    ap = argparse.ArgumentParser(description="Bot Polymarket BTC Up/Down (paper)")
    ap.add_argument("--minutes", type=float, default=None,
                    help="duración del loop en minutos (default: indefinido)")
    ap.add_argument("--diagnose", action="store_true",
                    help="una pasada de diagnóstico sin operar")
    ap.add_argument("--min-edge", type=float, default=None)
    ap.add_argument("--bankroll", type=float, default=None,
                    help="bankroll inicial (solo primera ejecución)")
    args = ap.parse_args()

    cfg = Config()
    if args.min_edge is not None:
        cfg.min_edge = args.min_edge
    if args.bankroll is not None:
        cfg.bankroll_start = args.bankroll

    if args.diagnose:
        diagnose(cfg)
        return

    Runner(cfg).run(duration_sec=args.minutes * 60 if args.minutes else None)


if __name__ == "__main__":
    main()

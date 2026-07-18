# -*- coding: utf-8 -*-
"""Análisis del poder predictivo de las features de order flow (Fase 0).

Sobre orderflow.db (generada por collector.py): reconstruye la serie de mid a
1s, calcula retornos forward a 10s/30s/1m/5m/15m y mide por feature el IC de
Spearman, su p-valor y el spread D10−D1 de retorno en bps. Compara contra los
costes reales de Kraken y emite el veredicto del gate escrito en README.md.

Uso:
    venv\\Scripts\\python.exe orderflow-sensor\\analyze.py
    venv\\Scripts\\python.exe orderflow-sensor\\analyze.py --maker-bps 16 --taker-bps 26
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):      # consola Windows cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HORIZONS = [10, 30, 60, 300, 900]           # segundos
MIN_N = 300                                  # mínimo de muestras por celda
IC_MIN, P_MAX = 0.03, 1e-3                   # umbral de señal del gate
SOFT_SPREAD_BPS = 10.0                       # gate blando: |D10-D1| mínimo


def load(db: str) -> pd.DataFrame:
    conn = sqlite3.connect(db)
    df = pd.read_sql_query("SELECT * FROM snapshots ORDER BY ts", conn)
    conn.close()
    if df.empty:
        sys.exit("snapshots vacía: ¿ha corrido collector.py?")
    df["sec"] = df["ts"].round().astype("int64")
    return df.drop_duplicates("sec", keep="last").set_index("sec")


def build_features(base: pd.DataFrame) -> dict[str, pd.Series]:
    feats = {k: base[k] for k in ("obi1", "obi5", "obi10")}
    # ofi/delta son "desde el snapshot anterior": sumas rodantes = flujo en ventana.
    # min_periods estricto para no fabricar señal dentro de huecos de recolección.
    for col in ("ofi", "delta"):
        feats[f"{col}_10s"] = base[col].rolling(10, min_periods=8).sum()
        feats[f"{col}_60s"] = base[col].rolling(60, min_periods=48).sum()
    feats["dist_vpoc_bps"] = (base["mid"] - base["vpoc"]) / base["mid"] * 1e4
    return feats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(Path(__file__).parent / "orderflow.db"))
    ap.add_argument("--maker-bps", type=float, default=25.0,
                    help="fee maker por lado en bps (tier base Kraken Pro)")
    ap.add_argument("--taker-bps", type=float, default=40.0,
                    help="fee taker por lado en bps (tier base Kraken Pro)")
    ap.add_argument("--min-days", type=float, default=7.0,
                    help="días de datos exigidos por el gate")
    args = ap.parse_args()

    df = load(args.db)
    span_days = (df["ts"].max() - df["ts"].min()) / 86400
    coverage_days = len(df) / 86400
    spread_med = float((df["spread"] / df["mid"] * 1e4).median())

    idx = np.arange(df.index.min(), df.index.max() + 1)
    base = df.reindex(idx)                    # huecos -> NaN, nunca rellenados
    mid = base["mid"]
    fwd = {h: (mid.shift(-h) / mid - 1) * 1e4 for h in HORIZONS}
    feats = build_features(base)

    taker_rt = 2 * args.taker_bps + spread_med
    maker_rt = 2 * args.maker_bps
    print(f"orderflow-sensor · análisis Fase 0")
    print(f"  datos: {len(df):,} snapshots | {span_days:.2f} días de rango | "
          f"{coverage_days:.2f} días de cobertura efectiva")
    print(f"  spread mediano: {spread_med:.2f} bps | coste ida+vuelta: "
          f"taker {taker_rt:.1f} bps, maker {maker_rt:.1f} bps\n")
    print(f"  {'feature':<15}{'horiz':>6}{'n':>9}{'IC':>8}{'p-valor':>10}{'D10-D1':>9}")
    print("  " + "-" * 57)

    hard, soft = [], []
    for name, feat in feats.items():
        for h in HORIZONS:
            sub = pd.DataFrame({"f": feat, "r": fwd[h]}).dropna()
            if len(sub) < MIN_N:
                continue
            ic, p = stats.spearmanr(sub["f"], sub["r"])
            try:
                decile = pd.qcut(sub["f"], 10, labels=False, duplicates="drop")
                by_d = sub.groupby(decile)["r"].mean()
                d_spread = float(by_d.iloc[-1] - by_d.iloc[0])
            except ValueError:                # feature degenerada (p.ej. todo ceros)
                d_spread = float("nan")
            mark = ""
            if abs(ic) >= IC_MIN and p < P_MAX and np.isfinite(d_spread):
                if abs(d_spread) > taker_rt:
                    hard.append((name, h, ic, d_spread)); mark = "  ← GATE DURO"
                elif abs(d_spread) >= SOFT_SPREAD_BPS:
                    soft.append((name, h, ic, d_spread)); mark = "  ← gate blando"
            print(f"  {name:<15}{h:>5}s{len(sub):>9,}{ic:>8.3f}{p:>10.1e}"
                  f"{d_spread:>8.1f}b{mark}")

    print("\n  VEREDICTO " + "=" * 47)
    if span_days < args.min_days:
        print(f"  DATOS INSUFICIENTES: {span_days:.2f} días de rango "
              f"(el gate exige ≥{args.min_days:.0f}). Seguir recolectando.")
    elif hard:
        best = max(hard, key=lambda x: abs(x[3]))
        print(f"  GATE DURO SUPERADO: {best[0]} @ {best[1]}s "
              f"(IC {best[2]:+.3f}, D10-D1 {best[3]:+.1f} bps > taker {taker_rt:.1f}).")
        print("  → diseñar paper trading direccional. (Revisar overfitting antes.)")
    elif soft:
        best = max(soft, key=lambda x: abs(x[3]))
        print(f"  GATE BLANDO superado: {best[0]} @ {best[1]}s "
              f"(IC {best[2]:+.3f}, D10-D1 {best[3]:+.1f} bps ≥ {SOFT_SPREAD_BPS:.0f}).")
        print("  → justifica Fase 1: simulación maker con cola sobre el tape.")
    else:
        print("  NINGÚN GATE SUPERADO: sin señal cobrable a ≤15min neta de costes.")
        print("  → descartar el bot de order flow y apagar el sensor (sin apego).")


if __name__ == "__main__":
    main()

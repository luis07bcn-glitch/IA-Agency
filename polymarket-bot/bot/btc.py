"""Precio spot de BTC y volatilidad realizada.

Usa la mediana de 3 fuentes públicas (Binance, Coinbase, Kraken) como proxy
del stream Chainlink BTC/USD que usa Polymarket para resolver. La discrepancia
típica es de pocos dólares; el umbral min_edge debe absorberla.
"""
import math
import statistics

import requests

TIMEOUT = 5


def _binance() -> float:
    r = requests.get(
        "https://api.binance.com/api/v3/ticker/price",
        params={"symbol": "BTCUSDT"}, timeout=TIMEOUT,
    )
    return float(r.json()["price"])


def _coinbase() -> float:
    r = requests.get(
        "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=TIMEOUT
    )
    return float(r.json()["data"]["amount"])


def _kraken() -> float:
    r = requests.get(
        "https://api.kraken.com/0/public/Ticker",
        params={"pair": "XBTUSD"}, timeout=TIMEOUT,
    )
    return float(r.json()["result"]["XXBTZUSD"]["c"][0])


def spot() -> float:
    """Mediana de las fuentes disponibles. Lanza si ninguna responde."""
    vals = []
    for fn in (_binance, _coinbase, _kraken):
        try:
            vals.append(fn())
        except Exception:
            continue
    if not vals:
        raise RuntimeError("Ninguna fuente de precio BTC disponible")
    return statistics.median(vals)


def _closes_1m(lookback_min: int) -> list[float]:
    """Cierres de velas de 1 minuto (Binance, fallback Kraken)."""
    try:
        ks = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1m", "limit": lookback_min},
            timeout=TIMEOUT,
        ).json()
        closes = [float(k[4]) for k in ks]
        if closes:
            return closes
    except Exception:
        pass
    r = requests.get(
        "https://api.kraken.com/0/public/OHLC",
        params={"pair": "XBTUSD", "interval": 1}, timeout=TIMEOUT,
    ).json()
    series = list(r["result"].values())[0]
    return [float(c[4]) for c in series[-lookback_min:]]


def market_state(vol_lookback_min: int = 120, drift_lookback_min: int = 30) -> dict:
    """Estado del mercado desde velas de 1 min, en una sola descarga.

    Además de mu/sigma (modelo), calcula features de precio reciente para el
    dataset de entrenamiento (window_snapshots): retornos a 1/3/5 min,
    aceleración, volatilidad de alta frecuencia y cruces de signo.
    """
    closes = _closes_1m(max(vol_lookback_min, drift_lookback_min))
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    if len(rets) < 10:
        raise RuntimeError("Histórico insuficiente para estimar volatilidad")
    sigma = statistics.pstdev(rets[-vol_lookback_min:])
    mu = statistics.fmean(rets[-drift_lookback_min:])

    def ret_n(n: int):
        if len(closes) <= n:
            return None
        return math.log(closes[-1] / closes[-1 - n])

    last10 = rets[-10:]
    crosses = sum(
        1 for i in range(1, len(last10))
        if (last10[i] > 0) != (last10[i - 1] > 0)
    )
    return {
        "mu": mu,
        "sigma": sigma,
        "ret_1m": ret_n(1),
        "ret_3m": ret_n(3),
        "ret_5m": ret_n(5),
        "accel": (rets[-1] - rets[-2]) if len(rets) >= 2 else None,
        "vol_hf": statistics.pstdev(last10),
        "crosses": crosses,
    }


def drift_vol_1m(vol_lookback_min: int = 120, drift_lookback_min: int = 30) -> tuple[float, float]:
    """(mu_1m, sigma_1m) — wrapper de market_state para compatibilidad."""
    st = market_state(vol_lookback_min, drift_lookback_min)
    return st["mu"], st["sigma"]


def realized_vol_1m(lookback_min: int = 120) -> float:
    """Desviación estándar de retornos log de 1 minuto."""
    return drift_vol_1m(lookback_min, drift_lookback_min=30)[1]

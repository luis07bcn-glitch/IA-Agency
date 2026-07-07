"""Cliente de la API Gamma de Polymarket: descubrimiento y liquidación de mercados.

Los mercados de 5 min de BTC usan slugs deterministas:
    btc-updown-5m-<epoch de inicio de ventana>   (epoch múltiplo de 300)
"""
import json

import requests

GAMMA = "https://gamma-api.polymarket.com"
TIMEOUT = 8


def window_slug(start_epoch: int) -> str:
    return f"btc-updown-5m-{start_epoch}"


def _fetch_market(start_epoch: int) -> dict | None:
    r = requests.get(
        f"{GAMMA}/events", params={"slug": window_slug(start_epoch)}, timeout=TIMEOUT
    )
    events = r.json()
    if not events or not events[0].get("markets"):
        return None
    return events[0]["markets"][0]


def get_window_market(start_epoch: int) -> dict | None:
    """Mercado operable de la ventana: tokens por outcome y estado."""
    m = _fetch_market(start_epoch)
    if m is None:
        return None
    outcomes = json.loads(m["outcomes"])
    tokens = json.loads(m["clobTokenIds"])
    return {
        "slug": window_slug(start_epoch),
        "question": m["question"],
        "tokens": dict(zip(outcomes, tokens)),  # {"Up": token_id, "Down": token_id}
        "accepting": bool(m.get("acceptingOrders")),
        "condition_id": m.get("conditionId"),
    }


def get_settlement(start_epoch: int) -> str | None:
    """Outcome oficial ("Up"/"Down") si el mercado ya cerró y liquidó; si no, None."""
    try:
        m = _fetch_market(start_epoch)
    except Exception:
        return None
    if m is None or not m.get("closed"):
        return None
    outcomes = json.loads(m["outcomes"])
    prices = json.loads(m.get("outcomePrices") or "[]")
    for outcome, price in zip(outcomes, prices):
        if float(price) >= 0.99:
            return outcome
    return None

"""Cliente del CLOB de Polymarket (solo lectura, endpoints públicos)."""
import requests

CLOB = "https://clob.polymarket.com"
TIMEOUT = 8


def top_of_book(token_id: str) -> dict:
    """Mejor bid/ask, tamaños y features de profundidad (imbalance, spread).

    imb1: presión compradora en el mejor nivel (0-1, >0.5 = domina el bid).
    imb3: lo mismo sumando los 3 mejores niveles de cada lado.
    """
    r = requests.get(f"{CLOB}/book", params={"token_id": token_id}, timeout=TIMEOUT)
    book = r.json()
    bids = sorted(book.get("bids") or [], key=lambda x: float(x["price"]),
                  reverse=True)
    asks = sorted(book.get("asks") or [], key=lambda x: float(x["price"]))
    best_bid = bids[0] if bids else None
    best_ask = asks[0] if asks else None

    def _imb(depth: int):
        b = sum(float(x["size"]) for x in bids[:depth])
        a = sum(float(x["size"]) for x in asks[:depth])
        return b / (b + a) if (b + a) > 0 else None

    bid = float(best_bid["price"]) if best_bid else None
    ask = float(best_ask["price"]) if best_ask else None
    return {
        "bid": bid,
        "bid_size": float(best_bid["size"]) if best_bid else 0.0,
        "ask": ask,
        "ask_size": float(best_ask["size"]) if best_ask else 0.0,
        "imb1": _imb(1),
        "imb3": _imb(3),
        "spread": (ask - bid) if (ask is not None and bid is not None) else None,
    }

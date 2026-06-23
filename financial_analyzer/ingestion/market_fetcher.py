"""
Ingesta de datos de mercado vía yfinance.
Cubre: índices, sectores, Bitcoin, commodities, breadth calculada.
"""
import pandas as pd
import yfinance as yf
from datetime import datetime


MARKET_TICKERS = {
    # Índices principales
    "SPX":       ("^GSPC",  "S&P 500"),
    "NASDAQ":    ("^IXIC",  "Nasdaq Composite"),
    "IBEX":      ("^IBEX",  "IBEX 35"),
    "EUROSTOXX": ("^STOXX50E", "Euro Stoxx 50"),
    "DAX":       ("^GDAXI", "DAX"),
    "RUSSELL2K": ("^RUT",   "Russell 2000 (small caps)"),

    # ETFs sectoriales S&P 500 (para momentum relativo)
    "XLK":  ("XLK",  "Tecnología"),
    "XLF":  ("XLF",  "Financiero"),
    "XLE":  ("XLE",  "Energía"),
    "XLV":  ("XLV",  "Healthcare (defensivo)"),
    "XLU":  ("XLU",  "Utilities (defensivo)"),
    "XLI":  ("XLI",  "Industriales"),
    "XLC":  ("XLC",  "Comunicaciones"),
    "XLRE": ("XLRE", "Real Estate"),
    "XLP":  ("XLP",  "Consumer Staples (defensivo)"),
    "XLY":  ("XLY",  "Consumer Discretionary"),
    "XLB":  ("XLB",  "Materiales"),

    # Commodities
    "GOLD":   ("GC=F", "Oro ($/oz)"),
    "OIL":    ("BZ=F", "Brent Crude ($/barril)"),
    "COPPER": ("HG=F", "Cobre ($/lb)"),

    # Bitcoin
    "BTC":  ("BTC-USD", "Bitcoin (USD)"),

    # Bonos (como proxy)
    "TLT":  ("TLT",    "ETF Bonos EEUU >20Y"),
    "HYG":  ("HYG",    "ETF High Yield"),
    "LQD":  ("LQD",    "ETF Investment Grade"),
}


def fetch_prices(start: str = "2010-01-01") -> dict[str, pd.DataFrame]:
    """Descarga precios OHLCV de todos los tickers."""
    results = {}
    for name, (ticker, description) in MARKET_TICKERS.items():
        try:
            raw = yf.download(ticker, start=start, progress=False, auto_adjust=True)
            if raw.empty:
                print(f"  SIN DATOS {name} ({ticker})")
                continue
            # Aplanar columnas multi-nivel si existen
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            df = raw[["Close"]].copy()
            df.columns = ["close"]
            df.index.name = "date"
            df = df.reset_index()
            df["ticker"] = ticker
            df["name"] = name
            df["description"] = description
            df["last_updated"] = datetime.now().isoformat()
            results[name] = df
            print(f"  OK {name}: {len(df)} días")
        except Exception as e:
            print(f"  ERROR {name} ({ticker}): {e}")

    return results


def compute_breadth_proxies(prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Calcula proxies de market breadth a partir de los índices disponibles.
    - % sectores por encima de su media 200d
    - Fuerza relativa sectores vs SPX
    """
    sector_keys = ["XLK", "XLF", "XLE", "XLV", "XLU", "XLI", "XLC", "XLRE", "XLP", "XLY", "XLB"]
    available = [k for k in sector_keys if k in prices]

    if not available:
        return pd.DataFrame()

    # Alinear fechas
    combined = pd.DataFrame()
    for key in available:
        s = prices[key].set_index("date")["close"].rename(key)
        combined = combined.join(s, how="outer") if not combined.empty else s.to_frame()

    combined = combined.sort_index().ffill()

    ma200 = combined.rolling(200).mean()
    above_200 = (combined > ma200).astype(int)
    pct_above_200 = above_200.mean(axis=1) * 100

    # Fuerza relativa: cada sector vs SPX
    rs_data = {}
    if "SPX" in prices:
        spx = prices["SPX"].set_index("date")["close"]
        for key in available:
            sector = prices[key].set_index("date")["close"]
            rs = (sector / spx).dropna()
            rs_data[f"RS_{key}"] = rs

    result = pd.DataFrame({"pct_sectors_above_200dma": pct_above_200})
    for col, series in rs_data.items():
        result = result.join(series.rename(col), how="left")

    return result.reset_index()


def compute_momentum(prices: dict[str, pd.DataFrame], tickers: list[str] = None) -> pd.DataFrame:
    """
    Calcula momentum (ROC) a 1M, 3M, 6M, 12M para los tickers indicados.
    También calcula distancia a media 50d y 200d.
    """
    if tickers is None:
        tickers = ["SPX", "NASDAQ", "IBEX", "EUROSTOXX", "XLK", "XLV", "XLU", "BTC"]

    rows = []
    for key in tickers:
        if key not in prices:
            continue
        df = prices[key].set_index("date")["close"].sort_index()
        if len(df) < 252:
            continue
        latest = df.iloc[-1]
        ma50  = df.rolling(50).mean().iloc[-1]
        ma200 = df.rolling(200).mean().iloc[-1]
        rows.append({
            "ticker": key,
            "close": latest,
            "roc_1m":  _roc(df, 21),
            "roc_3m":  _roc(df, 63),
            "roc_6m":  _roc(df, 126),
            "roc_12m": _roc(df, 252),
            "vs_ma50_pct":  round((latest / ma50 - 1) * 100, 2) if ma50 else None,
            "vs_ma200_pct": round((latest / ma200 - 1) * 100, 2) if ma200 else None,
            "above_200dma": latest > ma200 if ma200 else None,
        })

    return pd.DataFrame(rows)


def _roc(series: pd.Series, periods: int) -> float | None:
    if len(series) <= periods:
        return None
    past = series.iloc[-periods - 1]
    current = series.iloc[-1]
    return round((current / past - 1) * 100, 2) if past else None

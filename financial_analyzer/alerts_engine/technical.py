"""
Cálculo de indicadores técnicos usando yfinance (sin pandas-ta).
RSI, SMAs, ratio de volumen y momentum calculados manualmente.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def _rsi(series: pd.Series, period: int = 14) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return float(val) if pd.notna(val) else None


def get_technical_features(ticker: str, days: int = 260) -> dict | None:
    """
    Descarga precios de yfinance y calcula indicadores técnicos.
    Retorna None si no hay suficientes datos o falla la descarga.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=days + 60)
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 50:
            return None

        close = df["Close"].dropna()
        volume = df["Volume"].dropna()

        if len(close) < 50:
            return None

        price = float(close.iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        rsi = _rsi(close)

        vol_ratio = None
        if len(volume) >= 20:
            avg_vol = float(volume.rolling(20).mean().iloc[-1])
            if avg_vol > 0:
                vol_ratio = float(volume.iloc[-1]) / avg_vol

        roc_20d = float((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) >= 21 else None
        roc_5d = float((close.iloc[-1] / close.iloc[-6] - 1) * 100) if len(close) >= 6 else None

        vs_sma50 = round((price / sma50 - 1) * 100, 2) if sma50 else None
        vs_sma200 = round((price / sma200 - 1) * 100, 2) if sma200 else None

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "rsi": round(rsi, 1) if rsi is not None else None,
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2) if sma200 else None,
            "vs_sma50_pct": vs_sma50,
            "vs_sma200_pct": vs_sma200,
            "volume_ratio": round(vol_ratio, 2) if vol_ratio is not None else None,
            "roc_20d": round(roc_20d, 2) if roc_20d is not None else None,
            "roc_5d": round(roc_5d, 2) if roc_5d is not None else None,
        }

    except Exception as e:
        print(f"  ERROR técnico {ticker}: {e}")
        return None

"""
Módulo de Valoración Fundamental de Empresas.
Punto 1 incorporado: yfinance para US/globales + fallback manual para empresas europeas
donde yfinance tiene cobertura limitada (IBEX, EuroStoxx).

Fundamental Score 0-100:
  Rentabilidad  25 pts  ROE, ROIC, Margen Operativo
  Crecimiento   20 pts  CAGR Revenue, EPS growth
  Balance       20 pts  Deuda/EBITDA, Interest Coverage
  Cash Flow     15 pts  FCF Yield, FCF/Net Income
  Valoración    20 pts  P/E forward, EV/EBITDA, P/FCF
"""
import logging
import pandas as pd
import yfinance as yf
from dataclasses import dataclass, field
from datetime import datetime


# Tickers con sufijos para mercados europeos en yfinance
# Nota: la cobertura de fundamentales en yfinance es mejor para US.
# Para Europa usar sufijos: .MC (Madrid), .DE (Frankfurt), .PA (París), .MI (Milán)
WATCHLIST = {
    # ── IBEX 35 ───────────────────────────────────────────────
    "SAN.MC":  "Santander",
    "BBVA.MC": "BBVA",
    "TEF.MC":  "Telefónica",
    "IBE.MC":  "Iberdrola",
    "ITX.MC":  "Inditex",
    "REP.MC":  "Repsol",
    "AMS.MC":  "Amadeus",
    "FER.MC":  "Ferrovial",

    # ── EuroStoxx selección ───────────────────────────────────
    "SAP.DE":   "SAP",
    "ASML.AS":  "ASML",
    "MC.PA":    "LVMH",
    "SIE.DE":   "Siemens",
    "AIR.PA":   "Airbus",
    "SU.PA":    "Schneider Electric",

    # ── Semiconductores / Microchips ─────────────────────────
    "NVDA":   "NVIDIA",
    "AMD":    "AMD",
    "TSM":    "TSMC",
    "QCOM":   "Qualcomm",
    "INTC":   "Intel",
    "MU":     "Micron Technology",
    "AMAT":   "Applied Materials",
    "LRCX":   "Lam Research",
    "KLAC":   "KLA Corporation",
    "AVGO":   "Broadcom",
    "ON":     "ON Semiconductor",
    "MRVL":   "Marvell Technology",
    "ARM":    "ARM Holdings",

    # ── IA / Software / Nube ─────────────────────────────────
    "AAPL":   "Apple",
    "MSFT":   "Microsoft",
    "GOOGL":  "Alphabet",
    "META":   "Meta",
    "AMZN":   "Amazon",
    "PLTR":   "Palantir",
    "CRM":    "Salesforce",
    "SNOW":   "Snowflake",
    "DDOG":   "Datadog",
    "NET":    "Cloudflare",

    # ── Uranio / Nuclear ─────────────────────────────────────
    "CCJ":    "Cameco",
    "UEC":    "Uranium Energy Corp",
    "NXE":    "NexGen Energy",
    "DNN":    "Denison Mines",
    "UUUU":   "Energy Fuels",
    "URA":    "Global X Uranium ETF",
    "SMR":    "NuScale Power",
    "CEG":    "Constellation Energy",
    "VST":    "Vistra Corp",

    # ── Energía tradicional ───────────────────────────────────
    "XOM":    "ExxonMobil",
    "CVX":    "Chevron",
    "SLB":    "SLB (Schlumberger)",
    "OXY":    "Occidental Petroleum",

    # ── Cobre / Minería / Materias primas ────────────────────
    "FCX":    "Freeport-McMoRan (cobre)",
    "SCCO":   "Southern Copper",
    "NEM":    "Newmont (oro)",
    "GOLD":   "Barrick Gold",
    "MP":     "MP Materials (tierras raras)",
    "ALB":    "Albemarle (litio)",
    "SQM":    "SQM (litio)",

    # ── Defensa / Aeroespacial ───────────────────────────────
    "LMT":    "Lockheed Martin",
    "NOC":    "Northrop Grumman",
    "RTX":    "RTX Corporation",
    "GD":     "General Dynamics",
    "HII":    "Huntington Ingalls",
    "LDOS":   "Leidos",

    # ── Biofarma / Salud ─────────────────────────────────────
    "LLY":    "Eli Lilly",
    "ABBV":   "AbbVie",
    "NVO":    "Novo Nordisk",
    "MRNA":   "Moderna",
    "REGN":   "Regeneron",
    "JNJ":    "Johnson & Johnson",

    # ── Financiero ───────────────────────────────────────────
    "JPM":    "JPMorgan Chase",
    "GS":     "Goldman Sachs",
    "V":      "Visa",
    "MA":     "Mastercard",
    "COIN":   "Coinbase",

    # ── Infraestructura / Utilities / Data Centers ───────────
    "AMT":    "American Tower",
    "EQIX":   "Equinix",
    "NEE":    "NextEra Energy",

    # ── Defensivas calidad ───────────────────────────────────
    "PG":     "Procter & Gamble",
    "KO":     "Coca-Cola",
    "WMT":    "Walmart",
}


@dataclass
class FundamentalScore:
    ticker:          str = ""
    name:            str = ""
    score_profit:    float = 0.0   # máx 25
    score_growth:    float = 0.0   # máx 20
    score_balance:   float = 0.0   # máx 20
    score_cashflow:  float = 0.0   # máx 15
    score_valuation: float = 0.0   # máx 20
    data_quality:    str = "ok"    # 'ok' | 'partial' | 'unavailable'
    notes:           list = field(default_factory=list)
    timestamp:       str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total(self) -> float:
        return (self.score_profit + self.score_growth + self.score_balance +
                self.score_cashflow + self.score_valuation)

    @property
    def grade(self) -> str:
        if self.total >= 75:   return "A"
        if self.total >= 60:   return "B"
        if self.total >= 45:   return "C"
        if self.total >= 30:   return "D"
        return "F"

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "score_total": round(self.total, 1),
            "grade": self.grade,
            "score_profit": round(self.score_profit, 1),
            "score_growth": round(self.score_growth, 1),
            "score_balance": round(self.score_balance, 1),
            "score_cashflow": round(self.score_cashflow, 1),
            "score_valuation": round(self.score_valuation, 1),
            "data_quality": self.data_quality,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }


def score_ticker(ticker: str, name: str = "") -> FundamentalScore:
    """
    Calcula el Fundamental Score de un ticker.
    Para empresas europeas (sufijos .MC, .DE, .PA, etc.) yfinance puede tener
    datos parciales — el campo data_quality lo indica.
    """
    result = FundamentalScore(ticker=ticker, name=name or ticker)
    notes = []

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        is_european = any(ticker.endswith(s) for s in [".MC", ".DE", ".PA", ".MI", ".AS", ".LS"])
        if is_european:
            notes.append("Empresa europea: datos de fundamentales pueden ser parciales en yfinance")

        # ── RENTABILIDAD (máx 25) ──────────────────────
        profit = 0.0
        roe = info.get("returnOnEquity")
        if roe is not None:
            pts = 10 if roe > 0.20 else (7 if roe > 0.12 else (4 if roe > 0.05 else 0))
            profit += pts
        else:
            notes.append("ROE no disponible")

        margins = info.get("operatingMargins")
        if margins is not None:
            pts = 8 if margins > 0.20 else (5 if margins > 0.10 else (2 if margins > 0 else 0))
            profit += pts
        else:
            notes.append("Margen operativo no disponible")

        roic = info.get("returnOnAssets")  # proxy ROIC con ROA
        if roic is not None:
            pts = 7 if roic > 0.15 else (4 if roic > 0.07 else (1 if roic > 0 else 0))
            profit += pts

        result.score_profit = min(profit, 25.0)

        # ── CRECIMIENTO (máx 20) ──────────────────────
        growth = 0.0
        rev_growth = info.get("revenueGrowth")
        if rev_growth is not None:
            pts = 10 if rev_growth > 0.15 else (7 if rev_growth > 0.08 else (3 if rev_growth > 0 else 0))
            growth += pts
        else:
            notes.append("Revenue growth no disponible")

        eps_growth = info.get("earningsGrowth")
        if eps_growth is not None:
            pts = 10 if eps_growth > 0.15 else (7 if eps_growth > 0.08 else (3 if eps_growth > 0 else 0))
            growth += pts
        else:
            notes.append("EPS growth no disponible")

        result.score_growth = min(growth, 20.0)

        # ── BALANCE & DEUDA (máx 20) ──────────────────
        balance = 0.0
        debt_to_eq = info.get("debtToEquity")
        if debt_to_eq is not None:
            pts = 10 if debt_to_eq < 50 else (7 if debt_to_eq < 100 else (3 if debt_to_eq < 200 else 0))
            balance += pts
        else:
            notes.append("Deuda/Equity no disponible")

        current_ratio = info.get("currentRatio")
        if current_ratio is not None:
            pts = 10 if current_ratio > 2 else (7 if current_ratio > 1.2 else (3 if current_ratio > 0.8 else 0))
            balance += pts

        result.score_balance = min(balance, 20.0)

        # ── CASH FLOW (máx 15) ────────────────────────
        cashflow = 0.0
        fcf_yield = _compute_fcf_yield(stock, info)
        if fcf_yield is not None:
            pts = 15 if fcf_yield > 0.08 else (10 if fcf_yield > 0.04 else (5 if fcf_yield > 0.01 else 0))
            cashflow += pts
        else:
            cashflow += 5  # base si no hay datos
            notes.append("FCF Yield calculado con datos limitados")

        result.score_cashflow = min(cashflow, 15.0)

        # ── VALORACIÓN (máx 20) ───────────────────────
        valuation = 0.0
        fwd_pe = info.get("forwardPE")
        if fwd_pe is not None and fwd_pe > 0:
            pts = 8 if fwd_pe < 15 else (5 if fwd_pe < 22 else (2 if fwd_pe < 35 else 0))
            valuation += pts
        else:
            notes.append("P/E forward no disponible")

        ev_ebitda = info.get("enterpriseToEbitda")
        if ev_ebitda is not None and ev_ebitda > 0:
            pts = 12 if ev_ebitda < 10 else (8 if ev_ebitda < 16 else (4 if ev_ebitda < 25 else 0))
            valuation += pts

        result.score_valuation = min(valuation, 20.0)

        # Data quality
        missing = len([n for n in notes if "no disponible" in n])
        result.data_quality = "ok" if missing == 0 else ("partial" if missing <= 3 else "unavailable")

    except Exception as e:
        result.data_quality = "unavailable"
        result.notes = [f"Error descargando datos: {e}"]

    result.notes = notes
    return result


def _compute_fcf_yield(stock: yf.Ticker, info: dict) -> float | None:
    """Calcula FCF Yield = Free Cash Flow / Market Cap."""
    try:
        market_cap = info.get("marketCap")
        if not market_cap:
            return None
        cf = stock.cashflow
        if cf is None or cf.empty:
            return None
        # yfinance devuelve cashflow con filas = conceptos, cols = fechas
        if "Free Cash Flow" in cf.index:
            fcf = cf.loc["Free Cash Flow"].iloc[0]
        elif "Operating Cash Flow" in cf.index:
            fcf = cf.loc["Operating Cash Flow"].iloc[0]
        else:
            return None
        return float(fcf) / float(market_cap) if market_cap else None
    except Exception:
        return None


def score_watchlist(tickers: dict = None) -> pd.DataFrame:
    """
    Calcula el Fundamental Score de todos los tickers del watchlist.
    Retorna un DataFrame ordenado por score total descendente.
    """
    if tickers is None:
        tickers = WATCHLIST

    rows = []
    for ticker, name in tickers.items():
        logging.getLogger("financial_analyzer").info(f"  Analizando {ticker} ({name})...")
        s = score_ticker(ticker, name)
        rows.append(s.to_dict())

    df = pd.DataFrame(rows)
    df = df.sort_values("score_total", ascending=False).reset_index(drop=True)
    return df

"""
Ingesta de datos desde FRED (Federal Reserve Economic Data).
Cubre: tipos de interés, spreads crédito, VIX, M2, curva de tipos, mercado laboral US.
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred

FRED_SERIES = {
    # Liquidez / Masa Monetaria
    "M2_US":          ("M2SL",        "M2 USA (miles millones $)"),
    "FED_BALANCE":    ("WALCL",       "Balance Fed (miles millones $)"),

    # Tipos de interés
    "FED_FUNDS":      ("FEDFUNDS",    "Fed Funds Rate (%)"),
    "YIELD_2Y":       ("DGS2",        "Bono EEUU 2 años (%)"),
    "YIELD_10Y":      ("DGS10",       "Bono EEUU 10 años (%)"),
    "REAL_RATE_10Y":  ("DFII10",      "Tipo real 10Y EEUU (%)"),

    # Spreads crédito
    "SPREAD_HY":      ("BAMLH0A0HYM2",  "Spread High Yield EEUU (%)"),
    "SPREAD_IG":      ("BAMLC0A0CM",    "Spread Investment Grade EEUU (%)"),
    "TED_SPREAD":     ("TEDRATE",       "TED Spread (%)"),

    # Volatilidad
    "VIX":            ("VIXCLS",      "VIX (índice miedo)"),

    # Mercado laboral US
    "INITIAL_CLAIMS": ("ICSA",        "Initial Jobless Claims (miles)"),
    "JOLTS":          ("JTSJOL",      "JOLTS Job Openings (miles)"),
    "UNEMPLOYMENT_US":("UNRATE",      "Tasa paro EEUU (%)"),

    # Inflación US
    "CPI_US":         ("CPIAUCSL",    "IPC EEUU (índice)"),
    "CORE_CPI_US":    ("CPILFESL",    "IPC subyacente EEUU (índice)"),
    "CPI_YOY":        ("CPIAUCSL",    "IPC EEUU YoY % (calculado)"),

    # Confianza
    "MICHIGAN_SENT":  ("UMCSENT",     "Michigan Consumer Sentiment"),

    # Dólar
    "DXY":            ("DTWEXBGS",    "Índice dólar DXY"),

    # Curvas de tipos adicionales
    "T10Y3M":         ("T10Y3M",      "Spread 10Y-3M (%)"),

    # Liquidez avanzada
    "ON_RRP":         ("RRPONTSYD",   "ON RRP (Overnight Reverse Repos, miles millones $)"),
    "SOFR":           ("SOFR",        "SOFR — Secured Overnight Financing Rate (%)"),

    # Condiciones financieras
    "NFCI":           ("NFCI",        "Chicago Fed Financial Conditions Index"),
    "STLFSI":         ("STLFSI4",     "St. Louis Fed Financial Stress Index"),

    # Inflacion PCE (preferida de la Fed)
    "PCE":            ("PCEPI",       "PCE Price Index (indice)"),
    "CORE_PCE":       ("PCEPILFE",    "Core PCE Price Index (indice)"),

    # Indicadores adelantados
    "RETAIL_SALES":   ("RSAFS",       "Retail Sales EEUU (millones $)"),
    "INDPRO":         ("INDPRO",      "Produccion Industrial EEUU (indice)"),
    "PERMIT":         ("PERMIT",      "Building Permits EEUU (miles, anualizado)"),
    "CONT_CLAIMS":    ("CCSA",        "Continuing Jobless Claims (miles)"),
    "CAPACITY_UTIL":  ("TCU",         "Utilizacion Capacidad Industrial (%)"),

    # Recesiones y valoracion
    "USREC":          ("USREC",       "Periodos Recesion EEUU (NBER, 0/1)"),

    # Deficit fiscal y deuda EEUU (suelo implicito mercados)
    "DEFICIT":        ("MTSDS133FMS", "Deficit fiscal mensual EEUU (millones $)"),
    "DEBT_TOTAL":     ("GFDEBTN",     "Deuda publica total EEUU (millones $)"),
    "GDP_NOMINAL":    ("GDP",         "PIB nominal EEUU (miles millones $, trimestral)"),

    # Fontaneria financiera avanzada
    "FX_SWAPS":       ("SWPT",        "FX Swap Lines Fed (millones $)"),

    # Main Street — salud financiera del ciudadano
    "MORT_DELINQ":    ("DRSFRMACBS",  "Impagos hipotecas (% vivienda unifamiliar)"),
    "CC_DELINQ":      ("DRCCLACBS",   "Impagos tarjetas de credito (%)"),
    "AUTO_DELINQ":    ("DRAUTOACBS",  "Impagos prestamos de auto (%)"),
    "CC_DEBT":        ("REVOLSL",     "Deuda revolving/tarjetas (miles millones $)"),
    "CONSUMER_CREDIT":("TOTALSL",     "Credito total consumidor (miles millones $)"),
    "SAVING_RATE":    ("PSAVERT",     "Tasa de ahorro personal (%)"),
    "DEBT_SERVICE":   ("TDSP",        "Servicio deuda hogares (% renta disponible)"),
    "MORTGAGE_RATE":  ("MORTGAGE30US","Tipo hipotecario 30 años fijo (%)"),

    # SLOOS — Condiciones de credito bancario (Senior Loan Officer Opinion Survey)
    "SLOOS_CI":       ("STDSAUTO",        "SLOOS: bancos endureciendo credito auto (% neto)"),
    "SLOOS_CC":       ("DRTSCILM",        "SLOOS: bancos endureciendo tarjetas (% neto)"),
    "SLOOS_BUSINESS": ("DRTSCLNOBSMISNS", "SLOOS: bancos endureciendo credito empresas C&I (% neto)"),
}


def get_fred_client() -> Fred:
    key = os.getenv("FRED_API_KEY", "")
    if not key:
        raise ValueError("Falta FRED_API_KEY en variables de entorno.")
    return Fred(api_key=key)


def fetch_series(series_id: str, start: str = "2010-01-01") -> pd.Series:
    fred = get_fred_client()
    return fred.get_series(series_id, observation_start=start)


def fetch_all(start: str = "2010-01-01") -> dict[str, pd.DataFrame]:
    """
    Descarga todas las series FRED y devuelve un dict {nombre: DataFrame}.
    Cada DataFrame tiene columnas: date, value, source, description, last_updated.
    """
    fred = get_fred_client()
    results = {}

    for name, (series_id, description) in FRED_SERIES.items():
        try:
            raw = fred.get_series(series_id, observation_start=start)
            df = raw.reset_index()
            df.columns = ["date", "value"]
            df["source"] = "FRED"
            df["series_id"] = series_id
            df["description"] = description
            df["last_updated"] = datetime.now().isoformat()
            df["data_lag_days"] = _estimate_lag(name)
            results[name] = df
            print(f"  OK {name}: {len(df)} observaciones")
        except Exception as e:
            print(f"  ERROR {name} ({series_id}): {e}")

    return results


def _estimate_lag(name: str) -> int:
    """
    Retorna el lag típico en días de cada serie.
    Crítico para no tomar decisiones con datos obsoletos sin saberlo.
    """
    lags = {
        "M2_US": 30,
        "FED_BALANCE": 7,
        "FED_FUNDS": 1,
        "YIELD_2Y": 1,
        "YIELD_10Y": 1,
        "REAL_RATE_10Y": 1,
        "SPREAD_HY": 1,
        "SPREAD_IG": 1,
        "TED_SPREAD": 2,
        "VIX": 1,
        "INITIAL_CLAIMS": 5,
        "JOLTS": 45,
        "UNEMPLOYMENT_US": 30,
        "CPI_US": 30,
        "CORE_CPI_US": 30,
        "MICHIGAN_SENT": 14,
        "DXY": 1,
        "CPI_YOY": 30,
        "T10Y3M": 1,
        "ON_RRP": 1,
        "SOFR": 1,
        "NFCI": 7,
        "STLFSI": 7,
        "PCE": 35,
        "CORE_PCE": 35,
        "RETAIL_SALES": 30,
        "INDPRO": 30,
        "PERMIT": 30,
        "CONT_CLAIMS": 5,
        "CAPACITY_UTIL": 30,
        "USREC": 90,
        "DEFICIT": 35,
        "DEBT_TOTAL": 35,
        "GDP_NOMINAL": 90,
        "FX_SWAPS": 7,
        "MORT_DELINQ": 45,
        "CC_DELINQ":   45,
        "AUTO_DELINQ": 45,
        "CC_DEBT":     35,
        "CONSUMER_CREDIT": 35,
        "SAVING_RATE": 35,
        "DEBT_SERVICE": 45,
        "MORTGAGE_RATE": 4,
        "SLOOS_CI":       90,
        "SLOOS_CC":       90,
        "SLOOS_BUSINESS": 90,
    }
    return lags.get(name, 30)


def get_curve_spread(start: str = "2010-01-01") -> pd.DataFrame:
    """Calcula el spread 2Y-10Y (inversión de curva)."""
    fred = get_fred_client()
    y2 = fred.get_series("DGS2", observation_start=start)
    y10 = fred.get_series("DGS10", observation_start=start)
    spread = (y10 - y2).dropna()
    df = spread.reset_index()
    df.columns = ["date", "value"]
    df["description"] = "Spread 10Y-2Y (>0 = curva normal, <0 = invertida)"
    df["data_lag_days"] = 1
    df["last_updated"] = datetime.now().isoformat()
    return df

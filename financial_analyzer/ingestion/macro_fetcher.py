"""
Ingesta de datos macro de Europa y España.
Fuentes: Eurostat (librería eurostat), BdE API (REST JSON), ECB Data Warehouse.
Punto 3 incorporado: registro explícito de lag por serie para alertas de datos obsoletos.
"""
import requests
import pandas as pd
from datetime import datetime

try:
    import eurostat
    EUROSTAT_AVAILABLE = True
except ImportError:
    EUROSTAT_AVAILABLE = False
    print("AVISO: librería 'eurostat' no instalada. Ejecuta: pip install eurostat")


# ─────────────────────────────────────────────
#  EUROSTAT
# ─────────────────────────────────────────────

EUROSTAT_DATASETS = {
    # IPC Eurozona
    "HICP_EZ": {
        "code": "prc_hicp_midx",
        "filters": {"unit": "I15", "coicop": "CP00", "geo": "EA"},
        "description": "HICP Eurozona (índice, base 2015=100)",
        "lag_days": 35,
    },
    # PMI manufacturero Eurozona (vía Eurostat proxy)
    "UNEMPLOYMENT_EZ": {
        "code": "une_rt_m",
        "filters": {"sex": "T", "age": "TOTAL", "unit": "PC_ACT", "geo": "EA20", "s_adj": "SA"},
        "description": "Tasa de paro Eurozona (%)",
        "lag_days": 30,
    },
    # Tasa de paro España
    "UNEMPLOYMENT_ES": {
        "code": "une_rt_m",
        "filters": {"sex": "T", "age": "TOTAL", "unit": "PC_ACT", "geo": "ES", "s_adj": "SA"},
        "description": "Tasa de paro España (%)",
        "lag_days": 30,
    },
    # Confianza consumidor UE
    "CONSUMER_CONF_EU": {
        "code": "ei_bsco_m",
        "filters": {"indic": "BS-CSMCI-BAL", "s_adj": "SA", "geo": "EU27_2020"},
        "description": "Confianza consumidor UE (balance %)",
        "lag_days": 30,
    },
}


def fetch_eurostat_series(dataset_key: str) -> pd.DataFrame | None:
    if not EUROSTAT_AVAILABLE:
        return None

    cfg = EUROSTAT_DATASETS.get(dataset_key)
    if not cfg:
        return None

    try:
        df = eurostat.get_data_df(cfg["code"], flags=False)
        if df is None or df.empty:
            return None

        # Eurostat devuelve columnas de periodo en formato YYYY-MM
        id_cols = [c for c in df.columns if not str(c).startswith("19") and not str(c).startswith("20")]
        time_cols = [c for c in df.columns if c not in id_cols]

        # Filtrar por los parámetros definidos
        mask = pd.Series([True] * len(df), index=df.index)
        for key, val in cfg["filters"].items():
            if key in df.columns:
                mask = mask & (df[key] == val)

        df_filtered = df[mask][time_cols]
        if df_filtered.empty:
            return None

        series = df_filtered.iloc[0]
        result = pd.DataFrame({"date": pd.to_datetime(series.index, format="%Y-%m", errors="coerce"),
                               "value": pd.to_numeric(series.values, errors="coerce")})
        result = result.dropna()
        result["description"] = cfg["description"]
        result["source"] = "Eurostat"
        result["data_lag_days"] = cfg["lag_days"]
        result["last_updated"] = datetime.now().isoformat()
        return result

    except Exception as e:
        print(f"  ERROR Eurostat {dataset_key}: {e}")
        return None


# ─────────────────────────────────────────────
#  BANCO DE ESPAÑA — REST JSON API (BIEST)
# ─────────────────────────────────────────────

BDE_BASE_URL = "https://www.bde.es/webbde/es/estadis/infoest/si/si_1_1.csv"

BDE_SERIES = {
    "IPC_ES_GENERAL": {
        "url": "https://www.bde.es/webbde/es/estadis/infoest/si/si_1_1.csv",
        "description": "IPC España general (variación anual %)",
        "lag_days": 30,
    },
}


def fetch_ecb_series(series_key: str) -> pd.DataFrame | None:
    """
    Descarga series del ECB Statistical Data Warehouse via API REST.
    Documentación: https://data.ecb.europa.eu/help/api/data
    """
    ecb_series = {
        "M3_EZ": {
            "key": "BSI.M.U2.Y.V.M30.X.1.U2.2300.Z01.E",
            "description": "M3 Eurozona (tasa variación anual %)",
            "lag_days": 35,
        },
        "ECB_RATE": {
            "key": "FM.B.U2.EUR.4F.KR.DFR.LEV",
            "description": "Tipo depósito BCE (%)",
            "lag_days": 1,
        },
        "ECB_BALANCE": {
            "key": "ILM.W.U2.C.T000000.Z5.Z01",
            "description": "Balance BCE (miles millones EUR)",
            "lag_days": 7,
        },
    }

    cfg = ecb_series.get(series_key)
    if not cfg:
        return None

    url = f"https://data-api.ecb.europa.eu/service/data/{cfg['key']}?format=csvdata&startPeriod=2010-01"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))

        # El CSV del ECB tiene columnas: TIME_PERIOD, OBS_VALUE entre otras
        if "TIME_PERIOD" not in df.columns or "OBS_VALUE" not in df.columns:
            return None

        result = pd.DataFrame({
            "date": pd.to_datetime(df["TIME_PERIOD"], errors="coerce"),
            "value": pd.to_numeric(df["OBS_VALUE"], errors="coerce"),
        }).dropna()

        result["description"] = cfg["description"]
        result["source"] = "ECB"
        result["data_lag_days"] = cfg["lag_days"]
        result["last_updated"] = datetime.now().isoformat()
        return result

    except Exception as e:
        print(f"  ERROR ECB {series_key}: {e}")
        return None


def fetch_all_macro() -> dict[str, pd.DataFrame]:
    """Descarga todas las series macro europeas disponibles."""
    results = {}

    print("  Cargando datos ECB...")
    for key in ["M3_EZ", "ECB_RATE", "ECB_BALANCE"]:
        df = fetch_ecb_series(key)
        if df is not None and not df.empty:
            results[key] = df
            print(f"  OK {key}: {len(df)} observaciones")
        else:
            print(f"  SIN DATOS {key}")

    if EUROSTAT_AVAILABLE:
        print("  Cargando datos Eurostat...")
        for key in EUROSTAT_DATASETS:
            df = fetch_eurostat_series(key)
            if df is not None and not df.empty:
                results[key] = df
                print(f"  OK {key}: {len(df)} observaciones")
            else:
                print(f"  SIN DATOS {key}")

    return results

"""
Pipeline de actualización de datos. Ejecutar diariamente.
Descarga FRED + Mercados + Macro Europea -> almacena en DuckDB.
"""
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_analyzer.ingestion.fred_fetcher import fetch_all as fetch_fred, get_curve_spread
from financial_analyzer.ingestion.market_fetcher import fetch_prices, compute_breadth_proxies
from financial_analyzer.ingestion.macro_fetcher import fetch_all_macro
from financial_analyzer.ingestion.storage import (
    init_db, upsert_series, upsert_prices, get_stale_series
)
from financial_analyzer.alerts.notifier import notify, format_stale_data_alert

log = logging.getLogger("financial_analyzer.update")


def run_update(skip_fred: bool = False, skip_market: bool = False, skip_macro: bool = False):
    log.info("=" * 50)
    log.info("FINANCIAL ANALYZER - Actualizacion de datos")
    log.info("=" * 50)

    init_db()

    # FRED
    if not skip_fred:
        log.info("[1/4] Descargando datos FRED...")
        try:
            fred_data = fetch_fred()
            for name, df in fred_data.items():
                upsert_series(name, df)

            curve_df = get_curve_spread()
            curve_df["source"] = "FRED"
            curve_df["series_id"] = "SPREAD_2Y10Y"
            curve_df["data_lag_days"] = 1
            curve_df["last_updated"] = datetime.now().isoformat()
            upsert_series("CURVE_SPREAD_2Y10Y", curve_df)

            # CPI YoY calculado desde el índice
            if "CPI_US" in fred_data:
                cpi_df = fred_data["CPI_US"].copy()
                cpi_df = cpi_df.sort_values("date")
                cpi_df["value"] = cpi_df["value"].pct_change(12) * 100
                cpi_df = cpi_df.dropna()
                cpi_df["description"] = "IPC EEUU variacion anual (%)"
                cpi_df["source"] = "FRED"
                cpi_df["data_lag_days"] = 30
                cpi_df["last_updated"] = datetime.now().isoformat()
                upsert_series("CPI_YOY", cpi_df)

            if "CORE_CPI_US" in fred_data:
                core_df = fred_data["CORE_CPI_US"].copy()
                core_df = core_df.sort_values("date")
                core_df["value"] = core_df["value"].pct_change(12) * 100
                core_df = core_df.dropna()
                core_df["description"] = "IPC subyacente EEUU variacion anual (%)"
                core_df["source"] = "FRED"
                core_df["data_lag_days"] = 30
                core_df["last_updated"] = datetime.now().isoformat()
                upsert_series("CORE_CPI_YOY", core_df)

            if "PCE" in fred_data:
                pce_df = fred_data["PCE"].copy().sort_values("date")
                pce_df["value"] = pce_df["value"].pct_change(12) * 100
                pce_df = pce_df.dropna()
                pce_df["description"] = "PCE variacion anual (%)"
                pce_df["source"] = "FRED"
                pce_df["data_lag_days"] = 35
                pce_df["last_updated"] = datetime.now().isoformat()
                upsert_series("PCE_YOY", pce_df)

            if "CORE_PCE" in fred_data:
                cpce_df = fred_data["CORE_PCE"].copy().sort_values("date")
                cpce_df["value"] = cpce_df["value"].pct_change(12) * 100
                cpce_df = cpce_df.dropna()
                cpce_df["description"] = "Core PCE variacion anual (%)"
                cpce_df["source"] = "FRED"
                cpce_df["data_lag_days"] = 35
                cpce_df["last_updated"] = datetime.now().isoformat()
                upsert_series("CORE_PCE_YOY", cpce_df)

            # Deficit acumulado 12 meses (TTM) como % del PIB
            if "DEFICIT" in fred_data and "GDP_NOMINAL" in fred_data:
                deficit = fred_data["DEFICIT"].copy().sort_values("date").set_index("date")["value"]
                gdp = fred_data["GDP_NOMINAL"].copy().sort_values("date").set_index("date")["value"]
                # Deficit TTM (suma 12 meses)
                deficit_ttm = deficit.rolling(12).sum()
                # PIB anualizado interpolado a frecuencia mensual
                gdp_m = gdp.resample("MS").interpolate(method="time")
                # Alinear
                aligned = pd.DataFrame({"deficit": deficit_ttm, "gdp": gdp_m}).dropna()
                # Convertir GDP de miles millones a millones para misma escala
                aligned["deficit_pct_gdp"] = (aligned["deficit"] / (aligned["gdp"] * 1000)) * 100
                deficit_pct = aligned[["deficit_pct_gdp"]].reset_index()
                deficit_pct.columns = ["date", "value"]
                deficit_pct["source"] = "FRED"
                deficit_pct["description"] = "Deficit fiscal EEUU TTM como % PIB"
                deficit_pct["data_lag_days"] = 35
                deficit_pct["last_updated"] = datetime.now().isoformat()
                upsert_series("DEFICIT_PCT_GDP", deficit_pct)

            # Correlacion rodante BTC vs Balance Fed (90 dias)
            log.info(f"  FRED: {len(fred_data)+6} series actualizadas")
        except Exception as e:
            log.error(f"  ERROR FRED: {e}")

    # MERCADOS
    if not skip_market:
        log.info("[2/4] Descargando precios de mercado...")
        try:
            prices = fetch_prices()
            upsert_prices(prices)

            breadth = compute_breadth_proxies(prices)
            if not breadth.empty and "pct_sectors_above_200dma" in breadth.columns:
                breadth_df = breadth[["date", "pct_sectors_above_200dma"]].rename(
                    columns={"pct_sectors_above_200dma": "value"}
                )
                breadth_df["source"] = "calculated"
                breadth_df["description"] = "% sectores S&P sobre media 200d"
                breadth_df["data_lag_days"] = 1
                breadth_df["last_updated"] = datetime.now().isoformat()
                upsert_series("PCT_SECTORS_ABOVE_200DMA", breadth_df)

            log.info(f"  Mercados: {len(prices)} instrumentos actualizados")
        except Exception as e:
            log.error(f"  ERROR Mercados: {e}")

    # MACRO EUROPEA
    if not skip_macro:
        log.info("[3/4] Descargando datos macro europeos...")
        try:
            macro_data = fetch_all_macro()
            for name, df in macro_data.items():
                upsert_series(name, df)
            log.info(f"  Macro EU: {len(macro_data)} series actualizadas")
        except Exception as e:
            log.error(f"  ERROR Macro EU: {e}")

    # FRESCURA
    log.info("[4/4] Verificando frescura de datos...")
    stale = get_stale_series()
    if not stale.empty:
        stale_list = stale.to_dict("records")
        log.info(f"  AVISO: {len(stale_list)} series con datos obsoletos")
        for s in stale_list:
            log.info(f"    - {s['series_name']}: ultimo dato {s['last_data_date']}")
        try:
            alert_msg = format_stale_data_alert(stale_list)
            notify(alert_msg, channels=["console"])
        except Exception:
            pass
    else:
        log.info("  Todos los datos estan frescos.")

    log.info("Actualizacion completada.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_update()

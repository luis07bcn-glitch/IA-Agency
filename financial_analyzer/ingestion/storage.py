"""
Capa de almacenamiento: DuckDB como base de datos local + Parquet como backup.
Punto 3 implementado: tabla data_freshness que trackea lag y alerta de datos obsoletos.
"""
import os
import duckdb
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "financial_data.duckdb"
PARQUET_DIR = Path(__file__).parent.parent / "data" / "raw"


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))


def init_db():
    """Crea las tablas si no existen."""
    con = get_connection()

    con.execute("""
        CREATE TABLE IF NOT EXISTS time_series (
            series_name   VARCHAR,
            date          DATE,
            value         DOUBLE,
            source        VARCHAR,
            description   VARCHAR,
            data_lag_days INTEGER,
            last_updated  TIMESTAMP,
            PRIMARY KEY (series_name, date)
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS data_freshness (
            series_name      VARCHAR PRIMARY KEY,
            last_data_date   DATE,
            last_fetch_ts    TIMESTAMP,
            data_lag_days    INTEGER,
            expected_next    DATE,
            is_stale         BOOLEAN,
            description      VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS market_prices (
            ticker        VARCHAR,
            name          VARCHAR,
            date          DATE,
            close         DOUBLE,
            last_updated  TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS fundamental_scores (
            ticker        VARCHAR,
            date          DATE,
            score_total   DOUBLE,
            score_profit  DOUBLE,
            score_growth  DOUBLE,
            score_balance DOUBLE,
            score_cashflow DOUBLE,
            score_valuation DOUBLE,
            last_updated  TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)

    con.close()


def upsert_series(series_name: str, df: pd.DataFrame):
    """
    Inserta o actualiza una serie temporal.
    df debe tener columnas: date, value, source, description, data_lag_days, last_updated
    """
    if df is None or df.empty:
        return

    df = df.copy()
    df["series_name"] = series_name
    df["date"] = pd.to_datetime(df["date"]).dt.date

    con = get_connection()
    con.execute("DELETE FROM time_series WHERE series_name = ?", [series_name])
    con.execute("INSERT INTO time_series SELECT series_name, date, value, source, description, data_lag_days, last_updated FROM df")
    con.close()

    _update_freshness(series_name, df)


def upsert_prices(prices: dict[str, pd.DataFrame]):
    """Inserta o actualiza precios de mercado."""
    con = get_connection()
    for name, df in prices.items():
        if df is None or df.empty:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        con.execute("DELETE FROM market_prices WHERE name = ?", [name])
        con.execute("INSERT INTO market_prices SELECT ticker, name, date, close, last_updated FROM df")
    con.close()


def _update_freshness(series_name: str, df: pd.DataFrame):
    """Actualiza el registro de frescura de datos."""
    last_date = pd.to_datetime(df["date"]).max()
    lag_days = int(df["data_lag_days"].iloc[0]) if "data_lag_days" in df.columns else 30
    description = df["description"].iloc[0] if "description" in df.columns else ""

    expected_next = last_date + timedelta(days=lag_days + 15)
    is_stale = expected_next.date() < datetime.now().date()

    con = get_connection()
    con.execute("""
        INSERT OR REPLACE INTO data_freshness
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        series_name,
        last_date.date(),
        datetime.now(),
        lag_days,
        expected_next.date(),
        is_stale,
        description
    ])
    con.close()


def get_series(series_name: str, start: str = None) -> pd.DataFrame:
    """Lee una serie temporal de la DB."""
    con = get_connection()
    query = "SELECT date, value, description FROM time_series WHERE series_name = ?"
    params = [series_name]
    if start:
        query += " AND date >= ?"
        params.append(start)
    query += " ORDER BY date"
    df = con.execute(query, params).df()
    con.close()
    return df


def get_latest_value(series_name: str) -> tuple[float | None, str | None]:
    """Retorna (valor_más_reciente, fecha) de una serie."""
    con = get_connection()
    row = con.execute(
        "SELECT value, date FROM time_series WHERE series_name = ? ORDER BY date DESC LIMIT 1",
        [series_name]
    ).fetchone()
    con.close()
    if row:
        return row[0], str(row[1])
    return None, None


def get_prices(name: str, start: str = None) -> pd.DataFrame:
    """Lee precios de un instrumento."""
    con = get_connection()
    query = "SELECT date, close FROM market_prices WHERE name = ?"
    params = [name]
    if start:
        query += " AND date >= ?"
        params.append(start)
    query += " ORDER BY date"
    df = con.execute(query, params).df()
    con.close()
    return df


def get_stale_series() -> pd.DataFrame:
    """Retorna las series que tienen datos obsoletos según su lag esperado."""
    con = get_connection()
    df = con.execute("""
        SELECT series_name, last_data_date, data_lag_days, expected_next, description
        FROM data_freshness
        WHERE is_stale = TRUE
        ORDER BY last_data_date ASC
    """).df()
    con.close()
    return df


def get_freshness_status() -> pd.DataFrame:
    """Vista completa del estado de frescura de todas las series."""
    con = get_connection()
    df = con.execute("""
        SELECT series_name, description, last_data_date, data_lag_days,
               expected_next, is_stale, last_fetch_ts
        FROM data_freshness
        ORDER BY is_stale DESC, series_name
    """).df()
    con.close()
    return df

# -*- coding: utf-8 -*-
"""Persistencia SQLite del Radar Normativo (gestorias/data/radar.db)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "radar.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    identificador   TEXT PRIMARY KEY,
    fecha           TEXT NOT NULL,
    seccion         TEXT,
    departamento    TEXT,
    epigrafe        TEXT,
    titulo          TEXT NOT NULL,
    url_html        TEXT,
    url_pdf         TEXT,
    relevante       INTEGER,           -- NULL = pendiente de clasificar
    impacto         TEXT,              -- alto | medio | bajo
    areas           TEXT,              -- JSON: ["fiscal","laboral",...]
    resumen         TEXT,
    afecta          TEXT,
    accion          TEXT,
    clasificado_por TEXT,              -- llm | prefiltro | keywords
    creado_en       TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_items_fecha ON items(fecha);

CREATE TABLE IF NOT EXISTS boletines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_desde  TEXT,
    fecha_hasta  TEXT,
    contenido_md TEXT,
    creado_en    TEXT DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: Streamlit ejecuta cada rerun en un hilo distinto
    # y cachea la conexión con st.cache_resource; los accesos son secuenciales.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def upsert_items(conn: sqlite3.Connection, items: list[dict]) -> int:
    """Inserta items nuevos (ignora los ya existentes). Devuelve nº insertados."""
    antes = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.executemany(
        """INSERT OR IGNORE INTO items
           (identificador, fecha, seccion, departamento, epigrafe, titulo, url_html, url_pdf)
           VALUES (:identificador, :fecha, :seccion, :departamento, :epigrafe, :titulo, :url_html, :url_pdf)""",
        items,
    )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] - antes


def pendientes_de_clasificar(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM items WHERE relevante IS NULL ORDER BY fecha"
    ).fetchall()


def guardar_clasificacion(conn: sqlite3.Connection, identificador: str, *,
                          relevante: bool, impacto: str = "", areas: list[str] | None = None,
                          resumen: str = "", afecta: str = "", accion: str = "",
                          clasificado_por: str = "llm") -> None:
    conn.execute(
        """UPDATE items SET relevante=?, impacto=?, areas=?, resumen=?, afecta=?,
                            accion=?, clasificado_por=?
           WHERE identificador=?""",
        (int(relevante), impacto, json.dumps(areas or [], ensure_ascii=False),
         resumen, afecta, accion, clasificado_por, identificador),
    )


def items_relevantes(conn: sqlite3.Connection, desde: str, hasta: str) -> list[dict]:
    filas = conn.execute(
        """SELECT * FROM items WHERE relevante=1 AND fecha BETWEEN ? AND ?
           ORDER BY fecha DESC,
                    CASE impacto WHEN 'alto' THEN 0 WHEN 'medio' THEN 1 ELSE 2 END""",
        (desde, hasta),
    ).fetchall()
    out = []
    for f in filas:
        d = dict(f)
        d["areas"] = json.loads(d.get("areas") or "[]")
        out.append(d)
    return out


def guardar_boletin(conn: sqlite3.Connection, desde: str, hasta: str, contenido_md: str) -> None:
    conn.execute(
        "INSERT INTO boletines (fecha_desde, fecha_hasta, contenido_md) VALUES (?,?,?)",
        (desde, hasta, contenido_md),
    )
    conn.commit()


def ultimo_boletin(conn: sqlite3.Connection) -> dict | None:
    fila = conn.execute(
        "SELECT * FROM boletines ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return dict(fila) if fila else None

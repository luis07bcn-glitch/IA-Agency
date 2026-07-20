# -*- coding: utf-8 -*-
"""
Cartera de clientes del despacho.

Mapea remitentes (emails) y CIF/NIF a clientes de la gestoría, para que la
bandeja se clasifique POR NEGOCIO: "en la carpeta Meraki están sus facturas,
en la de Loli las suyas". Identificación en cascada:

1. email del remitente registrado en la cartera
2. CIF/NIF leído en la propia factura (como cliente o como emisor, para
   cubrir facturas recibidas Y emitidas del negocio)
3. si nada matchea → "Sin asignar (remitente)" y se sugiere darlo de alta
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "radar.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL,
    cif     TEXT DEFAULT '',
    emails  TEXT DEFAULT '[]',   -- JSON: ["admin@negocio.es", ...]
    carpeta TEXT NOT NULL        -- nombre de carpeta en disco
);
"""


@dataclass
class Cliente:
    id: int
    nombre: str
    cif: str
    emails: list[str]
    carpeta: str


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _norm_cif(cif: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (cif or "").upper())


def _norm_email(direccion: str) -> str:
    return parseaddr(direccion or "")[1].lower()


def sanear_carpeta(nombre: str) -> str:
    limpio = re.sub(r'[\\/:*?"<>|]', "", nombre).strip()
    return limpio or "sin_nombre"


def listar(conn: sqlite3.Connection) -> list[Cliente]:
    return [
        Cliente(r["id"], r["nombre"], r["cif"], json.loads(r["emails"] or "[]"), r["carpeta"])
        for r in conn.execute("SELECT * FROM clientes ORDER BY nombre")
    ]


def guardar(conn: sqlite3.Connection, nombre: str, cif: str = "",
            emails: list[str] | None = None, carpeta: str = "") -> None:
    conn.execute(
        "INSERT INTO clientes (nombre, cif, emails, carpeta) VALUES (?,?,?,?)",
        (nombre, cif, json.dumps([_norm_email(e) or e for e in (emails or [])]),
         sanear_carpeta(carpeta or nombre)),
    )
    conn.commit()


def reemplazar_cartera(conn: sqlite3.Connection, filas: list[dict]) -> None:
    """Sustituye la cartera completa (para el editor de la UI)."""
    conn.execute("DELETE FROM clientes")
    for f in filas:
        if not (f.get("nombre") or "").strip():
            continue
        emails = [e.strip().lower() for e in (f.get("emails") or "").split(";") if e.strip()]
        conn.execute(
            "INSERT INTO clientes (nombre, cif, emails, carpeta) VALUES (?,?,?,?)",
            (f["nombre"].strip(), (f.get("cif") or "").strip(),
             json.dumps(emails), sanear_carpeta(f.get("carpeta") or f["nombre"])),
        )
    conn.commit()


def identificar(clientes: list[Cliente], remitente: str = "",
                cifs_factura: list[str] | None = None) -> Cliente | None:
    """Devuelve el cliente al que pertenece un correo/factura, o None."""
    email = _norm_email(remitente)
    if email:
        for c in clientes:
            if email in c.emails:
                return c
    for cif in (cifs_factura or []):
        n = _norm_cif(cif)
        if n:
            for c in clientes:
                if n == _norm_cif(c.cif):
                    return c
    return None


def seed_demo(conn: sqlite3.Connection) -> None:
    """Da de alta la cartera de la demo (solo si la tabla está vacía)."""
    if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]:
        return
    demo = [
        ("MerakIA Studio, S.L.", "B-66123123", ["administracion@meraki.studio"], "Meraki"),
        ("Taller Pepe, S.L.", "B-64789456", ["taller.pepe@gmail.com"], "Taller Pepe"),
        ("Peluquería Loli", "38765412-K", ["loli.pelu@hotmail.com"], "Peluqueria Loli"),
        ("Centre Estètica Manolita, S.C.P.", "J-08991122", ["manolita.estetica@gmail.com"], "Centro Estetica Manolita"),
    ]
    for nombre, cif, emails, carpeta in demo:
        guardar(conn, nombre, cif, emails, carpeta)

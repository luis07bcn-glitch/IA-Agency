"""CRM local con SQLite. Sin dependencias externas."""
import sqlite3
import json
import csv
import io
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import ProspectorResult

DB_PATH = Path("outputs/prospector/crm.db")

ESTADOS = ["nuevo", "contactado", "reunion", "propuesta", "cliente", "descartado"]

ESTADO_COLORS = {
    "nuevo": "🔵",
    "contactado": "🟡",
    "reunion": "🟠",
    "propuesta": "🟣",
    "cliente": "🟢",
    "descartado": "🔴",
}


class CRM:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prospectos (
                    id                TEXT PRIMARY KEY,
                    nombre            TEXT NOT NULL,
                    tipo              TEXT,
                    ciudad            TEXT,
                    direccion         TEXT,
                    telefono          TEXT,
                    web               TEXT,
                    tiene_web         INTEGER DEFAULT 0,
                    rating            REAL,
                    total_resenas     INTEGER,
                    score_web         INTEGER,
                    score_oportunidad INTEGER DEFAULT 0,
                    oportunidad_nivel TEXT,
                    resumen           TEXT,
                    pains_json        TEXT,
                    resenas_json      TEXT,
                    email_asunto      TEXT,
                    email_cuerpo      TEXT,
                    whatsapp_mensaje  TEXT,
                    script_llamada    TEXT,
                    estado            TEXT DEFAULT 'nuevo',
                    notas             TEXT DEFAULT '',
                    fecha_creacion    TEXT,
                    fecha_contacto    TEXT
                )
            """)
        self._migrar()

    # Columnas añadidas después de la v1 (madurez digital, win probability, pérdidas, assets)
    _COLUMNAS_EXTRA = {
        "madurez_digital": "REAL",
        "percentil_nicho": "INTEGER",
        "win_probability": "INTEGER",
        "perdida_mes": "REAL",
        "scorecard_json": "TEXT",
        "win_json": "TEXT",
        "perdidas_json": "TEXT",
        "propuesta_texto": "TEXT",
        "demo_prompt": "TEXT",
        "landing_prompt": "TEXT",
        "presentacion_prompt": "TEXT",
        "tech_stack_json": "TEXT",
        "pagespeed_json": "TEXT",
        "competitive_json": "TEXT",
        "secuencia_json": "TEXT",
        "automation_json": "TEXT",
        "es_autonomo": "INTEGER",
        "nivel_automatizacion": "TEXT",
    }

    def _migrar(self):
        """Añade columnas nuevas a tablas creadas con versiones anteriores."""
        with self._conn() as conn:
            existentes = {row["name"] for row in conn.execute("PRAGMA table_info(prospectos)")}
            for col, tipo in self._COLUMNAS_EXTRA.items():
                if col not in existentes:
                    conn.execute(f"ALTER TABLE prospectos ADD COLUMN {col} {tipo}")

    # ── Escritura ──────────────────────────────────────────────────────────────

    def guardar(self, result: ProspectorResult) -> None:
        """Inserta o actualiza un resultado en el CRM."""
        b = result.business
        cl = result.web_checklist

        pains_data = [
            {
                "categoria": p.categoria,
                "descripcion": p.descripcion,
                "servicio": p.servicio,
                "urgencia": p.urgencia,
                "evidencia": p.evidencia,
            }
            for p in (result.pains or [])
        ]

        resenas_data = [
            {
                "autor": r.autor,
                "rating": r.rating,
                "texto": r.texto[:300],
                "categoria": r.categoria_dolor,
            }
            for r in (result.resenas or [])
        ]

        sc = result.scorecard or {}
        wp = result.win_probability or {}

        with self._conn() as conn:
            # Preservar estado y notas si ya existe
            existing = conn.execute(
                "SELECT estado, notas FROM prospectos WHERE id=?", (b.place_id,)
            ).fetchone()
            estado = existing["estado"] if existing else result.estado
            notas = existing["notas"] if existing else result.notas

            conn.execute("""
                INSERT OR REPLACE INTO prospectos
                (id, nombre, tipo, ciudad, direccion, telefono, web, tiene_web,
                 rating, total_resenas, score_web, score_oportunidad, oportunidad_nivel,
                 resumen, pains_json, resenas_json,
                 email_asunto, email_cuerpo, whatsapp_mensaje, script_llamada,
                 estado, notas, fecha_creacion, fecha_contacto,
                 madurez_digital, percentil_nicho, win_probability, perdida_mes,
                 scorecard_json, win_json, perdidas_json,
                 propuesta_texto, demo_prompt, landing_prompt, presentacion_prompt,
                 tech_stack_json, pagespeed_json, competitive_json, secuencia_json,
                 automation_json, es_autonomo, nivel_automatizacion)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                b.place_id, b.nombre, b.tipo, b.ciudad, b.direccion,
                b.telefono, b.web, int(b.tiene_web),
                b.rating, b.total_resenas,
                cl.score() if cl else None,
                result.score_oportunidad,
                cl.oportunidad() if cl else ("alta" if not b.tiene_web else "media"),
                result.resumen_oportunidad,
                json.dumps(pains_data, ensure_ascii=False),
                json.dumps(resenas_data, ensure_ascii=False),
                result.email_asunto,
                result.email_cuerpo,
                result.whatsapp_mensaje,
                result.script_llamada,
                estado, notas,
                datetime.now().isoformat(),
                result.fecha_contacto,
                sc.get("score_global"),
                sc.get("percentil_nicho"),
                wp.get("score"),
                result.perdida_total_mes,
                json.dumps(sc, ensure_ascii=False) if sc else None,
                json.dumps(wp, ensure_ascii=False) if wp else None,
                json.dumps(result.perdidas, ensure_ascii=False) if result.perdidas else None,
                result.propuesta_texto,
                result.demo_prompt,
                result.landing_prompt,
                result.presentacion_prompt,
                json.dumps(result.tech_stack, ensure_ascii=False) if result.tech_stack else None,
                json.dumps(result.pagespeed, ensure_ascii=False) if result.pagespeed else None,
                json.dumps(result.competitive, ensure_ascii=False) if result.competitive else None,
                json.dumps(result.secuencia_seguimiento, ensure_ascii=False) if result.secuencia_seguimiento else None,
                json.dumps(result.automation, ensure_ascii=False) if result.automation else None,
                int(bool(result.automation.get("es_autonomo"))) if result.automation else None,
                result.automation.get("nivel") if result.automation else None,
            ))

    # ── Lectura ────────────────────────────────────────────────────────────────

    def listar(
        self,
        ciudad: Optional[str] = None,
        estado: Optional[str] = None,
        oportunidad: Optional[str] = None,
        solo_con_web: Optional[bool] = None,
    ) -> List[dict]:
        query = "SELECT * FROM prospectos WHERE 1=1"
        params = []
        if ciudad:
            query += " AND LOWER(ciudad) LIKE ?"
            params.append(f"%{ciudad.lower()}%")
        if estado:
            query += " AND estado = ?"
            params.append(estado)
        if oportunidad:
            query += " AND oportunidad_nivel = ?"
            params.append(oportunidad)
        if solo_con_web is not None:
            query += " AND tiene_web = ?"
            params.append(1 if solo_con_web else 0)
        query += " ORDER BY score_oportunidad DESC, fecha_creacion DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def obtener(self, place_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM prospectos WHERE id=?", (place_id,)
            ).fetchone()
            return dict(row) if row else None

    def stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM prospectos").fetchone()[0]
            por_estado = conn.execute(
                "SELECT estado, COUNT(*) as n FROM prospectos GROUP BY estado"
            ).fetchall()
            alta_oportunidad = conn.execute(
                "SELECT COUNT(*) FROM prospectos WHERE oportunidad_nivel='alta'"
            ).fetchone()[0]
            return {
                "total": total,
                "por_estado": {r["estado"]: r["n"] for r in por_estado},
                "alta_oportunidad": alta_oportunidad,
            }

    # ── Actualización ──────────────────────────────────────────────────────────

    def actualizar_estado(
        self,
        place_id: str,
        estado: str,
        notas: str = "",
    ) -> None:
        fecha = datetime.now().isoformat() if estado != "nuevo" else None
        with self._conn() as conn:
            conn.execute(
                "UPDATE prospectos SET estado=?, notas=?, fecha_contacto=? WHERE id=?",
                (estado, notas, fecha, place_id),
            )

    # ── Exportar ───────────────────────────────────────────────────────────────

    def exportar_csv(self) -> str:
        rows = self.listar()
        if not rows:
            return ""

        exclude = {"pains_json", "resenas_json", "email_cuerpo", "script_llamada"}
        fieldnames = [k for k in rows[0].keys() if k not in exclude]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

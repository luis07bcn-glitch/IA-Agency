# -*- coding: utf-8 -*-
"""
Fuentes de correo: IMAP (buzón real del despacho) o carpeta local de .eml (demo).

Ambas devuelven la misma estructura `Correo`, así el clasificador y el
pipeline no saben de dónde vienen los mensajes.
"""
from __future__ import annotations

import datetime as dt
import email
import email.policy
import imaplib
from dataclasses import dataclass, field
from pathlib import Path

CARPETA_DEMO = Path(__file__).resolve().parent.parent / "demo_correo"

# Extensiones de adjunto que el extractor de facturas sabe procesar
EXT_PROCESABLES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"}


@dataclass
class Adjunto:
    filename: str
    content_type: str
    data: bytes

    @property
    def procesable(self) -> bool:
        return Path(self.filename).suffix.lower() in EXT_PROCESABLES


@dataclass
class Correo:
    uid: str
    de: str
    asunto: str
    fecha: str
    cuerpo: str                     # solo texto, recortado
    adjuntos: list[Adjunto] = field(default_factory=list)

    @property
    def nombres_adjuntos(self) -> list[str]:
        return [a.filename for a in self.adjuntos]


def _parsear_mensaje(uid: str, raw: bytes) -> Correo:
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    cuerpo = ""
    parte = msg.get_body(preferencelist=("plain", "html"))
    if parte is not None:
        try:
            cuerpo = parte.get_content()
        except Exception:
            cuerpo = ""
    cuerpo = " ".join(cuerpo.split())[:600]  # extracto compacto para el LLM

    adjuntos = []
    for adj in msg.iter_attachments():
        nombre = adj.get_filename() or "sin_nombre"
        try:
            data = adj.get_content()
            if isinstance(data, str):
                data = data.encode("utf-8", errors="ignore")
        except Exception:
            continue
        adjuntos.append(Adjunto(nombre, adj.get_content_type(), data))

    return Correo(
        uid=uid,
        de=str(msg.get("From", "")),
        asunto=str(msg.get("Subject", "")),
        fecha=str(msg.get("Date", "")),
        cuerpo=cuerpo,
        adjuntos=adjuntos,
    )


def leer_carpeta_eml(carpeta: Path | None = None) -> list[Correo]:
    """Lee todos los .eml de una carpeta local (modo demo / export de Outlook)."""
    carpeta = carpeta or CARPETA_DEMO
    correos = []
    for i, ruta in enumerate(sorted(carpeta.glob("*.eml"))):
        correos.append(_parsear_mensaje(f"eml-{i}-{ruta.stem}", ruta.read_bytes()))
    return correos


def leer_imap(host: str, usuario: str, password: str, *,
              carpeta: str = "INBOX", dias: int = 92,
              max_correos: int = 300) -> list[Correo]:
    """Lee los correos de los últimos `dias` días de un buzón IMAP (SSL).

    Para Gmail/Outlook usar contraseña de aplicación, no la de la cuenta.
    Solo lectura: no marca, no mueve, no borra nada.
    """
    desde = (dt.date.today() - dt.timedelta(days=dias)).strftime("%d-%b-%Y")
    correos: list[Correo] = []

    con = imaplib.IMAP4_SSL(host)
    try:
        con.login(usuario, password)
        con.select(carpeta, readonly=True)
        _, datos = con.search(None, f'(SINCE "{desde}")')
        uids = datos[0].split()
        for uid in uids[-max_correos:]:
            _, msg_data = con.fetch(uid, "(RFC822)")
            if msg_data and msg_data[0] is not None:
                correos.append(_parsear_mensaje(uid.decode(), msg_data[0][1]))
    finally:
        try:
            con.logout()
        except Exception:
            pass
    return correos

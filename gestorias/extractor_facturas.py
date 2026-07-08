# -*- coding: utf-8 -*-
"""
Extractor de facturas — el "core" del servicio a gestorias.

Lee una factura (PNG/JPG/PDF), usa el modelo de vision de Claude para extraer
los campos estructurados y los devuelve listos para volcar al software de
gestion (A3, Sage, Holded...) o para exportar a CSV/Excel.

ESTO es el producto. No se compra: son ~150 lineas sobre la API de Claude que
la agencia ya paga. La validacion humana es parte del diseno, no un parche.

Uso CLI:
    venv\\Scripts\\python.exe gestorias\\extractor_facturas.py ruta\\a\\factura.png
"""
import base64
import json
import sys
from pathlib import Path
from typing import List

import anthropic

# Permite ejecutar como script suelto (añade la raiz del repo al path)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings  # noqa: E402

MODEL = "claude-haiku-4-5-20251001"  # vision, rapido y barato; suficiente para facturas

# Campos que una gestoria necesita de una factura de proveedor para el IVA/IRPF
SCHEMA = {
    "emisor_nombre": "razon social de quien emite la factura",
    "emisor_cif": "CIF/NIF del emisor",
    "cliente_nombre": "razon social del receptor",
    "cliente_cif": "CIF/NIF del receptor",
    "numero_factura": "numero o serie de la factura",
    "fecha": "fecha de emision en formato AAAA-MM-DD",
    "fecha_vencimiento": "vencimiento en AAAA-MM-DD o null",
    "base_imponible": "base imponible como numero (punto decimal)",
    "tipo_iva": "porcentaje de IVA como numero (ej 21)",
    "cuota_iva": "importe del IVA como numero",
    "retencion_irpf": "importe de retencion IRPF como numero negativo o 0",
    "total": "total de la factura como numero",
    "moneda": "codigo de moneda (EUR)",
}

MEDIA = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif",
}


def _pdf_bytes_a_png(data: bytes) -> bytes:
    """Convierte la 1a pagina de un PDF (en bytes) a PNG con fitz (PyMuPDF)."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=data, filetype="pdf")
    pix = doc[0].get_pixmap(dpi=150)
    return pix.tobytes("png")


def _pdf_primera_pagina_a_png(pdf_path: Path) -> bytes:
    return _pdf_bytes_a_png(Path(pdf_path).read_bytes())


def cargar_imagen_desde_bytes(data: bytes, filename: str):
    """(media_type, base64) para el bloque image de la API, desde bytes en memoria."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        data = _pdf_bytes_a_png(data)
        return "image/png", base64.b64encode(data).decode()
    if ext in MEDIA:
        return MEDIA[ext], base64.b64encode(data).decode()
    raise ValueError(f"Formato no soportado: {ext}")


def _cargar_imagen(ruta: Path):
    """(media_type, base64) desde una ruta en disco."""
    return cargar_imagen_desde_bytes(Path(ruta).read_bytes(), str(ruta))


def png_preview_bytes(data: bytes, filename: str) -> bytes:
    """Devuelve PNG para previsualizar en la UI (convierte el PDF; imagen tal cual)."""
    if Path(filename).suffix.lower() == ".pdf":
        return _pdf_bytes_a_png(data)
    return data


def _prompt_extraccion() -> str:
    campos = "\n".join(f'  "{k}": {v}' for k, v in SCHEMA.items())
    return f"""Eres un asistente de una gestoria. Extrae los datos de esta factura
para volcarlos al programa de contabilidad.

Devuelve UNICAMENTE un JSON valido con exactamente estas claves:
{{
{campos}
}}

Reglas:
- Numeros con punto decimal, sin separador de miles y sin simbolo de moneda.
- Si un dato no aparece, pon null (no lo inventes).
- Anade una clave "_confianza" de 0 a 100: cuan seguro estas de la lectura.
- Anade una clave "_avisos": lista de textos con cualquier cosa que un humano
  deberia revisar (dato ambiguo, sello borroso, importes que no cuadran...).
Nada de texto fuera del JSON."""


def _extraer_desde_b64(media_type: str, b64: str, filename: str,
                       client: anthropic.Anthropic) -> dict:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": _prompt_extraccion()},
            ],
        }],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("```"))
    data = json.loads(raw)
    data["_archivo"] = filename
    return data


def extraer_factura(ruta, client: anthropic.Anthropic | None = None) -> dict:
    """Extrae los campos de UNA factura en disco. Devuelve dict segun SCHEMA."""
    ruta = Path(ruta)
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
    media_type, b64 = _cargar_imagen(ruta)
    return _extraer_desde_b64(media_type, b64, ruta.name, client)


def extraer_factura_bytes(data: bytes, filename: str,
                          client: anthropic.Anthropic | None = None) -> dict:
    """Extrae los campos de UNA factura recibida en memoria (ej. subida en la app)."""
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
    media_type, b64 = cargar_imagen_desde_bytes(data, filename)
    return _extraer_desde_b64(media_type, b64, filename, client)


def extraer_lote(rutas: List) -> List[dict]:
    """Procesa varias facturas con un solo cliente."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    out = []
    for r in rutas:
        try:
            out.append(extraer_factura(r, client))
        except Exception as e:
            out.append({"_archivo": Path(r).name, "_error": str(e)})
    return out


def a_csv(filas: List[dict], destino) -> Path:
    """Exporta las filas extraidas al CSV que la gestoria importa/revisa."""
    import csv
    destino = Path(destino)
    campos = list(SCHEMA.keys())
    extra = ["_confianza", "_avisos", "_archivo"]
    with destino.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(campos + extra)
        for d in filas:
            avisos = d.get("_avisos") or []
            if isinstance(avisos, list):
                avisos = " | ".join(str(a) for a in avisos)
            w.writerow([d.get(k, "") for k in campos]
                       + [d.get("_confianza", ""), avisos, d.get("_archivo", "")])
    return destino


def _pretty(d: dict) -> str:
    orden = list(SCHEMA.keys())
    lines = []
    for k in orden:
        lines.append(f"  {k:20s}: {d.get(k)}")
    lines.append(f"  {'_confianza':20s}: {d.get('_confianza')}")
    if d.get("_avisos"):
        lines.append(f"  {'_avisos':20s}: {d.get('_avisos')}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Por defecto, la factura de muestra de la demo
        ruta = Path(__file__).parent / "demo_facturas" / "factura_muestra.png"
    else:
        ruta = Path(sys.argv[1])
    print(f"Leyendo: {ruta.name}\n")
    resultado = extraer_factura(ruta)
    print(_pretty(resultado))

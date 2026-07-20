# -*- coding: utf-8 -*-
"""
Pipeline de bandeja: correos → clasificación → facturas adjuntas → extractor → CSV.

Este es el flujo "trimestre": el cliente vuelca sus facturas por email y el
despacho recibe una tabla estructurada lista para su software, con los campos
dudosos flaggeados para revisión humana.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from gestorias import clientes as cartera  # noqa: E402
from gestorias.extractor_facturas import extraer_factura_bytes  # noqa: E402

from .clasificador import Clasificacion, clasificar  # noqa: E402
from .fuentes import Correo  # noqa: E402

SIN_ASIGNAR = "⚠ Sin asignar"
SALIDA_DIR = Path(__file__).resolve().parent.parent / "salida"

# Campos internos que no deben ir al CSV del despacho
_CAMPOS_INTERNOS = ("_adjunto_bytes",)


@dataclass
class ResultadoBandeja:
    correos: list[Correo]
    clasificaciones: list[Clasificacion]
    facturas: list[dict] = field(default_factory=list)   # filas del extractor
    errores_extraccion: list[str] = field(default_factory=list)

    @property
    def por_categoria(self) -> dict[str, int]:
        cuenta: dict[str, int] = {}
        for c in self.clasificaciones:
            cuenta[c.categoria] = cuenta.get(c.categoria, 0) + 1
        return cuenta

    @property
    def urgentes(self) -> int:
        return sum(1 for c in self.clasificaciones if c.prioridad == "alta")

    @property
    def facturas_por_cliente(self) -> dict[str, list[dict]]:
        """Facturas agrupadas por negocio, 'Sin asignar' al final."""
        grupos: dict[str, list[dict]] = {}
        for f in self.facturas:
            grupos.setdefault(f.get("_cliente", SIN_ASIGNAR), []).append(f)
        return dict(sorted(grupos.items(), key=lambda kv: (kv[0].startswith("⚠"), kv[0])))


def _asignar_cliente(fila: dict, correo: Correo,
                     lista_clientes: list[cartera.Cliente]) -> None:
    """Cascada: email del remitente → CIF leído en la factura (cliente o emisor)."""
    cifs = [fila.get("cliente_cif") or "", fila.get("emisor_cif") or ""]
    cli = cartera.identificar(lista_clientes, remitente=correo.de, cifs_factura=cifs)
    if cli:
        fila["_cliente"] = cli.nombre
        fila["_carpeta"] = cli.carpeta
    else:
        fila["_cliente"] = f"{SIN_ASIGNAR} ({correo.de})"
        fila["_carpeta"] = ""


def procesar_bandeja(correos: list[Correo], *, extraer_facturas: bool = True,
                     log=print) -> ResultadoBandeja:
    """Clasifica la bandeja y extrae las facturas adjuntas de los correos 'factura'."""
    clasificaciones = clasificar(correos, log=log)
    resultado = ResultadoBandeja(correos=correos, clasificaciones=clasificaciones)
    if not extraer_facturas:
        return resultado

    conn = cartera.get_conn()
    lista_clientes = cartera.listar(conn)
    conn.close()

    por_uid = {c.uid: c for c in correos}
    for clasif in clasificaciones:
        if clasif.categoria != "factura":
            continue
        correo = por_uid[clasif.uid]
        for adj in correo.adjuntos:
            if not adj.procesable:
                continue
            try:
                fila = extraer_factura_bytes(adj.data, adj.filename)
                fila["_correo_de"] = correo.de
                fila["_correo_asunto"] = correo.asunto
                fila["_archivo"] = adj.filename
                fila["_adjunto_bytes"] = adj.data
                _asignar_cliente(fila, correo, lista_clientes)
                resultado.facturas.append(fila)
                log(f"  factura extraida: {adj.filename} -> {fila['_cliente']}")
            except Exception as e:
                resultado.errores_extraccion.append(f"{adj.filename}: {e}")
                log(f"  [aviso] fallo extrayendo {adj.filename}: {e}")
    return resultado


def _fila_csv(fila: dict) -> dict:
    return {k: v for k, v in fila.items() if k not in _CAMPOS_INTERNOS}


def guardar_en_carpetas(resultado: ResultadoBandeja, periodo: str,
                        base_dir: Path | None = None) -> dict[str, dict]:
    """Escribe salida/<periodo>/<carpeta cliente>/ con los archivos originales
    y un CSV por cliente, más un resumen global. Devuelve {cliente: {n, ruta}}.
    """
    import csv

    base = (base_dir or SALIDA_DIR) / periodo
    base.mkdir(parents=True, exist_ok=True)
    resumen: dict[str, dict] = {}
    todas: list[dict] = []

    for nombre_cliente, filas in resultado.facturas_por_cliente.items():
        carpeta_nombre = filas[0].get("_carpeta") or cartera.sanear_carpeta(
            nombre_cliente.replace(SIN_ASIGNAR, "_SIN ASIGNAR"))
        carpeta = base / carpeta_nombre
        carpeta.mkdir(parents=True, exist_ok=True)

        for f in filas:
            destino = carpeta / Path(f["_archivo"]).name
            n = 1
            while destino.exists():
                destino = carpeta / f"{destino.stem.rstrip('_0123456789')}_{n}{destino.suffix}"
                n += 1
            if f.get("_adjunto_bytes"):
                destino.write_bytes(f["_adjunto_bytes"])
            f["_guardado_en"] = str(destino)

        filas_csv = [_fila_csv(f) for f in filas]
        campos = sorted({k for f in filas_csv for k in f}, key=lambda k: (k.startswith("_"), k))
        ruta_csv = carpeta / f"facturas_{periodo}.csv"
        with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerows(filas_csv)

        todas.extend(filas_csv)
        resumen[nombre_cliente] = {"n": len(filas), "ruta": str(carpeta)}

    if todas:
        campos = sorted({k for f in todas for k in f}, key=lambda k: (k.startswith("_"), k))
        with open(base / f"resumen_{periodo}.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerows(todas)
    return resumen


def periodo_por_defecto() -> str:
    """En época de presentación se declara el trimestre ANTERIOR."""
    import datetime as dt
    hoy = dt.date.today()
    tri_actual = (hoy.month - 1) // 3 + 1
    if tri_actual == 1:
        return f"{hoy.year - 1}-4T"
    return f"{hoy.year}-{tri_actual - 1}T"

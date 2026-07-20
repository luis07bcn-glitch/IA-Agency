# -*- coding: utf-8 -*-
"""
Cliente del API de datos abiertos del BOE.

Descarga el sumario diario (https://www.boe.es/datosabiertos/api/boe/sumario/AAAAMMDD)
y lo aplana a una lista de items homogéneos. El JSON del BOE viene de una
conversión XML→JSON: cualquier nodo puede ser dict u lista según haya 1 o N
elementos, de ahí el helper _as_list.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import requests

API_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"

# Secciones con contenido normativo útil para una gestoría.
# 1 = Disposiciones generales (leyes, RD, órdenes ministeriales)
# 3 = Otras disposiciones (convenios colectivos, subvenciones, resoluciones)
SECCIONES_UTILES = ("1", "3")


@dataclass
class ItemBOE:
    identificador: str
    fecha: str  # YYYY-MM-DD
    seccion: str
    departamento: str
    epigrafe: str
    titulo: str
    url_html: str = ""
    url_pdf: str = ""

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _as_list(nodo) -> list:
    if nodo is None:
        return []
    if isinstance(nodo, list):
        return nodo
    return [nodo]


def sumario_del_dia(fecha: dt.date, timeout: int = 30) -> list[ItemBOE]:
    """Devuelve los items de las secciones útiles del BOE de esa fecha.

    Lanza excepción de red si el API falla; devuelve [] si ese día no hubo
    BOE (domingos y algunos festivos → HTTP 404).
    """
    url = API_URL.format(fecha=fecha.strftime("%Y%m%d"))
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()

    sumario = resp.json()["data"]["sumario"]
    fecha_iso = fecha.isoformat()
    items: list[ItemBOE] = []

    for diario in _as_list(sumario.get("diario")):
        for seccion in _as_list(diario.get("seccion")):
            cod_seccion = str(seccion.get("codigo", ""))
            if cod_seccion not in SECCIONES_UTILES:
                continue
            for depto in _as_list(seccion.get("departamento")):
                nombre_depto = depto.get("nombre", "")
                # Los items pueden colgar del departamento o de un epígrafe
                bloques = [("", _as_list(depto.get("item")))]
                for epi in _as_list(depto.get("epigrafe")):
                    bloques.append((epi.get("nombre", ""), _as_list(epi.get("item"))))
                for nombre_epi, lista_items in bloques:
                    for it in lista_items:
                        url_pdf = it.get("url_pdf") or {}
                        items.append(ItemBOE(
                            identificador=it.get("identificador", ""),
                            fecha=fecha_iso,
                            seccion=cod_seccion,
                            departamento=nombre_depto,
                            epigrafe=nombre_epi,
                            titulo=it.get("titulo", ""),
                            url_html=it.get("url_html", ""),
                            url_pdf=url_pdf.get("texto", "") if isinstance(url_pdf, dict) else "",
                        ))
    return items


def sumarios_rango(desde: dt.date, hasta: dt.date) -> list[ItemBOE]:
    """Items de todos los BOE publicados en [desde, hasta], ambos incluidos."""
    items: list[ItemBOE] = []
    dia = desde
    while dia <= hasta:
        items.extend(sumario_del_dia(dia))
        dia += dt.timedelta(days=1)
    return items

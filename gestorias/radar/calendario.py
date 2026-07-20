# -*- coding: utf-8 -*-
"""
Calendario fiscal español — vencimientos de los modelos habituales de una
gestoría. Determinista, sin IA: las reglas generales del calendario del
contribuyente son estables año a año.

Nota: si un vencimiento cae en sábado/domingo se traslada al siguiente hábil
(aquí se ajusta fin de semana; festivos no, se marca como orientativo). Las
domiciliaciones bancarias suelen cerrar ~5 días naturales antes.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass
class Vencimiento:
    fecha: dt.date          # último día de plazo (ajustado a día hábil)
    modelo: str
    descripcion: str
    periodo: str
    colectivo: str          # a quién aplica


def _habil(fecha: dt.date) -> dt.date:
    """Si cae en fin de semana, pasa al lunes siguiente."""
    while fecha.weekday() >= 5:
        fecha += dt.timedelta(days=1)
    return fecha


def _vencimientos_del_anyo(anyo: int) -> list[Vencimiento]:
    V = []

    def add(mes: int, dia: int, modelo: str, desc: str, periodo: str, colectivo: str):
        V.append(Vencimiento(_habil(dt.date(anyo, mes, dia)), modelo, desc, periodo, colectivo))

    # --- Trimestrales (día 20 de abril/julio/octubre; 4T en enero) ---
    trimestres = [(4, "1T"), (7, "2T"), (10, "3T")]
    for mes, tri in trimestres:
        add(mes, 20, "111", "Retenciones IRPF trabajadores y profesionales", tri, "Empleadores y quienes pagan a profesionales")
        add(mes, 20, "115", "Retenciones alquileres", tri, "Quienes pagan alquiler de local")
        add(mes, 20, "130/131", "Pago fraccionado IRPF (directa/módulos)", tri, "Autónomos")
        add(mes, 20, "303", "Autoliquidación IVA", tri, "Autónomos y empresas con IVA")
        add(mes, 20, "349", "Operaciones intracomunitarias", tri, "Quienes operan con la UE")
    # 4T del año anterior + resúmenes anuales (enero)
    add(1, 20, "111", "Retenciones IRPF — 4T año anterior", "4T", "Empleadores")
    add(1, 20, "115", "Retenciones alquileres — 4T año anterior", "4T", "Quienes pagan alquiler de local")
    add(1, 20, "130/131", "Pago fraccionado IRPF — 4T año anterior", "4T", "Autónomos")
    add(1, 30, "303", "IVA — 4T año anterior", "4T", "Autónomos y empresas")
    add(1, 30, "390", "Resumen anual de IVA", "Anual", "Autónomos y empresas")
    add(1, 31, "180", "Resumen anual retenciones alquileres", "Anual", "Quienes pagan alquiler de local")
    add(1, 31, "190", "Resumen anual retenciones IRPF", "Anual", "Empleadores")

    # --- Anuales ---
    add(2, 28, "347", "Operaciones con terceros > 3.005,06 €", "Anual", "Pymes y autónomos")
    add(3, 31, "720", "Bienes y derechos en el extranjero", "Anual", "Residentes con bienes fuera > 50.000 €")
    add(6, 30, "100", "Declaración de la Renta (fin de campaña; con domiciliación ~25/06)", "Anual", "Particulares y autónomos")
    add(7, 25, "200", "Impuesto de Sociedades (ejercicio = año natural)", "Anual", "Sociedades")

    # --- Pagos fraccionados IS (modelo 202) ---
    for mes in (4, 10, 12):
        add(mes, 20, "202", "Pago fraccionado Impuesto de Sociedades", f"{mes:02d}", "Sociedades (obligadas o con cuota positiva)")

    # --- Cuentas anuales (mercantil, ejercicio = año natural) ---
    add(7, 30, "Cuentas anuales", "Depósito en el Registro Mercantil (aprobadas antes del 30/06)", "Anual", "Sociedades")
    add(4, 30, "Libros", "Legalización de libros contables en el Registro Mercantil", "Anual", "Sociedades")

    return V


def proximos_vencimientos(desde: dt.date | None = None, dias: int = 60) -> list[Vencimiento]:
    """Vencimientos en los próximos `dias` días a partir de `desde` (hoy)."""
    desde = desde or dt.date.today()
    hasta = desde + dt.timedelta(days=dias)
    todos = _vencimientos_del_anyo(desde.year) + _vencimientos_del_anyo(desde.year + 1)
    return sorted((v for v in todos if desde <= v.fecha <= hasta), key=lambda v: v.fecha)

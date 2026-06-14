"""
Informe de diagnóstico digital — HTML white-label, listo para enviar al cliente.

Es el "caballo de Troya" documental: llegas (o te adelantas) a la reunión con
un diagnóstico profesional con SU marca de agencia, sus datos reales, lo que
pierde y la solución con ROI. Autocontenido (CSS inline) → se abre en cualquier
navegador y se imprime a PDF (Ctrl+P).

IMPORTANTE: es un documento para EL CLIENTE. No incluye métricas internas de la
agencia (win probability, lógica de pricing): solo lo que aporta valor a él.
"""
from datetime import datetime
from typing import Optional

from .models import ProspectorResult


def _eur(n) -> str:
    try:
        return f"{float(n):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _barra(score: float, color: str) -> str:
    return (
        f"<div style='background:#eef2f7;border-radius:6px;height:9px;overflow:hidden'>"
        f"<div style='width:{score}%;background:{color};height:9px'></div></div>"
    )


def _color_score(s: float) -> str:
    if s >= 75:
        return "#16a34a"
    if s >= 50:
        return "#eab308"
    if s >= 25:
        return "#f97316"
    return "#dc2626"


def generar_informe_html(
    result: ProspectorResult,
    agencia: str = "MerakIA",
    color_marca: str = "#4f46e5",
    contacto: str = "",
) -> str:
    """Devuelve el HTML completo y autocontenido del informe de diagnóstico."""
    b = result.business
    sc = result.scorecard or {}
    perd = result.perdidas or []
    comp = result.competitive or {}
    ps = result.pagespeed or {}
    paquetes = result.paquetes or []
    reco = next((p for p in paquetes if p.get("recomendado")), (paquetes[0] if paquetes else None))

    hoy = datetime.now().strftime("%d/%m/%Y")
    mad = sc.get("score_global")
    secciones = []

    # ── Resumen ejecutivo ─────────────────────────────────────────────────
    resumen_items = []
    if mad is not None:
        resumen_items.append(
            f"<div class='kpi'><div class='kpi-num' style='color:{_color_score(mad)}'>{mad:.0f}<span>/100</span></div>"
            f"<div class='kpi-lbl'>Madurez digital</div></div>"
        )
    if sc.get("percentil_nicho") is not None:
        por_encima = 100 - sc["percentil_nicho"]
        resumen_items.append(
            f"<div class='kpi'><div class='kpi-num'>{por_encima}%</div>"
            f"<div class='kpi-lbl'>de tu competencia lo hace mejor</div></div>"
        )
    if result.perdida_total_mes:
        resumen_items.append(
            f"<div class='kpi'><div class='kpi-num' style='color:#dc2626'>−{_eur(result.perdida_total_mes)}€</div>"
            f"<div class='kpi-lbl'>estimado que pierdes al mes</div></div>"
        )
    if resumen_items:
        secciones.append(f"<div class='kpis'>{''.join(resumen_items)}</div>")

    # ── Scorecard por dimensión ───────────────────────────────────────────
    dims = sc.get("dimensiones", [])
    if dims:
        filas = []
        for d in dims:
            s = d.get("score", 0)
            falta = d.get("senales_falta", [])
            tip = falta[0] if falta else "Bien cubierto"
            filas.append(
                f"<tr><td style='width:34%'>{d.get('icono','')} {d.get('nombre','')}</td>"
                f"<td style='width:40%'>{_barra(s, _color_score(s))}</td>"
                f"<td style='width:8%;text-align:right;font-weight:600;color:{_color_score(s)}'>{s:.0f}</td>"
                f"<td style='width:18%;font-size:12px;color:#64748b'>{tip}</td></tr>"
            )
        secciones.append(
            "<h2>Diagnóstico por área</h2>"
            f"<table class='dims'>{''.join(filas)}</table>"
        )

    # ── Dinero sobre la mesa ──────────────────────────────────────────────
    if perd:
        filas = "".join(
            f"<tr><td>{p.get('concepto','')}</td>"
            f"<td style='text-align:right;color:#dc2626;font-weight:600;white-space:nowrap'>−{_eur(p.get('euros_mes'))} €/mes</td></tr>"
            f"<tr><td colspan='2' style='font-size:12px;color:#64748b;padding-top:0'>{p.get('explicacion','')}</td></tr>"
            for p in perd
        )
        secciones.append(
            "<h2>💸 Lo que estás dejando sobre la mesa</h2>"
            f"<table class='perd'>{filas}</table>"
            f"<p class='total'>Pérdida estimada total: <b>−{_eur(result.perdida_total_mes)} €/mes</b> "
            f"(≈ {_eur((result.perdida_total_mes or 0) * 12)} €/año)</p>"
        )

    # ── Sistemas autónomos / IA ───────────────────────────────────────────
    au = result.automation or {}
    if au:
        if not au.get("es_autonomo"):
            secciones.append(
                "<h2>🤖 Atención automática 24/7 — tu mayor oportunidad</h2>"
                "<p>Tu negocio <b>no dispone de ningún sistema autónomo</b> (chatbot con IA "
                "ni agente de WhatsApp automatizado). Cada consulta que llega fuera de tu "
                "horario —noches, fines de semana, festivos— se queda sin respuesta y, muy "
                "probablemente, acaba en la competencia. Un agente con IA atiende, responde "
                "dudas y agenda citas <b>24/7, sin intervención humana</b>.</p>"
            )
        else:
            sist = ", ".join(au.get("sistemas_detectados", [])) or "sistema propio"
            secciones.append(
                "<h2>🤖 Atención automática</h2>"
                f"<p>Ya cuentas con cierta automatización ({sist}). El siguiente paso es "
                "integrarla con un agente de IA que unifique web y WhatsApp y haga seguimiento.</p>"
            )

    # ── Posición competitiva ──────────────────────────────────────────────
    if comp and comp.get("posicion"):
        bc = ""
        if comp.get("battle_card"):
            bc = "<ul>" + "".join(f"<li>{l}</li>" for l in comp["battle_card"]) + "</ul>"
        secciones.append(
            "<h2>⚔️ Tu posición frente a la competencia</h2>"
            f"<p>Ocupas el puesto <b>{comp['posicion']} de {comp['total']}</b> en madurez digital "
            f"dentro de tu sector en la zona (media del sector: {comp.get('media_nicho','—')}/100).</p>{bc}"
        )

    # ── Rendimiento web real ──────────────────────────────────────────────
    if ps and ps.get("performance_score") is not None:
        extra = f" · LCP {ps['lcp_s']:.1f}s" if ps.get("lcp_s") else ""
        secciones.append(
            "<h2>⚡ Rendimiento real de tu web (Google)</h2>"
            f"<p>Puntuación PageSpeed: <b style='color:{_color_score(ps['performance_score'])}'>"
            f"{ps['performance_score']}/100</b>{extra}. Google penaliza el posicionamiento de las "
            f"webs lentas (LCP por encima de 2,5s).</p>"
        )

    # ── Solución recomendada + ROI ────────────────────────────────────────
    if reco:
        roi = reco.get("roi", {})
        servicios = "".join(f"<li>{s}</li>" for s in reco.get("servicios", []))
        payback = roi.get("payback_meses")
        payback_txt = f"{payback:.1f} meses" if payback and payback < 99 else "—"
        secciones.append(
            "<h2>✅ Solución recomendada</h2>"
            f"<div class='pack'><div class='pack-name'>{reco.get('nombre','')}</div>"
            f"<ul class='pack-svc'>{servicios}</ul>"
            f"<div class='pack-roi'>"
            f"<div><span>Ingreso extra estimado</span><b style='color:#16a34a'>+{_eur(roi.get('ingreso_extra_mes'))} €/mes</b></div>"
            f"<div><span>Recuperación de la inversión</span><b>{payback_txt}</b></div>"
            f"<div><span>Inversión</span><b>{_eur(reco.get('setup'))} € + {_eur(reco.get('mensual'))} €/mes</b></div>"
            f"</div></div>"
            f"<p style='font-size:12px;color:#94a3b8'>Proyección conservadora basada en datos del sector. "
            f"Los resultados dependen de la implementación y del mercado.</p>"
        )

    contacto_html = f"<p style='margin-top:6px'>{contacto}</p>" if contacto else ""
    cuerpo = "".join(f"<section>{s}</section>" for s in secciones)

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagnóstico digital — {b.nombre}</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         color:#1e293b; background:#f1f5f9; margin:0; padding:24px; }}
  .doc {{ max-width:820px; margin:0 auto; background:#fff; border-radius:14px;
         box-shadow:0 4px 24px rgba(0,0,0,.08); overflow:hidden; }}
  .top {{ background:{color_marca}; color:#fff; padding:28px 36px; }}
  .top .brand {{ font-size:13px; opacity:.85; letter-spacing:.5px; text-transform:uppercase; }}
  .top h1 {{ margin:6px 0 2px; font-size:26px; }}
  .top .sub {{ opacity:.9; font-size:14px; }}
  section {{ padding:18px 36px; border-bottom:1px solid #f1f5f9; }}
  h2 {{ font-size:17px; margin:6px 0 12px; }}
  .kpis {{ display:flex; gap:14px; padding:24px 36px; flex-wrap:wrap; }}
  .kpi {{ flex:1; min-width:150px; background:#f8fafc; border-radius:10px; padding:16px; text-align:center; }}
  .kpi-num {{ font-size:30px; font-weight:800; }}
  .kpi-num span {{ font-size:14px; color:#94a3b8; font-weight:600; }}
  .kpi-lbl {{ font-size:12px; color:#64748b; margin-top:4px; }}
  table {{ width:100%; border-collapse:collapse; }}
  .dims td {{ padding:7px 6px; vertical-align:middle; font-size:14px; }}
  .perd td {{ padding:6px 6px; font-size:14px; border-bottom:1px solid #f1f5f9; }}
  .total {{ text-align:right; font-size:15px; margin-top:10px; }}
  ul {{ margin:6px 0; padding-left:20px; }} li {{ margin:3px 0; font-size:14px; }}
  .pack {{ border:2px solid {color_marca}; border-radius:12px; padding:18px; }}
  .pack-name {{ font-weight:800; font-size:18px; color:{color_marca}; }}
  .pack-svc {{ columns:2; }}
  .pack-roi {{ display:flex; gap:16px; flex-wrap:wrap; margin-top:10px; }}
  .pack-roi div {{ flex:1; min-width:150px; background:#f8fafc; border-radius:8px; padding:10px 12px; }}
  .pack-roi span {{ display:block; font-size:12px; color:#64748b; }}
  .pack-roi b {{ font-size:16px; }}
  .foot {{ padding:20px 36px; background:#f8fafc; font-size:13px; color:#64748b; }}
  @media print {{ body {{ background:#fff; padding:0; }} .doc {{ box-shadow:none; }} }}
</style></head>
<body><div class="doc">
  <div class="top">
    <div class="brand">{agencia} · Diagnóstico digital</div>
    <h1>{b.nombre}</h1>
    <div class="sub">{b.tipo} · {b.ciudad} · {hoy}</div>
  </div>
  {cuerpo}
  <div class="foot">
    Informe preparado por <b>{agencia}</b> a partir de datos públicos y análisis automatizado.
    {contacto_html}
  </div>
</div></body></html>"""

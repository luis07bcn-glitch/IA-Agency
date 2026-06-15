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
    gb = result.gbp_audit if hasattr(result, "gbp_audit") else None or {}
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

    # ── Ficha de Google Business Profile ─────────────────────────────────
    if gb and gb.get("senales_falta"):
        gbp_score = gb.get("completitud", 0)
        color_gbp = _color_score(gbp_score)
        problemas_gbp = "".join(f"<li>{p}</li>" for p in gb["senales_falta"])
        secciones.append(
            "<h2>📍 Tu ficha de Google Business — visibilidad local</h2>"
            f"<p>Completitud de tu ficha de Google: <b style='color:{color_gbp}'>{gbp_score}/100</b>. "
            f"La ficha de Google es lo primero que ven tus clientes antes de visitar tu web o llamarte.</p>"
            f"{_barra(gbp_score, color_gbp)}"
            f"<ul style='margin-top:12px'>{problemas_gbp}</ul>"
            f"<p style='font-size:13px;color:#64748b'>{gb.get('oportunidad','')}</p>"
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
        score_ps = ps["performance_score"]
        color_ps = _color_score(score_ps)

        def _cwv_row(label, value, unit, umbral_ok, umbral_warn, invert=False):
            """Fila de Core Web Vital con semáforo."""
            if value is None:
                return ""
            if invert:
                ok = value <= umbral_ok
                warn = value <= umbral_warn
            else:
                ok = value <= umbral_ok
                warn = value <= umbral_warn
            color = "#16a34a" if ok else ("#eab308" if warn else "#dc2626")
            icon = "✅" if ok else ("⚠️" if warn else "❌")
            return (
                f"<tr>"
                f"<td style='font-weight:600'>{label}</td>"
                f"<td style='text-align:right;font-weight:700;color:{color}'>{value}{unit}</td>"
                f"<td>{icon}</td>"
                f"<td style='font-size:12px;color:#64748b'>bueno &lt;{umbral_ok}{unit} · penaliza &gt;{umbral_warn}{unit}</td>"
                f"</tr>"
            )

        lcp = ps.get("lcp_s")
        cls = ps.get("cls")
        fcp = ps.get("fcp_s")
        tbt = ps.get("tbt_ms")

        filas_cwv = "".join(filter(None, [
            _cwv_row("LCP — carga principal", lcp, "s", 2.5, 4.0),
            _cwv_row("FCP — primer elemento", fcp, "s", 1.8, 3.0),
            _cwv_row("CLS — estabilidad visual", cls, "", 0.1, 0.25),
            _cwv_row("TBT — bloqueo interacción", tbt, "ms", 200, 600),
        ]))

        lcp_argumento = ""
        if lcp and lcp > 2.5:
            lcp_argumento = (
                f"<p style='background:#fef9c3;border-left:4px solid #eab308;"
                f"padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;margin-top:12px'>"
                f"<b>¿Qué significa para tu negocio?</b> Tu web tarda <b>{lcp}s</b> en mostrar "
                f"el contenido principal en móvil. Google considera penalizable cualquier valor "
                f"por encima de 2,5s — y el 70&nbsp;% de las búsquedas locales se hacen desde el "
                f"móvil. Cada segundo de retraso reduce las conversiones aproximadamente un 7&nbsp;%.</p>"
            )

        secciones.append(
            "<h2>⚡ Rendimiento real de tu web (Google PageSpeed)</h2>"
            f"<p>Puntuación global (móvil): "
            f"<b style='font-size:20px;color:{color_ps}'>{score_ps}/100</b> — "
            f"<i>{'bueno' if score_ps >= 90 else 'mejorable' if score_ps >= 50 else 'malo'}</i></p>"
            f"{_barra(score_ps, color_ps)}"
            f"<table class='dims' style='margin-top:14px'>{filas_cwv}</table>"
            f"{lcp_argumento}"
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
  @media print {{
    body {{ background:#fff; padding:0; }}
    .doc {{ box-shadow:none; border-radius:0; }}
    .pdf-btn {{ display:none !important; }}
  }}
</style></head>
<body><div class="doc">
  <div class="top">
    <div class="brand">{agencia} · Diagnóstico digital</div>
    <h1>{b.nombre}</h1>
    <div class="sub">{b.tipo} · {b.ciudad} · {hoy}</div>
    <button class="pdf-btn" onclick="window.print()"
      style="margin-top:14px;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.5);
             color:#fff;padding:7px 18px;border-radius:8px;cursor:pointer;font-size:13px;
             font-weight:600;letter-spacing:.3px">
      📄 Guardar como PDF
    </button>
  </div>
  {cuerpo}
  <div class="foot">
    Informe preparado por <b>{agencia}</b> a partir de datos públicos y análisis automatizado.
    {contacto_html}
    <button class="pdf-btn" onclick="window.print()"
      style="margin-top:12px;display:block;background:{color_marca};border:none;
             color:#fff;padding:8px 20px;border-radius:8px;cursor:pointer;font-size:13px;
             font-weight:600">
      📄 Guardar como PDF
    </button>
  </div>
</div></body></html>"""

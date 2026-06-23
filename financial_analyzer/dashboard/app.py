"""
Dashboard principal — Financial Analyzer.
Ejecutar: streamlit run financial_analyzer/dashboard/app.py
"""
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(message)s")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import io as _io
import contextlib
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from financial_analyzer.ingestion.storage import (
    init_db, get_series, get_latest_value, get_prices,
    get_freshness_status, get_stale_series
)
from financial_analyzer.engine.regime_engine import compute_regime_score, build_inputs_from_db
from financial_analyzer.engine.market_cycle import detect_cycle_phase
from financial_analyzer.ingestion.market_fetcher import compute_momentum

st.set_page_config(
    page_title="Financial Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _interpret(series_name: str, value, change=None) -> str:
    """Devuelve una interpretacion automatica en texto para mostrar bajo el grafico."""
    if value is None:
        return ""
    v = float(value)
    ch = float(change) if change is not None else None
    trend = ("subiendo" if ch and ch > 0 else "bajando") if ch is not None else ""

    if series_name == "VIX":
        zona = "calma extrema (<15)" if v < 15 else ("calma (15-18)" if v < 18 else ("alerta (18-25)" if v < 25 else ("miedo (25-35)" if v < 35 else "panico (>35)")))
        return f"VIX en {zona} — nivel actual {v:.1f}. {'Mayor volatilidad = menor apetito al riesgo.' if v > 25 else 'Mercado tranquilo.'}"
    if series_name == "SPREAD_HY":
        zona = "Risk-On (<3%)" if v < 3 else ("moderado (3-5%)" if v < 5 else "estres crediticio (>5%)")
        return f"Spread HY en zona {zona} ({v:.2f}%). {'Credito bajo presion — los inversores piden mas prima de riesgo.' if v > 5 else 'El credito de alto rendimiento funciona normal.'}{' Spread ' + trend + ' en los ultimos 3 meses.' if trend else ''}"
    if series_name == "NFCI":
        return f"NFCI en {v:.3f}. {'Condiciones financieras LAXAS — favorable para activos de riesgo.' if v < 0 else 'Condiciones financieras APRETADAS — presion sobre activos de riesgo.'} Un nivel {'muy negativo' if v < -0.5 else 'negativo' if v < 0 else 'positivo' if v < 0.5 else 'elevado'} historicamente {'acompana subidas de activos.' if v < 0 else 'precede correcciones.'}"
    if series_name == "ON_RRP":
        return f"ON RRP en ${v:,.0f}B. {'Elevado: exceso de liquidez aparcado en la Fed — cuando drene ira a mercados.' if v > 500 else 'Bajo o drenado: la liquidez excedente ya ha llegado al sistema financiero.' if v < 100 else 'Nivel moderado de liquidez excedente.'}"
    if series_name == "SOFR":
        return f"SOFR en {v:.3f}% — tipo interbancario overnight. {'Spike detectado: posible tension en el mercado repo.' if ch and ch > 0.2 else 'Funcionamiento normal del mercado repo.'}"
    if series_name == "CURVE_SPREAD_2Y10Y":
        return f"Curva 10Y-2Y en {v:.2f}%. {'CURVA NORMAL: los bonos largos rinden mas que los cortos — señal de expansion economica.' if v > 0 else 'CURVA INVERTIDA: los bonos cortos rinden mas — historicamente predice recesion en 6-18 meses.'}"
    if series_name == "T10Y3M":
        return f"Spread 10Y-3M en {v:.2f}%. {'POSITIVO: curva inclinada, señal de crecimiento.' if v > 0 else 'INVERTIDO: señal de recesion segun la Fed de Nueva York (modelo Estrella-Mishkin). Alta precision historica.'}"
    if series_name == "FED_BALANCE":
        return f"Balance Fed en ${v:,.0f}B. {'Expansion (QE): inyeccion de liquidez al sistema — historicamente positivo para activos de riesgo.' if ch and ch > 0 else 'Contraccion (QT): drenaje de liquidez — presion sobre activos de alta beta.' if ch and ch < 0 else ''}"
    if series_name == "DEFICIT_PCT_GDP":
        return f"Deficit fiscal EEUU en {v:.1f}% del PIB (TTM). {'Deficit elevado: el gasto publico actua como suelo implicito bajo los activos — la liquidez fiscal sostiene el mercado.' if v < -4 else 'Deficit moderado.' if v < -2 else 'Deficit reducido: menor soporte fiscal.'}"
    if series_name == "CPI_YOY":
        return f"IPC EEUU en {v:.1f}% interanual. {'Muy por encima del objetivo Fed (2%) — presion para mantener tipos altos.' if v > 3.5 else 'Cerca del objetivo Fed (2%) — politica monetaria puede relajarse.' if v < 2.5 else 'IPC moderado pero Fed vigilante.'}"
    if series_name == "RETAIL_SALES":
        trend_txt = f" ({'+' if ch and ch > 0 else ''}{ch:.1f}% vs hace 3 meses)" if ch else ""
        return f"Ventas minoristas{trend_txt}. {'Consumo fuerte — el motor de la economia EEUU aguanta.' if ch and ch > 2 else 'Consumo debilitandose — señal de desaceleracion economica.' if ch and ch < 0 else ''}"
    return ""

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2130; border-radius: 10px; padding: 16px;
        border-left: 4px solid #3498db; margin-bottom: 10px;
    }
    .regime-badge {
        font-size: 2rem; font-weight: bold; padding: 12px 24px;
        border-radius: 8px; text-align: center; margin: 10px 0;
    }
    .risk-on  { background: #1a4a2e; color: #2ecc71; border: 2px solid #2ecc71; }
    .neutral  { background: #4a3a1a; color: #f39c12; border: 2px solid #f39c12; }
    .risk-off { background: #4a1a1a; color: #e74c3c; border: 2px solid #e74c3c; }
    .stale-warning { background: #4a3a00; color: #f1c40f; padding: 8px 12px;
                     border-radius: 6px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── REGIME SCORE GLOBAL (cacheado 10 min) ────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _get_regime_cached(db_path: str):
    import io as _io, contextlib
    _buf = _io.StringIO()
    with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
        inp = build_inputs_from_db(db_path)
    return compute_regime_score(inp).to_dict()

_db_path = str(Path(__file__).parent.parent / "data" / "financial_data.duckdb")
_regime_global = _get_regime_cached(_db_path)

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Financial Analyzer")

    # Banner de régimen siempre visible
    _rg = _regime_global
    _badge_color = {"RISK-ON": "#2ecc71", "NEUTRAL": "#f39c12", "RISK-OFF": "#e74c3c"}.get(_rg["regime"], "#aaa")
    _badge_bg    = {"RISK-ON": "#1a4a2e", "NEUTRAL": "#4a3a1a", "RISK-OFF": "#4a1a1a"}.get(_rg["regime"], "#222")
    st.markdown(
        f'<div style="background:{_badge_bg};border:2px solid {_badge_color};border-radius:8px;'
        f'padding:10px;text-align:center;margin-bottom:8px">'
        f'<span style="color:{_badge_color};font-size:1.3rem;font-weight:bold">{_rg["regime"]}</span><br>'
        f'<span style="color:#ccc;font-size:0.95rem">{_rg["total"]:.0f}/100 pts</span></div>',
        unsafe_allow_html=True
    )
    # Mini sub-scores
    _sub_labels = [("Liq", _rg["liquidity"], 28), ("Riesgo", _rg["risk_appetite"], 25),
                   ("Crec", _rg["growth"], 20), ("Val", _rg["valuation"], 12), ("Mom", _rg["momentum"], 15)]
    _cols = st.columns(5)
    for _ci, (_lbl, _val, _mx) in enumerate(_sub_labels):
        _pct = _val / _mx
        _c = "#2ecc71" if _pct > 0.6 else ("#f39c12" if _pct > 0.35 else "#e74c3c")
        _cols[_ci].markdown(f'<div style="text-align:center;font-size:0.7rem;color:#aaa">{_lbl}</div>'
                            f'<div style="text-align:center;font-size:0.85rem;color:{_c};font-weight:bold">{_val:.0f}</div>',
                            unsafe_allow_html=True)

    st.divider()
    page = st.radio("Navegación", [
        "🏠 Overview & Régimen",
        "📰 Noticias & Eventos",
        "📈 Mercados & Momentum",
        "🌍 Macro & Liquidez",
        "🔄 Ciclo de Mercado",
        "🏢 Fundamentales",
        "💼 Portfolio",
        "🔍 Screener / Research",
        "🧠 Condiciones Financieras",
        "📡 Indicadores Adelantados",
        "💾 Exportar Datos",
        "⚠️ Estado de Datos",
    ])

    st.divider()
    # Botones rápidos de período
    st.caption("Período")
    _btn_cols = st.columns(4)
    _now = datetime.now()
    _preset = None
    if _btn_cols[0].button("YTD"):  _preset = datetime(_now.year, 1, 1)
    if _btn_cols[1].button("1A"):   _preset = _now - timedelta(days=365)
    if _btn_cols[2].button("3A"):   _preset = _now - timedelta(days=3*365)
    if _btn_cols[3].button("Max"):  _preset = datetime(2010, 1, 1)

    _default_start = _preset if _preset else (_now - timedelta(days=3*365))
    start_date = st.date_input("Desde", _default_start)
    if st.button("Actualizar datos ahora", type="primary"):
        with st.spinner("Descargando datos..."):
            import io, contextlib
            log_buffer = io.StringIO()
            try:
                from financial_analyzer.update_data import run_update
                with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
                    run_update()
                st.success("Datos actualizados correctamente")
            except Exception as e:
                st.error(f"Error: {e}")
            log = log_buffer.getvalue()
            if log:
                with st.expander("Log de actualización"):
                    st.text(log)

# ─────────────────────────────────────────────────────────────
# PÁGINA 1: OVERVIEW & RÉGIMEN
# ─────────────────────────────────────────────────────────────
if "Overview" in page:
    st.title("Visión Global del Mercado")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Alerta de datos obsoletos
    stale = get_stale_series()
    if not stale.empty:
        st.markdown(
            f'<div class="stale-warning">⚠️ {len(stale)} series con datos obsoletos. '
            f'Revisa la pestaña "Estado de Datos".</div>',
            unsafe_allow_html=True
        )
        st.write("")

    # ── Construir inputs desde DB (v2: deficit + eurodolar) ──
    import io as _io, contextlib
    _buf = _io.StringIO()
    with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
        inputs = build_inputs_from_db(
            str(Path(__file__).parent.parent / "data" / "financial_data.duckdb"),
            start=str(start_date)
        )

    regime = compute_regime_score(inputs)
    r = regime.to_dict()

    # ── PANEL PRINCIPAL RÉGIMEN ──
    col_regime, col_gauge = st.columns([1, 1])

    with col_regime:
        css_class = {"RISK-ON": "risk-on", "NEUTRAL": "neutral", "RISK-OFF": "risk-off"}[r["regime"]]
        st.markdown(
            f'<div class="regime-badge {css_class}">{r["regime"]}<br>'
            f'<span style="font-size:1.2rem">{r["total"]}/100 puntos</span></div>',
            unsafe_allow_html=True
        )
        st.info(f"**Acción sugerida:** {r['action']}")

        st.write("**Sub-scores:**")
        sub = {
            "Liquidez + Deficit + Eurodolar": (r["liquidity"], 28),
            "Apetito Riesgo + NFCI + DXY":   (r["risk_appetite"], 25),
            "Crecimiento + Retail Sales":      (r["growth"], 20),
            "Valoracion (curvas + tipos)":     (r["valuation"], 12),
            "Momentum + BTC-Liquidez":         (r["momentum"], 15),
        }
        for label, (val, max_val) in sub.items():
            pct = val / max_val
            color = "#2ecc71" if pct > 0.6 else ("#f39c12" if pct > 0.35 else "#e74c3c")
            st.markdown(f"**{label}**: {val:.0f}/{max_val}")
            st.progress(pct)

    with col_gauge:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=r["total"],
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Score Total (0-100)", "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#3498db"},
                "steps": [
                    {"range": [0, 40],  "color": "#2d1b1b"},
                    {"range": [40, 70], "color": "#2d2a1b"},
                    {"range": [70, 100],"color": "#1b2d1e"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.75,
                    "value": r["total"],
                },
            }
        ))
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    # ── ALERTAS CRITICAS DEL MOTOR ──
    if r.get("warnings"):
        st.divider()
        st.subheader("Alertas del Motor de Regimenes")
        for w in r["warnings"]:
            st.warning(w)

    # ── MÉTRICAS CLAVE ──
    st.divider()
    st.subheader("Variables Clave en Tiempo Real")

    vix_val, _    = get_latest_value("VIX")
    hy_val, _     = get_latest_value("SPREAD_HY")
    ted_val, _    = get_latest_value("TED_SPREAD")
    curve_val, _  = get_latest_value("CURVE_SPREAD_2Y10Y")
    t10y3m_val, _ = get_latest_value("T10Y3M")
    nfci_val, _   = get_latest_value("NFCI")
    onrrp_val, _  = get_latest_value("ON_RRP")
    deficit_val, _= get_latest_value("DEFICIT_PCT_GDP")
    sofr_val, _   = get_latest_value("SOFR")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Liquidez & Fontaneria**")
        st.metric("ON RRP",      f"${onrrp_val:,.0f}B" if onrrp_val else "N/D",
                 help="Alto = exceso liquidez aparcado | Cayendo = liquidez al mercado")
        st.metric("SOFR",        f"{sofr_val:.3f}%" if sofr_val else "N/D",
                 help="Tipo interbancario overnight")
        st.metric("Deficit/PIB", f"{deficit_val:.1f}%" if deficit_val else "N/D",
                 help="Deficit <-5% = suelo implicito fuerte bajo activos")
        st.metric("TED Spread",  f"{ted_val:.2f}%" if ted_val else "N/D",
                 help="<0.3% = liquidez interbancaria OK | >0.5% = alerta")

    with col2:
        st.markdown("**Apetito al Riesgo**")
        st.metric("VIX",         f"{vix_val:.1f}" if vix_val else "N/D",
                 help="<18 calma | 18-25 alerta | >30 panico")
        st.metric("Spread HY",   f"{hy_val:.2f}%" if hy_val else "N/D",
                 help="<3% Risk-On | >5% estres crediticio")
        st.metric("NFCI",        f"{nfci_val:.3f}" if nfci_val else "N/D",
                 help="Negativo = condiciones laxas | Positivo = estres")

    with col3:
        st.markdown("**Tipos & Curvas**")
        st.metric("T10Y2Y",      f"{curve_val:.2f}%" if curve_val else "N/D",
                 delta="Normal" if (curve_val or 0) > 0 else "Invertida",
                 delta_color="normal" if (curve_val or 0) > 0 else "inverse")
        st.metric("T10Y3M",      f"{t10y3m_val:.2f}%" if t10y3m_val else "N/D",
                 delta="Normal" if (t10y3m_val or 0) > 0 else "Invertida",
                 delta_color="normal" if (t10y3m_val or 0) > 0 else "inverse")

    # ── INTERPRETACIONES AUTOMATICAS ──
    st.divider()
    st.subheader("Lectura del mercado — interpretacion automatica")
    _interp_items = [
        ("NFCI",              nfci_val,   None,       "Condiciones Financieras"),
        ("VIX",               vix_val,    None,       "Volatilidad"),
        ("SPREAD_HY",         hy_val,     None,       "Credito High Yield"),
        ("CURVE_SPREAD_2Y10Y",curve_val,  None,       "Curva de Tipos"),
        ("T10Y3M",            t10y3m_val, None,       "Indicador Recesion"),
        ("ON_RRP",            onrrp_val,  None,       "Liquidez (ON RRP)"),
        ("DEFICIT_PCT_GDP",   deficit_val,None,       "Deficit Fiscal"),
    ]
    _interp_cols = st.columns(2)
    for _i, (_sn, _vl, _ch, _title) in enumerate(_interp_items):
        _txt = _interpret(_sn, _vl, _ch)
        if _txt:
            _interp_cols[_i % 2].info(f"**{_title}**: {_txt}")

    # ── CADENA DE TRANSMISIÓN: ¿Es sostenible el Risk-On? ──────
    st.divider()
    st.subheader("Cadena de transmision — ¿Es el Risk-On sostenible o una trampa?")
    st.caption(
        "Tres eslabones conectados: cuando el estres del consumidor real llega al credito corporativo "
        "y los bancos cierran el grifo, el mercado puede girar violentamente."
    )

    # Cargar valores necesarios
    _cc_delinq_val, _  = get_latest_value("CC_DELINQ")
    _auto_delinq_val, _= get_latest_value("AUTO_DELINQ")
    _hy_spread_val, _  = get_latest_value("SPREAD_HY")
    _sloos_ci_val, _   = get_latest_value("SLOOS_CI")
    _sloos_cc_val, _   = get_latest_value("SLOOS_CC")
    _sloos_biz_val, _  = get_latest_value("SLOOS_BUSINESS")

    # ── Evaluar cada eslabón ──────────────────────────────────
    # Eslabón 1: Estrés en consumo (impagos tarjetas + auto)
    _link1_score = 0
    _link1_signals = []
    if _cc_delinq_val:
        if _cc_delinq_val > 5:   _link1_score += 3; _link1_signals.append(f"Impagos tarjetas criticos: {_cc_delinq_val:.2f}%")
        elif _cc_delinq_val > 3: _link1_score += 1; _link1_signals.append(f"Impagos tarjetas al alza: {_cc_delinq_val:.2f}%")
    if _auto_delinq_val:
        if _auto_delinq_val > 3: _link1_score += 2; _link1_signals.append(f"Impagos auto elevados: {_auto_delinq_val:.2f}%")
        elif _auto_delinq_val > 2: _link1_score += 1; _link1_signals.append(f"Impagos auto subiendo: {_auto_delinq_val:.2f}%")
    _link1_status = "🟢 CONTENIDO" if _link1_score == 0 else ("🟡 ALERTA" if _link1_score <= 2 else "🔴 CRITICO")
    _link1_color  = "#2ecc71" if _link1_score == 0 else ("#f39c12" if _link1_score <= 2 else "#e74c3c")

    # Eslabón 2: Diferenciales de crédito corporativo HY
    _link2_score = 0
    _link2_signals = []
    if _hy_spread_val:
        if _hy_spread_val > 6:   _link2_score += 3; _link2_signals.append(f"Spread HY en zona crisis: {_hy_spread_val:.2f}%")
        elif _hy_spread_val > 4: _link2_score += 2; _link2_signals.append(f"Spread HY en expansion: {_hy_spread_val:.2f}%")
        elif _hy_spread_val > 3: _link2_score += 1; _link2_signals.append(f"Spread HY moderado: {_hy_spread_val:.2f}%")
        else:                     _link2_signals.append(f"Spread HY comprimido (Risk-On): {_hy_spread_val:.2f}%")
    _link2_status = "🟢 COMPRIMIDO" if _link2_score == 0 else ("🟡 AMPLIANDO" if _link2_score <= 2 else "🔴 ESTRES")
    _link2_color  = "#2ecc71" if _link2_score == 0 else ("#f39c12" if _link2_score <= 2 else "#e74c3c")

    # Eslabón 3: SLOOS — bancos cerrando el grifo
    _sloos_max = max(filter(None, [_sloos_ci_val, _sloos_cc_val, _sloos_biz_val] or [0]), default=None)
    _link3_score = 0
    _link3_signals = []
    if _sloos_max is not None:
        if _sloos_max > 30:   _link3_score += 3; _link3_signals.append(f"Bancos endureciendo credito agresivamente ({_sloos_max:.0f}% neto)")
        elif _sloos_max > 10: _link3_score += 2; _link3_signals.append(f"Bancos moderadamente restrictivos ({_sloos_max:.0f}% neto)")
        elif _sloos_max > 0:  _link3_score += 1; _link3_signals.append(f"Bancos ligeramente cautelosos ({_sloos_max:.0f}% neto)")
        else:                  _link3_signals.append(f"Bancos relajando condiciones ({_sloos_max:.0f}% neto) — favorable")
    else:
        _link3_signals.append("SLOOS pendiente de actualizar (trimestral)")
    _link3_status = "🟢 RELAJADO" if _link3_score == 0 else ("🟡 CAUTELOSO" if _link3_score <= 2 else "🔴 RESTRICTIVO")
    _link3_color  = "#2ecc71" if _link3_score == 0 else ("#f39c12" if _link3_score <= 2 else "#e74c3c")

    # ── Diagnóstico global de la cadena ──────────────────────
    _chain_total = _link1_score + _link2_score + _link3_score
    if _chain_total == 0:
        _chain_verdict = "RISK-ON SOSTENIBLE"
        _chain_color   = "#2ecc71"
        _chain_bg      = "#1a4a2e"
        _chain_text    = ("Los tres eslabones en verde: el consumidor aguanta, el credito corporativo esta barato "
                          "y los bancos prestan con normalidad. La expansion tiene base real.")
    elif _chain_total <= 3:
        _chain_verdict = "RIESGO LATENTE — VIGILAR"
        _chain_color   = "#f39c12"
        _chain_bg      = "#4a3a1a"
        _chain_text    = ("Señales de tension en alguno de los eslabones. El Risk-On puede continuar "
                          "pero la base se esta debilitando. Monitoriza semanalmente los spreads.")
    elif _chain_total <= 6:
        _chain_verdict = "POSIBLE TRAMPA RISK-ON"
        _chain_color   = "#e67e22"
        _chain_bg      = "#4a2a1a"
        _chain_text    = ("Dos o mas eslabones bajo presion. La divergencia entre mercados financieros "
                          "y economia real es significativa. Reduce beta y aumenta coberturas.")
    else:
        _chain_verdict = "TRAMPA RISK-ON — PELIGRO"
        _chain_color   = "#e74c3c"
        _chain_bg      = "#4a1a1a"
        _chain_text    = ("Cadena de transmision activada: el consumidor no paga, el credito se encarece "
                          "y los bancos cierran el grifo. El giro de mercado puede ser violento. "
                          "Prioriza capital preservation.")

    # ── Visualización de la cadena ────────────────────────────
    st.markdown(f"""
    <div style="background:{_chain_bg};border:2px solid {_chain_color};border-radius:10px;
                padding:14px 20px;margin:10px 0;text-align:center">
        <div style="font-size:1.4rem;font-weight:bold;color:{_chain_color}">
            Veredicto: {_chain_verdict}
        </div>
        <div style="color:#ccc;font-size:0.9rem;margin-top:6px">{_chain_text}</div>
    </div>
    """, unsafe_allow_html=True)

    _ch1, _ch_arr1, _ch2, _ch_arr2, _ch3 = st.columns([5, 1, 5, 1, 5])

    def _chain_card(col, num, title, subtitle, status, color, signals, metric_val, metric_label):
        col.markdown(f"""
        <div style="background:#1a1a2e;border:2px solid {color};border-radius:10px;
                    padding:14px;text-align:center;height:220px">
            <div style="color:#888;font-size:0.75rem;margin-bottom:4px">ESLABON {num}</div>
            <div style="color:{color};font-size:1rem;font-weight:bold">{title}</div>
            <div style="color:#aaa;font-size:0.8rem;margin:4px 0">{subtitle}</div>
            <div style="font-size:1.6rem;margin:8px 0">{status}</div>
            <div style="color:{color};font-size:0.85rem;font-weight:bold">
                {metric_val if metric_val else "N/D"} {metric_label}
            </div>
            <div style="color:#888;font-size:0.72rem;margin-top:6px">
                {"<br>".join(signals[:2]) if signals else "Sin señales"}
            </div>
        </div>""", unsafe_allow_html=True)

    _chain_card(
        _ch1, "1", "Estres Consumidor",
        "Impagos tarjetas + auto",
        _link1_status, _link1_color, _link1_signals,
        f"{_cc_delinq_val:.2f}%" if _cc_delinq_val else None, "mora tarjetas"
    )
    _ch_arr1.markdown(
        '<div style="text-align:center;font-size:2rem;color:#666;margin-top:80px">▶</div>',
        unsafe_allow_html=True
    )
    _chain_card(
        _ch2, "2", "Diferenciales HY",
        "Credito corporativo alto riesgo",
        _link2_status, _link2_color, _link2_signals,
        f"{_hy_spread_val:.2f}%" if _hy_spread_val else None, "spread HY"
    )
    _ch_arr2.markdown(
        '<div style="text-align:center;font-size:2rem;color:#666;margin-top:80px">▶</div>',
        unsafe_allow_html=True
    )
    _chain_card(
        _ch3, "3", "SLOOS — Bancos",
        "Condiciones credito bancario",
        _link3_status, _link3_color, _link3_signals,
        f"{_sloos_max:.0f}%" if _sloos_max is not None else None, "% neto restrictivo"
    )

    # ── Gráfico histórico superpuesto de los 3 eslabones ──────
    with st.expander("Ver evolucion historica de la cadena de transmision"):
        _cc_df_ov  = get_series("CC_DELINQ",    start=str(start_date))
        _hy_df_ov  = get_series("SPREAD_HY",    start=str(start_date))
        _sloos_df  = get_series("SLOOS_BUSINESS",start=str(start_date))

        if not _cc_df_ov.empty and not _hy_df_ov.empty:
            _fig_chain = go.Figure()
            _fig_chain.add_scatter(
                x=_cc_df_ov["date"], y=_cc_df_ov["value"],
                name="Impagos tarjetas (%)", line=dict(color="#e74c3c", width=2)
            )
            _fig_chain.add_scatter(
                x=_hy_df_ov["date"], y=_hy_df_ov["value"],
                name="Spread HY (%)", yaxis="y2", line=dict(color="#f39c12", width=2, dash="dot")
            )
            if not _sloos_df.empty:
                _fig_chain.add_scatter(
                    x=_sloos_df["date"], y=_sloos_df["value"],
                    name="SLOOS Empresas (% neto restrict.)", yaxis="y2",
                    line=dict(color="#9b59b6", width=1.5, dash="dash")
                )
            # Sombreado recesiones
            _rec_ov = get_series("USREC", start=str(start_date))
            if not _rec_ov.empty:
                _in_r2 = False; _rs2 = None
                for _, _rw in _rec_ov.iterrows():
                    if _rw["value"] == 1 and not _in_r2: _in_r2 = True; _rs2 = _rw["date"]
                    elif _rw["value"] == 0 and _in_r2:
                        _in_r2 = False
                        _fig_chain.add_vrect(x0=_rs2, x1=_rw["date"],
                                             fillcolor="red", opacity=0.08, layer="below", line_width=0)
            _fig_chain.update_layout(
                title="Cadena de transmision historica — impagos → spreads → condiciones bancarias",
                yaxis=dict(title="Impagos (%)", color="#e74c3c"),
                yaxis2=dict(title="Spread HY (%) / SLOOS (%)", overlaying="y", side="right", color="#f39c12"),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=380,
                legend=dict(orientation="h"), margin=dict(t=50, b=20)
            )
            st.plotly_chart(_fig_chain, use_container_width=True)
            st.caption(
                "Patron historico: en 2007-08 los impagos de tarjetas y subprime (eslabon 1) se dispararon 6-12 meses "
                "ANTES de que los spreads HY explotaran (eslabon 2). Los bancos empezaron a endurecer el SLOOS "
                "(eslabon 3) justo en el punto medio. Cuando los tres se mueven a la vez, la caida es acelerada."
            )

    # ── DETALLES DEL SCORING ──
    with st.expander("Ver detalles del scoring — auditoria completa"):
        details = r.get("details", {})
        if details:
            rows_d = []
            for key, d in details.items():
                rows_d.append({
                    "Variable": d.get("label", key),
                    "Valor": str(d.get("value", "—")),
                    "Puntos": d.get("pts", 0),
                })
            df_det = pd.DataFrame(rows_d).sort_values("Puntos", ascending=False)
            st.dataframe(df_det, use_container_width=True, hide_index=True)

            # Inputs brutos usados por el motor
            with st.expander("Inputs brutos del motor"):
                st.json({k: (round(v, 3) if isinstance(v, float) else v)
                         for k, v in inputs.items() if v is not None})
        else:
            st.write("Sin datos suficientes para mostrar detalles.")

# ─────────────────────────────────────────────────────────────
# PÁGINA 2: NOTICIAS & EVENTOS
# ─────────────────────────────────────────────────────────────
elif "Noticias" in page:
    from financial_analyzer.news.fetcher import fetch_news, get_macro_calendar, CATEGORIES, CATEGORY_IMPACT

    st.title("Noticias & Eventos de Mercado")
    st.caption("Noticias relevantes filtradas por impacto en mercados: geopolítica, Fed, macro, crédito, energía y salud.")

    # ── Régimen banner ──
    _rg_n = _regime_global
    _rg_nc = {"RISK-ON": "#2ecc71", "NEUTRAL": "#f39c12", "RISK-OFF": "#e74c3c"}.get(_rg_n["regime"], "#aaa")
    st.markdown(
        f'<div style="background:#1a1a2e;border-left:4px solid {_rg_nc};padding:8px 16px;'
        f'border-radius:6px;margin-bottom:16px">'
        f'<span style="color:{_rg_nc};font-weight:bold">Régimen: {_rg_n["regime"]} ({_rg_n["total"]:.0f}/100)</span>'
        f' — <span style="color:#aaa;font-size:0.9rem">Lee las noticias en contexto del régimen actual.</span>'
        f'</div>', unsafe_allow_html=True
    )

    # ── Controles ──
    _nc1, _nc2, _nc3 = st.columns([2, 2, 1])
    with _nc1:
        _cat_filter = st.multiselect(
            "Filtrar por categoría",
            list(CATEGORIES.keys()),
            default=list(CATEGORIES.keys()),
        )
    with _nc2:
        _impact_filter = st.multiselect(
            "Impacto mínimo",
            ["🔴 Critico", "⚠️ Alto", "🟠 Alto", "🟡 Medio"],
            default=["🔴 Critico", "⚠️ Alto", "🟠 Alto", "🟡 Medio"],
        )
    with _nc3:
        _refresh_btn = st.button("Actualizar noticias", type="primary")

    # ── Cache noticias (5 min) ──
    @st.cache_data(ttl=300, show_spinner=False)
    def _load_news():
        return fetch_news(max_per_feed=10)

    if _refresh_btn:
        st.cache_data.clear()

    with st.spinner("Cargando noticias..."):
        _all_news = _load_news()

    # Filtrar
    _filtered = [
        n for n in _all_news
        if any(c in _cat_filter for c in n["categories"])
        and n["impact"] in _impact_filter
    ]

    if not _filtered:
        st.info("No hay noticias que coincidan con los filtros seleccionados. Prueba a ampliar los criterios o actualiza.")
    else:
        st.caption(f"{len(_filtered)} noticias relevantes encontradas de {len(_all_news)} totales analizadas")

        # ── Resumen por categoría ──
        _cat_counts = {}
        for n in _filtered:
            for c in n["categories"]:
                _cat_counts[c] = _cat_counts.get(c, 0) + 1
        if _cat_counts:
            _cc_sorted = sorted(_cat_counts.items(), key=lambda x: x[1], reverse=True)
            _cc_cols = st.columns(min(len(_cc_sorted), 7))
            for _ci, (_cat, _cnt) in enumerate(_cc_sorted):
                _imp = CATEGORY_IMPACT.get(_cat, "🟡")
                _cc_cols[_ci % len(_cc_cols)].metric(_cat, f"{_cnt} noticias", help=f"Impacto: {_imp}")

        st.divider()

        # ── Feed de noticias ──
        _impact_order = {"🔴 Critico": 0, "⚠️ Alto": 1, "🟠 Alto": 2, "🟡 Medio": 3}
        _sorted_news = sorted(_filtered, key=lambda x: (_impact_order.get(x["impact"], 9),
                                                         -x["date"].timestamp() if hasattr(x["date"], "timestamp") else 0))

        for _n in _sorted_news:
            _imp = _n["impact"]
            _border = {"🔴 Critico": "#e74c3c", "⚠️ Alto": "#e67e22",
                       "🟠 Alto": "#f39c12", "🟡 Medio": "#3498db"}.get(_imp, "#555")
            _cats_str = " · ".join(_n["categories"])
            _date_str = _n["date"].strftime("%d/%m %H:%M") if hasattr(_n["date"], "strftime") else "—"

            st.markdown(f"""
            <div style="border-left:4px solid {_border};background:#1a1a2e;border-radius:6px;
                        padding:12px 16px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="flex:1">
                        <span style="color:{_border};font-size:0.75rem;font-weight:bold">{_imp} &nbsp;|&nbsp; {_cats_str} &nbsp;|&nbsp; {_n['source']}</span>
                        <div style="color:#eee;font-size:1rem;font-weight:bold;margin:4px 0;line-height:1.3">
                            <a href="{_n['link']}" target="_blank" style="color:#eee;text-decoration:none">
                                {_n['title']}
                            </a>
                        </div>
                        <div style="color:#888;font-size:0.82rem;line-height:1.4">{_n['summary']}</div>
                    </div>
                    <div style="color:#666;font-size:0.75rem;min-width:70px;text-align:right;padding-left:12px">{_date_str}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Calendario macro semanal ──
    st.divider()
    st.subheader("Calendario macro — eventos clave de la semana")
    st.caption("Eventos de alto impacto en mercados EEUU (horario CET = ET +6h)")
    _calendar = get_macro_calendar()
    for _ev in _calendar:
        _ev_color = {"🔴 Critico": "#e74c3c", "🟠 Alto": "#f39c12", "🟡 Medio": "#3498db"}.get(_ev["impact"], "#555")
        st.markdown(
            f'<div style="border-left:3px solid {_ev_color};padding:6px 12px;margin:4px 0;background:#1a1a2e;border-radius:4px">'
            f'<span style="color:{_ev_color};font-size:0.8rem">{_ev["impact"]}</span> &nbsp;'
            f'<span style="color:#aaa;font-size:0.8rem">{_ev["date"]} {_ev["time"]} ET</span> &nbsp;'
            f'<span style="color:#eee;font-weight:bold">{_ev["event"]}</span> &nbsp;'
            f'<span style="color:#666;font-size:0.8rem">({_ev["source"]})</span>'
            f'</div>', unsafe_allow_html=True
        )

    # ── Nota sobre Trading Economics ──
    st.divider()
    with st.expander("¿Por qué no usamos Trading Economics directamente?"):
        st.markdown("""
**Trading Economics** tiene datos excelentes, pero su API es de **pago** (~$50–200/mes según el plan).

Lo que **ya tenemos** cubierto gratis equivalente a Trading Economics:
| Indicador TE | Fuente que usamos | Estado |
|---|---|---|
| US GDP, CPI, PCE, NFP | FRED (Federal Reserve) | ✅ Activo |
| Fed Funds Rate, Balance Sheet | FRED | ✅ Activo |
| Yield Curve, Spreads HY/IG | FRED | ✅ Activo |
| HICP Europa, Paro UE/ES | Eurostat | ✅ Activo |
| Precios SPX, BTC, Gold, Oil | yfinance | ✅ Activo |
| Retail Sales, IndPro, Claims | FRED | ✅ Activo |
| Hipotecas 30A, SLOOS | FRED | ✅ Activo |

**Lo que SÍ añadiría TE que no tenemos:**
- PMI compuesto en tiempo real (S&P Global — requiere licencia)
- Datos de más de 196 países (nosotros solo EEUU + UE)
- GDP en tiempo real (nowcasting) vs trimestral con lag
- Confianza del consumidor Europa (GfK, INSEE)

**Alternativas gratuitas para lo que falta:**
- **PMI flash**: publicado mensualmente gratis en prensa (S&P Global press release)
- **OCDE**: datos macro para países desarrollados (API gratuita)
- **World Bank**: datos históricos globales (API gratuita)
        """)

# ─────────────────────────────────────────────────────────────
# PÁGINA 2: MERCADOS & MOMENTUM
# ─────────────────────────────────────────────────────────────
elif "Mercados" in page:
    st.title("Mercados & Momentum")

    tickers_to_show = ["SPX", "NASDAQ", "IBEX", "EUROSTOXX", "BTC", "GOLD", "OIL"]
    col1, col2 = st.columns(2)

    with col1:
        selected = st.selectbox("Seleccionar instrumento", tickers_to_show)
        df_price = get_prices(selected, start=str(start_date))
        if not df_price.empty:
            fig = px.line(df_price, x="date", y="close", title=selected)
            # Añadir media 200d
            df_price["ma200"] = df_price["close"].rolling(200).mean()
            df_price["ma50"]  = df_price["close"].rolling(50).mean()
            fig.add_scatter(x=df_price["date"], y=df_price["ma200"],
                           mode="lines", name="MA 200", line=dict(color="orange", dash="dash"))
            fig.add_scatter(x=df_price["date"], y=df_price["ma50"],
                           mode="lines", name="MA 50", line=dict(color="cyan", dash="dot"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                             legend=dict(orientation="h"), height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Sin datos para {selected}. Ejecuta la actualización primero.")

    with col2:
        st.subheader("Tabla de Momentum")
        st.caption("ROC = Rate of Change | vs MA = distancia a media móvil")

        # Construir tabla de momentum con datos disponibles
        momentum_rows = []
        for ticker in tickers_to_show:
            df_p = get_prices(ticker, start=str(start_date))
            if df_p.empty or len(df_p) < 30:
                continue
            prices_series = df_p.set_index("date")["close"]
            latest = prices_series.iloc[-1]
            ma200 = prices_series.rolling(200).mean().iloc[-1]
            ma50  = prices_series.rolling(50).mean().iloc[-1]
            roc_1m = ((latest / prices_series.iloc[-22]) - 1) * 100 if len(prices_series) > 22 else None
            roc_3m = ((latest / prices_series.iloc[-63]) - 1) * 100 if len(prices_series) > 63 else None
            momentum_rows.append({
                "Ticker": ticker,
                "Precio": f"{latest:.2f}",
                "ROC 1M %": f"{roc_1m:.1f}" if roc_1m else "—",
                "ROC 3M %": f"{roc_3m:.1f}" if roc_3m else "—",
                "vs MA50 %": f"{((latest/ma50)-1)*100:.1f}" if ma50 and ma50 > 0 else "—",
                "vs MA200 %": f"{((latest/ma200)-1)*100:.1f}" if ma200 and ma200 > 0 else "—",
                "Sobre 200d": "✅" if (ma200 and latest > ma200) else "❌",
            })

        if momentum_rows:
            st.dataframe(pd.DataFrame(momentum_rows), use_container_width=True, hide_index=True)
        else:
            st.warning("Sin datos de precios. Ejecuta la actualización de datos.")

    # ── BTC vs BALANCE FED + CORRELACION RODANTE ──
    st.divider()
    st.subheader("BTC vs Balance Fed — Correlacion con Liquidez")
    st.caption("BTC actua como activo de liquidez marginal: sube cuando la Fed expande su balance y cae cuando lo contrae.")
    df_btc   = get_prices("BTC",  start=str(start_date))
    df_walcl = get_series("FED_BALANCE", start=str(start_date))
    if not df_btc.empty and not df_walcl.empty:
        df_btc2   = df_btc.set_index("date")["close"].rename("BTC")
        df_walcl2 = df_walcl.set_index("date")["value"].rename("WALCL")
        merged = pd.merge_asof(
            df_btc2.reset_index().sort_values("date"),
            df_walcl2.reset_index().sort_values("date"),
            on="date", direction="nearest"
        ).dropna().set_index("date")

        if len(merged) >= 30:
            # Correlacion rodante 90 dias
            merged["corr_90d"] = merged["BTC"].rolling(90).corr(merged["WALCL"])

            fig_btc = go.Figure()
            fig_btc.add_trace(go.Scatter(x=merged.index, y=merged["BTC"],
                                         name="BTC (USD)", yaxis="y1",
                                         line=dict(color="#f7931a", width=2)))
            fig_btc.add_trace(go.Scatter(x=merged.index, y=merged["WALCL"],
                                         name="Balance Fed (B$)", yaxis="y2",
                                         line=dict(color="#3498db", width=1.5, dash="dot")))
            fig_btc.update_layout(
                title="BTC vs Balance Fed (eje dual)",
                yaxis=dict(title="BTC (USD)", side="left", color="#f7931a"),
                yaxis2=dict(title="Balance Fed (B$)", side="right", overlaying="y", color="#3498db"),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                legend=dict(orientation="h"), height=350
            )
            st.plotly_chart(fig_btc, use_container_width=True)

            fig_corr = go.Figure()
            fig_corr.add_trace(go.Scatter(x=merged.index, y=merged["corr_90d"],
                                           name="Correlacion 90d", fill="tozeroy",
                                           line=dict(color="#9b59b6", width=2)))
            fig_corr.add_hline(y=0.6, line_dash="dash", line_color="#2ecc71",
                                annotation_text="Alta correlacion (0.6)")
            fig_corr.add_hline(y=0, line_color="#aaa")
            fig_corr.update_layout(
                title="Correlacion rodante 90 dias BTC vs Balance Fed",
                yaxis=dict(title="Correlacion", range=[-1, 1]),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=250
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            _corr_last = merged["corr_90d"].dropna().iloc[-1] if not merged["corr_90d"].dropna().empty else None
            if _corr_last is not None:
                _corr_txt = (f"Correlacion actual BTC-Fed ({_corr_last:.2f}): "
                             + ("ALTA — BTC funcionando como activo de liquidez, se mueve con el balance de la Fed."
                                if _corr_last > 0.6
                                else "MODERADA — BTC parcialmente desacoplado del ciclo de liquidez."
                                if _corr_last > 0.3
                                else "BAJA — BTC cotizando por factores propios (oferta/demanda cripto)."))
                st.info(_corr_txt)
    else:
        st.info("Sin datos BTC o Balance Fed. Ejecuta la actualizacion primero.")

    # ── SECTORES ──
    st.divider()
    st.subheader("Fuerza Relativa Sectorial (vs S&P 500)")
    sector_keys = ["XLK", "XLF", "XLE", "XLV", "XLU", "XLI", "XLC", "XLRE", "XLP", "XLY", "XLB"]
    sector_names = {
        "XLK": "Tech", "XLF": "Financiero", "XLE": "Energía", "XLV": "Healthcare",
        "XLU": "Utilities", "XLI": "Industriales", "XLC": "Comunicaciones",
        "XLRE": "Real Estate", "XLP": "Staples", "XLY": "Discrecional", "XLB": "Materiales"
    }

    spx_df = get_prices("SPX", start=str(start_date))
    rs_rows = []
    for key in sector_keys:
        sec_df = get_prices(key, start=str(start_date))
        if sec_df.empty or spx_df.empty:
            continue
        sec = sec_df.set_index("date")["close"]
        spx = spx_df.set_index("date")["close"]
        rs = (sec / spx).dropna()
        if len(rs) < 22:
            continue
        rs_1m = ((rs.iloc[-1] / rs.iloc[-22]) - 1) * 100
        rs_3m = ((rs.iloc[-1] / rs.iloc[-63]) - 1) * 100 if len(rs) > 63 else None
        rs_rows.append({
            "Sector": sector_names.get(key, key),
            "RS 1M %": round(rs_1m, 1),
            "RS 3M %": round(rs_3m, 1) if rs_3m else None,
        })

    if rs_rows:
        rs_df = pd.DataFrame(rs_rows).sort_values("RS 1M %", ascending=False)
        fig = px.bar(rs_df, x="Sector", y="RS 1M %", title="Fuerza Relativa 1M vs S&P 500",
                    color="RS 1M %", color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Actualiza los datos para ver la fuerza relativa sectorial.")

# ─────────────────────────────────────────────────────────────
# PÁGINA 3: MACRO & LIQUIDEZ
# ─────────────────────────────────────────────────────────────
elif "Macro" in page:
    st.title("Macro & Liquidez")

    def make_chart(df, title, hline=None, hline_label=None, color="#3498db", height=320):
        if df is None or df.empty:
            st.info("Sin datos — actualiza primero.")
            return
        fig = px.line(df, x="date", y="value", title=title)
        fig.update_traces(line_color=color)
        if hline is not None:
            fig.add_hline(y=hline, line_dash="dash", line_color="red",
                         annotation_text=hline_label or "")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                         height=height, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Liquidez & Balance Fed",
        "Curvas de Tipos",
        "Inflacion (CPI)",
        "Fed Funds & Tipos",
        "Empleo & Confianza",
    ])

    # ── TAB 1: LIQUIDEZ ──────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            make_chart(get_series("FED_BALANCE", start=str(start_date)),
                      "WALCL — Balance Fed (miles millones $)", color="#e74c3c")

        with col2:
            make_chart(get_series("ON_RRP", start=str(start_date)),
                      "ON RRP — Overnight Reverse Repos (miles millones $)", color="#9b59b6")

        col1, col2 = st.columns(2)
        with col1:
            make_chart(get_series("M2_US", start=str(start_date)),
                      "M2 USA (miles millones $)", color="#3498db")

        with col2:
            # BTC vs Balance Fed normalizado
            btc_df = get_prices("BTC", start=str(start_date))
            walcl_df = get_series("FED_BALANCE", start=str(start_date))
            if not btc_df.empty and not walcl_df.empty:
                fig = go.Figure()
                btc_s = btc_df.set_index("date")["close"]
                btc_s = (btc_s / btc_s.iloc[0]) * 100
                walcl_s = walcl_df.set_index("date")["value"]
                walcl_s = (walcl_s / walcl_s.iloc[0]) * 100
                fig.add_scatter(x=btc_s.index, y=btc_s.values,
                               name="BTC", line=dict(color="#f39c12"))
                fig.add_scatter(x=walcl_s.index, y=walcl_s.values,
                               name="WALCL (Balance Fed)", line=dict(color="#e74c3c", dash="dash"))
                fig.update_layout(title="BTC vs Balance Fed (base 100)",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos de BTC o Balance Fed.")

    # ── TAB 2: CURVAS DE TIPOS ────────────────────────────────
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            make_chart(get_series("CURVE_SPREAD_2Y10Y", start=str(start_date)),
                      "T10Y2Y — Spread 10Y minus 2Y (%)",
                      hline=0, hline_label="Inversion", color="#e67e22")

        with col2:
            t10y3m = get_series("T10Y3M", start=str(start_date))
            make_chart(t10y3m,
                      "T10Y3M — Spread 10Y minus 3M (%)",
                      hline=0, hline_label="Inversion", color="#e74c3c")

        col1, col2 = st.columns(2)
        with col1:
            # Superponer ambas curvas
            curve_2y = get_series("CURVE_SPREAD_2Y10Y", start=str(start_date))
            curve_3m = get_series("T10Y3M", start=str(start_date))
            if not curve_2y.empty and not curve_3m.empty:
                fig = go.Figure()
                fig.add_scatter(x=curve_2y["date"], y=curve_2y["value"],
                               name="10Y-2Y", line=dict(color="#e67e22"))
                fig.add_scatter(x=curve_3m["date"], y=curve_3m["value"],
                               name="10Y-3M", line=dict(color="#e74c3c", dash="dot"))
                fig.add_hline(y=0, line_dash="dash", line_color="white",
                             annotation_text="Inversion")
                fig.update_layout(title="Curvas de tipos superpuestas",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            make_chart(get_series("SPREAD_HY", start=str(start_date)),
                      "Spread High Yield EEUU (%) — estres credito",
                      hline=4, hline_label="Alerta", color="#c0392b")

    # ── TAB 3: INFLACION ──────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            cpi_yoy = get_series("CPI_YOY", start=str(start_date))
            core_yoy = get_series("CORE_CPI_YOY", start=str(start_date))
            if not cpi_yoy.empty:
                fig = go.Figure()
                fig.add_scatter(x=cpi_yoy["date"], y=cpi_yoy["value"],
                               name="CPI YoY %", line=dict(color="#e74c3c"))
                if not core_yoy.empty:
                    fig.add_scatter(x=core_yoy["date"], y=core_yoy["value"],
                                   name="Core CPI YoY %", line=dict(color="#f39c12", dash="dot"))
                fig.add_hline(y=2, line_dash="dash", line_color="green",
                             annotation_text="Objetivo Fed 2%")
                fig.update_layout(title="CPI vs Core CPI — Variacion anual (%)",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos de CPI. Actualiza primero.")

        with col2:
            make_chart(get_series("REAL_RATE_10Y", start=str(start_date)),
                      "Tipo real 10Y EEUU — TIPS (%)",
                      hline=0, hline_label="Tipos reales negativos", color="#27ae60")

        # Tabla resumen inflacion
        st.divider()
        st.subheader("Resumen inflacion actual")
        cpi_val, cpi_date = get_latest_value("CPI_YOY")
        core_val, core_date = get_latest_value("CORE_CPI_YOY")
        real_val, real_date = get_latest_value("REAL_RATE_10Y")
        hicp_df = get_series("HICP_EZ", start=str(start_date))
        hicp_val = hicp_df["value"].iloc[-1] if not hicp_df.empty else None

        cols = st.columns(4)
        cols[0].metric("CPI EEUU YoY", f"{cpi_val:.1f}%" if cpi_val else "N/D",
                      help=f"Dato: {cpi_date}")
        cols[1].metric("Core CPI EEUU", f"{core_val:.1f}%" if core_val else "N/D",
                      help=f"Dato: {core_date}")
        cols[2].metric("Tipos reales 10Y", f"{real_val:.2f}%" if real_val else "N/D",
                      help=f"Dato: {real_date}")
        cols[3].metric("HICP Eurozona", f"{hicp_val:.1f}" if hicp_val else "N/D",
                      help="Indice HICP (base 2015=100)")

    # ── TAB 4: FED FUNDS & TIPOS ──────────────────────────────
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            ff_df = get_series("FED_FUNDS", start=str(start_date))
            ecb_df = get_series("ECB_RATE", start=str(start_date))
            if not ff_df.empty:
                fig = go.Figure()
                fig.add_scatter(x=ff_df["date"], y=ff_df["value"],
                               name="Fed Funds Rate", line=dict(color="#3498db"))
                if not ecb_df.empty:
                    fig.add_scatter(x=ecb_df["date"], y=ecb_df["value"],
                                   name="Tipo BCE", line=dict(color="#2ecc71", dash="dot"))
                fig.update_layout(title="Fed Funds Rate vs Tipo BCE (%)",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos de Fed Funds.")

        with col2:
            col_a, col_b = st.columns(2)
            y2_df = get_series("YIELD_2Y", start=str(start_date))
            y10_df = get_series("YIELD_10Y", start=str(start_date))
            if not y2_df.empty and not y10_df.empty:
                fig = go.Figure()
                fig.add_scatter(x=y2_df["date"], y=y2_df["value"],
                               name="2Y", line=dict(color="#e74c3c"))
                fig.add_scatter(x=y10_df["date"], y=y10_df["value"],
                               name="10Y", line=dict(color="#3498db", dash="dot"))
                fig.update_layout(title="Bonos EEUU 2Y vs 10Y (%)",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)

        # Metricas clave actuales
        st.divider()
        st.subheader("Tipos actuales")
        ff_val, ff_date   = get_latest_value("FED_FUNDS")
        ecb_val, ecb_date = get_latest_value("ECB_RATE")
        y2_val, _         = get_latest_value("YIELD_2Y")
        y10_val, _        = get_latest_value("YIELD_10Y")
        curve_val, _      = get_latest_value("CURVE_SPREAD_2Y10Y")
        t10y3m_val, _     = get_latest_value("T10Y3M")

        cols = st.columns(6)
        cols[0].metric("Fed Funds", f"{ff_val:.2f}%" if ff_val else "N/D")
        cols[1].metric("Tipo BCE", f"{ecb_val:.2f}%" if ecb_val else "N/D")
        cols[2].metric("Bono 2Y", f"{y2_val:.2f}%" if y2_val else "N/D")
        cols[3].metric("Bono 10Y", f"{y10_val:.2f}%" if y10_val else "N/D")
        cols[4].metric("T10Y2Y", f"{curve_val:.2f}%" if curve_val else "N/D",
                      delta="Normal" if (curve_val or 0) > 0 else "Invertida",
                      delta_color="normal" if (curve_val or 0) > 0 else "inverse")
        cols[5].metric("T10Y3M", f"{t10y3m_val:.2f}%" if t10y3m_val else "N/D",
                      delta="Normal" if (t10y3m_val or 0) > 0 else "Invertida",
                      delta_color="normal" if (t10y3m_val or 0) > 0 else "inverse")

    # ── TAB 5: EMPLEO & CONFIANZA ─────────────────────────────
    with tab5:
        col1, col2 = st.columns(2)
        with col1:
            make_chart(get_series("UNEMPLOYMENT_US", start=str(start_date)),
                      "Tasa paro EEUU (%)", color="#e74c3c")
        with col2:
            make_chart(get_series("INITIAL_CLAIMS", start=str(start_date)),
                      "Initial Jobless Claims EEUU (miles)", color="#e67e22")

        col1, col2 = st.columns(2)
        with col1:
            make_chart(get_series("MICHIGAN_SENT", start=str(start_date)),
                      "Michigan Consumer Sentiment", color="#3498db")
        with col2:
            unemp_ez = get_series("UNEMPLOYMENT_EZ", start=str(start_date))
            unemp_es = get_series("UNEMPLOYMENT_ES", start=str(start_date))
            if not unemp_ez.empty:
                fig = go.Figure()
                fig.add_scatter(x=unemp_ez["date"], y=unemp_ez["value"],
                               name="Eurozona", line=dict(color="#3498db"))
                if not unemp_es.empty:
                    fig.add_scatter(x=unemp_es["date"], y=unemp_es["value"],
                                   name="España", line=dict(color="#e74c3c", dash="dot"))
                fig.update_layout(title="Tasa de paro Eurozona vs España (%)",
                                 paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                 height=320, margin=dict(t=40, b=20),
                                 legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos de paro europeo.")

# ─────────────────────────────────────────────────────────────
# PÁGINA 4: CICLO DE MERCADO (PUNTO 2)
# ─────────────────────────────────────────────────────────────
elif "Ciclo" in page:
    st.title("Ciclo de Mercado")
    st.caption("Basado en el modelo de ciclo económico (Fidelity Investment Clock)")

    # Construir inputs del ciclo con datos disponibles
    vix_val, _ = get_latest_value("VIX")
    curve, _ = get_latest_value("CURVE_SPREAD_2Y10Y")
    hy_spread, _ = get_latest_value("SPREAD_HY")

    cycle_inputs = {
        "pmi_composite": 51.5,
        "pmi_trend": "stable",
        "unemployment_change": -0.05,
        "gdp_growth": 1.8,
        "gdp_trend": "stable",
        "inflation_rate": 2.8,
        "inflation_trend": "falling",
        "curve_spread": curve or 0.3,
        "cb_stance": "neutral",
        "credit_spread_trend": "tightening" if (hy_spread or 5) < 4 else "widening",
        "leading_sector": "growth",
    }

    st.sidebar.divider()
    st.sidebar.subheader("Ajustar inputs del ciclo")
    cycle_inputs["pmi_composite"] = st.sidebar.slider("PMI Compuesto", 40.0, 60.0, 51.5, 0.5)
    cycle_inputs["pmi_trend"] = st.sidebar.selectbox("Tendencia PMI", ["rising", "stable", "falling"])
    cycle_inputs["inflation_rate"] = st.sidebar.slider("Inflación (%)", 0.0, 10.0, 2.8, 0.1)
    cycle_inputs["cb_stance"] = st.sidebar.selectbox("Política BC", ["expansive", "neutral", "restrictive"])
    cycle_inputs["gdp_growth"] = st.sidebar.slider("PIB Growth (%)", -3.0, 6.0, 1.8, 0.1)

    cycle = detect_cycle_phase(cycle_inputs)
    c = cycle.to_dict()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div style="background:{c['color']}22; border: 2px solid {c['color']};
                    border-radius: 10px; padding: 20px; text-align: center;">
            <h2 style="color:{c['color']}; margin:0">{c['phase']}</h2>
            <p style="color: #ccc; margin:8px 0 0">{c['description']}</p>
            <p style="font-size: 0.9rem; color: #aaa">Confianza: {c['confidence']:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.write("**Sectores favorecidos:**")
        for s in c["favored_sectors"]:
            st.success(f"✅ {s}")

        st.write("**Evitar / Infraponderar:**")
        for s in c["avoid_sectors"]:
            st.error(f"❌ {s}")

    with col2:
        st.write("**Sesgo de activos:**")
        st.info(c["asset_bias"])

        st.write("**Bitcoin:**")
        btc_color = "success" if "positivo" in c["bitcoin_signal"].lower() else \
                    ("error" if "negativo" in c["bitcoin_signal"].lower() else "info")
        getattr(st, btc_color)(f"₿ {c['bitcoin_signal']}")

        if c["signals_supporting"]:
            st.write("**Señales que soportan esta fase:**")
            for sig in c["signals_supporting"]:
                st.write(f"• {sig}")

        if c["signals_against"]:
            with st.expander("Señales contradictorias"):
                for sig in c["signals_against"]:
                    st.write(f"• {sig}")

    # Diagrama de ciclo visual
    st.divider()
    st.subheader("Las 4 Fases del Ciclo")
    phases_info = [
        ("EARLY RECOVERY", "#2ecc71", "Salida recesión\nBC expansivos\nCíclicas ↑"),
        ("MID EXPANSION",  "#3498db", "Crecimiento sólido\nBeneficios ↑\nTech & Momentum ↑"),
        ("LATE CYCLE",     "#f39c12", "Inflación alta\nBC restrictivos\nEnergía & Value ↑"),
        ("RECESSION",      "#e74c3c", "Contracción\nRisk-Off puro\nDefensivas & Bonos ↑"),
    ]
    cols = st.columns(4)
    for col, (phase_name, color, desc) in zip(cols, phases_info):
        is_current = c["phase"] == phase_name
        border = f"3px solid {color}" if is_current else f"1px solid {color}55"
        bg = f"{color}33" if is_current else f"{color}11"
        col.markdown(f"""
        <div style="background:{bg}; border:{border}; border-radius:8px;
                    padding:12px; text-align:center; min-height: 130px;">
            <b style="color:{color}">{phase_name}</b>
            {'<br><span style="font-size:1.2rem">◀ ACTUAL</span>' if is_current else ''}
            <br><small style="color:#ccc; white-space:pre-line">{desc}</small>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# PÁGINA 5: FUNDAMENTALES
# ─────────────────────────────────────────────────────────────
elif "Fundamentales" in page:
    import io as _io2, contextlib as _ctx2
    from financial_analyzer.fundamentals.scorer import score_ticker as _score_ticker, score_watchlist as _score_watchlist, WATCHLIST

    st.title("Análisis Fundamental de Empresas")

    # ── Conexión con régimen actual ──
    _rg2 = _regime_global
    _rg_color = {"RISK-ON": "#2ecc71", "NEUTRAL": "#f39c12", "RISK-OFF": "#e74c3c"}.get(_rg2["regime"], "#aaa")
    _rg_bg    = {"RISK-ON": "#1a4a2e", "NEUTRAL": "#4a3a1a", "RISK-OFF": "#4a1a1a"}.get(_rg2["regime"], "#222")
    st.markdown(
        f'<div style="background:{_rg_bg};border-left:4px solid {_rg_color};padding:10px 16px;'
        f'border-radius:6px;margin-bottom:16px">'
        f'<span style="color:{_rg_color};font-weight:bold">Régimen actual: {_rg2["regime"]} ({_rg2["total"]:.0f}/100)</span> — '
        f'<span style="color:#ccc;font-size:0.9rem">'
        f'{"En entornos Risk-On el sesgo es hacia empresas de crecimiento (Growth, Tech, alta beta). Prioriza scores altos en Crecimiento y Momentum." if _rg2["regime"]=="RISK-ON" else "En entornos Neutral busca calidad: FCF yield alto, deuda baja, dividendo. Equilibrio entre crecimiento y defensa." if _rg2["regime"]=="NEUTRAL" else "En entornos Risk-Off prioriza defensivas: Staples, Healthcare, Utilities con bajo D/E y FCF generoso. Evita alto apalancamiento."}'
        f'</span></div>',
        unsafe_allow_html=True
    )

    # ── Grupos de peers por sector ──
    PEER_GROUPS = {
        "US Mega-Cap Tech":     ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"],
        "US Defensivas":        ["JNJ", "PG", "KO"],
        "IBEX 35":              ["SAN.MC", "BBVA.MC", "TEF.MC", "IBE.MC", "ITX.MC", "REP.MC"],
        "EuroStoxx Select":     ["SAP.DE", "ASML.AS", "MC.PA", "SIE.DE"],
        "Personalizado":        [],
    }

    tab_single, tab_peers, tab_watchlist = st.tabs(["Empresa Individual", "Comparativa Peers", "Watchlist Completo"])

    # ── TAB 1: Empresa individual ──────────────────────────────
    with tab_single:
        col_inp, col_quick = st.columns([2, 3])
        with col_inp:
            custom_ticker = st.text_input("Ticker (ej: AAPL, SAN.MC, ASML.AS)", "AAPL")
        with col_quick:
            st.caption("Acceso rápido:")
            _qcols = st.columns(6)
            _quick = ["AAPL", "MSFT", "NVDA", "SAN.MC", "ASML.AS", "IBE.MC"]
            for _qi, _qt in enumerate(_quick):
                if _qcols[_qi].button(_qt, key=f"q_{_qt}"):
                    custom_ticker = _qt

        analyze_btn = st.button("Analizar", type="primary")

        if analyze_btn and custom_ticker:
            _tk = custom_ticker.strip().upper()
            with st.spinner(f"Descargando datos de {_tk}..."):
                _buf2 = _io2.StringIO()
                with _ctx2.redirect_stdout(_buf2), _ctx2.redirect_stderr(_buf2):
                    result = _score_ticker(_tk)
                d = result.to_dict()

            # ── Info de mercado actual (yfinance) ──
            try:
                import yfinance as _yf
                _info = _yf.Ticker(_tk).info or {}
                _price     = _info.get("currentPrice") or _info.get("regularMarketPrice")
                _prev      = _info.get("previousClose")
                _mktcap    = _info.get("marketCap")
                _sector    = _info.get("sector", "—")
                _industry  = _info.get("industry", "—")
                _name      = _info.get("longName") or _info.get("shortName") or _tk
                _fwd_pe    = _info.get("forwardPE")
                _ev_ebitda = _info.get("enterpriseToEbitda")
                _pct_chg   = ((_price / _prev) - 1) * 100 if _price and _prev else None
            except Exception:
                _price = _prev = _mktcap = _sector = _industry = _fwd_pe = _ev_ebitda = None
                _pct_chg = None
                _name = _tk

            grade_color = {"A": "#2ecc71", "B": "#3498db", "C": "#f39c12",
                           "D": "#e67e22", "F": "#e74c3c"}.get(d["grade"], "#fff")

            # ── Fila superior: badge + métricas de mercado ──
            c_badge, c_metrics = st.columns([1, 3])
            with c_badge:
                st.markdown(f"""
                <div style="text-align:center;padding:20px;border:2px solid {grade_color};
                            border-radius:10px;background:{grade_color}22">
                    <div style="color:{grade_color};font-size:2.5rem;font-weight:bold;margin:0">{d['grade']}</div>
                    <div style="color:{grade_color};font-size:1.4rem">{d['score_total']}/100</div>
                    <div style="color:#aaa;font-size:0.85rem;margin-top:4px">{_name}</div>
                    <div style="color:#888;font-size:0.75rem">{_sector}</div>
                </div>""", unsafe_allow_html=True)
            with c_metrics:
                _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                _mc1.metric("Precio",
                            f"${_price:.2f}" if _price else "N/D",
                            delta=f"{_pct_chg:+.2f}%" if _pct_chg is not None else None)
                _mc2.metric("Market Cap",
                            f"${_mktcap/1e9:.1f}B" if _mktcap else "N/D")
                _mc3.metric("P/E Forward",
                            f"{_fwd_pe:.1f}x" if _fwd_pe else "N/D",
                            help="<15 barato | 15-25 razonable | >30 caro")
                _mc4.metric("EV/EBITDA",
                            f"{_ev_ebitda:.1f}x" if _ev_ebitda else "N/D",
                            help="<10 barato | 10-16 razonable | >20 caro")

            st.divider()

            # ── Gráfico de barras horizontal (% del máximo, siempre positivo) ──
            c_chart, c_interp = st.columns([3, 2])
            with c_chart:
                _cats  = ["Rentabilidad\n(máx 25)", "Crecimiento\n(máx 20)",
                          "Balance\n(máx 20)", "Cash Flow\n(máx 15)", "Valoración\n(máx 20)"]
                _scores = [d["score_profit"], d["score_growth"], d["score_balance"],
                           d["score_cashflow"], d["score_valuation"]]
                _maxs   = [25, 20, 20, 15, 20]
                _pcts   = [s / m for s, m in zip(_scores, _maxs)]

                fig_fund = go.Figure()
                # Barra de fondo (máximo posible)
                fig_fund.add_trace(go.Bar(
                    y=_cats, x=_maxs, orientation="h",
                    marker_color="rgba(255,255,255,0.07)", name="Máximo",
                    showlegend=False
                ))
                # Barra obtenida con color por porcentaje
                _bar_colors = ["#2ecc71" if p > 0.6 else ("#f39c12" if p > 0.35 else "#e74c3c")
                               for p in _pcts]
                fig_fund.add_trace(go.Bar(
                    y=_cats, x=_scores, orientation="h",
                    marker_color=_bar_colors, name="Score",
                    text=[f"{s:.0f}/{m}  ({p*100:.0f}%)" for s, m, p in zip(_scores, _maxs, _pcts)],
                    textposition="outside", showlegend=False
                ))
                fig_fund.update_layout(
                    title=f"Desglose Fundamental — {_tk}",
                    barmode="overlay",
                    xaxis=dict(range=[0, max(_maxs) * 1.3], title="Puntos"),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=320,
                    margin=dict(t=40, b=20, r=20)
                )
                st.plotly_chart(fig_fund, use_container_width=True)

            with c_interp:
                st.markdown("**Interpretacion por categoria**")
                _cat_texts = {
                    "Rentabilidad":  {
                        "high": "ROE y margenes fuertes — empresa bien gestionada.",
                        "mid":  "Rentabilidad aceptable pero con margen de mejora.",
                        "low":  "Rentabilidad debil — vigila si los margenes se comprimen."
                    },
                    "Crecimiento":   {
                        "high": "Revenue y EPS creciendo rapido — motor de expansion activo.",
                        "mid":  "Crecimiento moderado. Empresa madura o en transicion.",
                        "low":  "Crecimiento estancado o negativo. Requiere atencion."
                    },
                    "Balance":       {
                        "high": "Balance solido: baja deuda, liquidez suficiente.",
                        "mid":  "Deuda manejable pero vigila el ratio de cobertura.",
                        "low":  "Apalancamiento elevado. Riesgo en entornos de tipos altos."
                    },
                    "Cash Flow":     {
                        "high": "FCF Yield alto — genera caja de verdad.",
                        "mid":  "FCF positivo pero limitado.",
                        "low":  "FCF insuficiente o no disponible. Vigilar burn rate."
                    },
                    "Valoracion":    {
                        "high": "Cotiza a multiples atractivos vs fundamentales.",
                        "mid":  "Valoracion razonable, sin descuento claro.",
                        "low":  "Multiples exigentes. El mercado ya descuenta mucho crecimiento."
                    },
                }
                _cat_keys = ["Rentabilidad", "Crecimiento", "Balance", "Cash Flow", "Valoracion"]
                for _ck, _pct in zip(_cat_keys, _pcts):
                    _tier = "high" if _pct > 0.6 else ("mid" if _pct > 0.35 else "low")
                    _icon = "✅" if _tier == "high" else ("⚠️" if _tier == "mid" else "🔴")
                    st.caption(f"{_icon} **{_ck}**: {_cat_texts[_ck][_tier]}")

            # ── Interpretación conectada al régimen ──
            _regime_name = _rg2["regime"]
            _grade = d["grade"]
            if _regime_name == "RISK-ON":
                _action = ("Empresa de calidad en entorno favorable. Candidato a sobreponderar." if _grade in ("A","B")
                           else "Score moderado en entorno Risk-On. Considera peers con mejor momentum.")
            elif _regime_name == "NEUTRAL":
                _action = ("Buena empresa para mantener en cartera equilibrada." if _grade in ("A","B")
                           else "En entorno neutral, prioriza empresas con score A o B.")
            else:
                _action = ("A pesar del entorno Risk-Off, fundamentales sólidos pueden proteger la cartera." if _grade in ("A","B")
                           else "Entorno Risk-Off + fundamentales debiles. Candidato a reducir exposición.")
            st.info(f"**Régimen {_regime_name} + {_tk} ({_grade} — {d['score_total']}/100):** {_action}")

            if d["data_quality"] != "ok":
                with st.expander("Notas de calidad de datos"):
                    for note in d["notes"]:
                        st.caption(f"• {note}")

    # ── TAB 2: Comparativa Peers ───────────────────────────────
    with tab_peers:
        _group_sel = st.selectbox("Grupo de peers", list(PEER_GROUPS.keys()))
        _peer_tickers = PEER_GROUPS[_group_sel]
        if _group_sel == "Personalizado":
            _custom_peers = st.text_input("Tickers separados por coma (ej: AAPL,MSFT,GOOGL)", "AAPL,MSFT,GOOGL")
            _peer_tickers = [t.strip().upper() for t in _custom_peers.split(",") if t.strip()]

        if st.button("Comparar peers", type="primary") and _peer_tickers:
            with st.spinner(f"Analizando {len(_peer_tickers)} empresas..."):
                _peer_rows = []
                for _pt in _peer_tickers:
                    _buf3 = _io2.StringIO()
                    with _ctx2.redirect_stdout(_buf3), _ctx2.redirect_stderr(_buf3):
                        _pr = _score_ticker(_pt)
                    _peer_rows.append(_pr.to_dict())
                _df_peers = pd.DataFrame(_peer_rows).sort_values("score_total", ascending=False)

            # Gráfico radar / barras comparativas
            _fig_comp = go.Figure()
            _comp_cats = ["Rentabilidad", "Crecimiento", "Balance", "Cash Flow", "Valoracion"]
            _comp_cols_map = ["score_profit", "score_growth", "score_balance", "score_cashflow", "score_valuation"]
            _comp_maxs     = [25, 20, 20, 15, 20]
            _colors_peers  = ["#3498db","#2ecc71","#e74c3c","#f39c12","#9b59b6","#1abc9c","#e67e22","#e91e63"]
            for _pi, _row in _df_peers.iterrows():
                _vals_pct = [_row[c] / m * 100 for c, m in zip(_comp_cols_map, _comp_maxs)]
                _fig_comp.add_trace(go.Bar(
                    name=_row["ticker"],
                    x=_comp_cats,
                    y=_vals_pct,
                    marker_color=_colors_peers[_pi % len(_colors_peers)],
                    text=[f"{v:.0f}%" for v in _vals_pct],
                    textposition="outside"
                ))
            _fig_comp.update_layout(
                title="Comparativa Fundamental (% del máximo por categoría)",
                barmode="group",
                yaxis=dict(title="% obtenido", range=[0, 130]),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=420,
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(_fig_comp, use_container_width=True)

            # Tabla resumen con ranking
            _df_display = _df_peers[["ticker","name","score_total","grade",
                                      "score_profit","score_growth","score_balance",
                                      "score_cashflow","score_valuation","data_quality"]].copy()
            _df_display.insert(0, "Rank", range(1, len(_df_display)+1))
            _df_display.columns = ["Rank","Ticker","Nombre","Score","Nota",
                                   "Rentab.","Crec.","Balance","CF","Valor.","Datos"]
            st.dataframe(_df_display, use_container_width=True, hide_index=True)

            # Mejor y peor de cada categoría
            st.markdown("**Mejor empresa por categoría:**")
            _best_cols = st.columns(5)
            for _bci, (_bcat, _bcol) in enumerate(zip(_comp_cats, _comp_cols_map)):
                _best_row = _df_peers.loc[_df_peers[_bcol].idxmax()]
                _best_cols[_bci].metric(_bcat, _best_row["ticker"],
                                        delta=f"{_best_row[_bcol]:.0f}pts")

    # ── TAB 3: Watchlist completo ──────────────────────────────
    with tab_watchlist:
        st.caption(f"Watchlist predefinido: {len(WATCHLIST)} empresas (IBEX, EuroStoxx, S&P 500 selección)")
        st.warning("El análisis completo descarga datos de yfinance para cada empresa. Puede tardar 1-2 minutos.")

        if st.button("Analizar watchlist completo", type="primary"):
            _progress = st.progress(0, text="Iniciando análisis...")
            _wl_rows = []
            _wl_items = list(WATCHLIST.items())
            for _wi, (_wt, _wn) in enumerate(_wl_items):
                _progress.progress((_wi + 1) / len(_wl_items), text=f"Analizando {_wt} ({_wi+1}/{len(_wl_items)})...")
                _buf4 = _io2.StringIO()
                with _ctx2.redirect_stdout(_buf4), _ctx2.redirect_stderr(_buf4):
                    _wr = _score_ticker(_wt, _wn)
                _wl_rows.append(_wr.to_dict())
            _progress.empty()

            _df_wl = pd.DataFrame(_wl_rows).sort_values("score_total", ascending=False).reset_index(drop=True)
            _df_wl.insert(0, "Rank", range(1, len(_df_wl)+1))

            # Heatmap visual del watchlist
            _fig_wl = px.bar(_df_wl, x="ticker", y="score_total", color="score_total",
                             color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
                             range_color=[0, 100], text="grade",
                             title=f"Watchlist — Fundamental Score (Régimen: {_rg2['regime']})")
            _fig_wl.update_traces(textposition="outside")
            _fig_wl.add_hline(y=60, line_dash="dash", line_color="white", opacity=0.4,
                               annotation_text="Umbral calidad (60)")
            _fig_wl.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                   height=400, xaxis_tickangle=-45)
            st.plotly_chart(_fig_wl, use_container_width=True)

            st.dataframe(
                _df_wl[["Rank","ticker","name","score_total","grade",
                         "score_profit","score_growth","score_balance","score_cashflow","score_valuation","data_quality"]],
                use_container_width=True, hide_index=True
            )

# ─────────────────────────────────────────────────────────────
# PÁGINA 6: PORTFOLIO
# ─────────────────────────────────────────────────────────────
elif "Portfolio" in page:
    import json, yfinance as _yf2

    _PORTFOLIO_FILE = Path(__file__).parent.parent / "data" / "portfolio.json"

    def _load_portfolio():
        if _PORTFOLIO_FILE.exists():
            try:
                return json.loads(_PORTFOLIO_FILE.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_portfolio(positions):
        _PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PORTFOLIO_FILE.write_text(json.dumps(positions, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fetch_price(ticker):
        try:
            _buf = _io.StringIO()
            with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
                info = _yf2.Ticker(ticker).info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            name  = info.get("shortName") or info.get("longName") or ticker
            prev  = info.get("previousClose")
            sector = info.get("sector", "—")
            return price, name, prev, sector
        except Exception:
            return None, ticker, None, "—"

    st.title("Portfolio — Seguimiento de Posiciones")

    # Régimen
    _rg3 = _regime_global
    _rg3_c = {"RISK-ON": "#2ecc71", "NEUTRAL": "#f39c12", "RISK-OFF": "#e74c3c"}.get(_rg3["regime"], "#aaa")
    st.markdown(
        f'<div style="background:#1a1a2e;border-left:4px solid {_rg3_c};padding:8px 16px;border-radius:6px;margin-bottom:12px">'
        f'<span style="color:{_rg3_c};font-weight:bold">Régimen: {_rg3["regime"]} ({_rg3["total"]:.0f}/100)</span>'
        f'</div>', unsafe_allow_html=True
    )

    positions = _load_portfolio()

    # ── Añadir posición ──
    with st.expander("Añadir / editar posición", expanded=len(positions) == 0):
        _ac1, _ac2, _ac3, _ac4 = st.columns(4)
        _new_tk    = _ac1.text_input("Ticker", placeholder="AAPL, SAN.MC, MSCI…")
        _new_shares= _ac2.number_input("Acciones / Participaciones", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
        _new_price = _ac3.number_input("Precio entrada (€/$)", min_value=0.0001, value=100.0, step=0.01)
        _new_curr  = _ac4.selectbox("Divisa entrada", ["USD", "EUR", "GBP"])
        _add_btn   = st.button("Añadir posición", type="primary")

        if _add_btn and _new_tk:
            _tk_clean = _new_tk.strip().upper()
            # Actualizar si ya existe, añadir si no
            _found = False
            for _pos in positions:
                if _pos["ticker"] == _tk_clean:
                    _pos["shares"] = _new_shares
                    _pos["entry_price"] = _new_price
                    _pos["currency"] = _new_curr
                    _found = True
                    break
            if not _found:
                positions.append({"ticker": _tk_clean, "shares": _new_shares,
                                   "entry_price": _new_price, "currency": _new_curr})
            _save_portfolio(positions)
            st.success(f"{_tk_clean} añadido/actualizado.")
            st.rerun()

    if not positions:
        st.info("Añade posiciones usando el panel de arriba para empezar a trackear tu portfolio.")
    else:
        # ── Enriquecer con precios actuales ──
        with st.spinner("Actualizando precios..."):
            _rows = []
            _total_cost = 0.0
            _total_value = 0.0
            for _pos in positions:
                _px, _nm, _prev, _sec = _fetch_price(_pos["ticker"])
                _cost  = _pos["shares"] * _pos["entry_price"]
                _value = _pos["shares"] * _px if _px else None
                _pnl   = (_value - _cost) if _value else None
                _pnl_pct = (_pnl / _cost * 100) if (_pnl is not None and _cost > 0) else None
                _day_chg = ((_px / _prev) - 1) * 100 if (_px and _prev) else None
                _total_cost  += _cost
                _total_value += (_value or _cost)
                _rows.append({
                    "ticker":   _pos["ticker"],
                    "name":     _nm,
                    "sector":   _sec,
                    "shares":   _pos["shares"],
                    "entry":    _pos["entry_price"],
                    "currency": _pos["currency"],
                    "price":    _px,
                    "cost":     _cost,
                    "value":    _value,
                    "pnl":      _pnl,
                    "pnl_pct":  _pnl_pct,
                    "day_chg":  _day_chg,
                })

        _total_pnl = _total_value - _total_cost
        _total_pnl_pct = (_total_pnl / _total_cost * 100) if _total_cost > 0 else 0

        # ── KPIs portfolio ──
        _k1, _k2, _k3, _k4 = st.columns(4)
        _k1.metric("Valor total", f"${_total_value:,.0f}",
                   delta=f"{_total_pnl:+,.0f} ({_total_pnl_pct:+.1f}%)",
                   delta_color="normal" if _total_pnl >= 0 else "inverse")
        _k2.metric("Coste total", f"${_total_cost:,.0f}")
        _k3.metric("P&L total", f"${_total_pnl:+,.0f}", delta=f"{_total_pnl_pct:+.1f}%",
                   delta_color="normal" if _total_pnl >= 0 else "inverse")
        _k4.metric("Posiciones", len(positions))

        st.divider()

        # ── Tabla de posiciones ──
        _df_port = pd.DataFrame(_rows)
        _df_port["Peso %"] = (_df_port["value"].fillna(_df_port["cost"]) / _total_value * 100).round(1)

        _display_cols = {
            "ticker": "Ticker", "name": "Empresa", "sector": "Sector",
            "shares": "Acciones", "entry": "Entrada", "price": "Precio actual",
            "value": "Valor", "pnl": "P&L", "pnl_pct": "P&L %",
            "day_chg": "Hoy %", "Peso %": "Peso %"
        }
        _df_show = _df_port[list(_display_cols.keys())].rename(columns=_display_cols)
        for _col in ["Entrada", "Precio actual", "Valor", "P&L"]:
            if _col in _df_show.columns:
                _df_show[_col] = _df_show[_col].apply(lambda x: f"${x:,.2f}" if x is not None and not pd.isna(x) else "N/D")
        for _col in ["P&L %", "Hoy %"]:
            if _col in _df_show.columns:
                _df_show[_col] = _df_show[_col].apply(lambda x: f"{x:+.2f}%" if x is not None and not pd.isna(x) else "N/D")
        _df_show["Acciones"] = _df_show["Acciones"].apply(lambda x: f"{x:.4f}" if x else "")

        st.dataframe(_df_show, use_container_width=True, hide_index=True)

        # ── Botón eliminar posición ──
        _del_tk = st.selectbox("Eliminar posición", ["—"] + [p["ticker"] for p in positions])
        if st.button("Eliminar", type="secondary") and _del_tk != "—":
            positions = [p for p in positions if p["ticker"] != _del_tk]
            _save_portfolio(positions)
            st.success(f"{_del_tk} eliminado.")
            st.rerun()

        st.divider()

        # ── Gráficos ──
        _gc1, _gc2 = st.columns(2)

        with _gc1:
            # Treemap de pesos
            _df_tree = _df_port[_df_port["value"].notna()].copy()
            if not _df_tree.empty:
                _fig_tree = px.treemap(
                    _df_tree, path=["sector", "ticker"], values="value",
                    color="pnl_pct", color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
                    color_continuous_midpoint=0,
                    title="Distribución portfolio por valor (color = P&L %)"
                )
                _fig_tree.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=380)
                st.plotly_chart(_fig_tree, use_container_width=True)

        with _gc2:
            # Barras P&L por posición
            _df_pnl = _df_port[_df_port["pnl_pct"].notna()].sort_values("pnl_pct")
            if not _df_pnl.empty:
                _fig_pnl = go.Figure(go.Bar(
                    x=_df_pnl["pnl_pct"], y=_df_pnl["ticker"], orientation="h",
                    marker_color=["#2ecc71" if v >= 0 else "#e74c3c" for v in _df_pnl["pnl_pct"]],
                    text=[f"{v:+.1f}%" for v in _df_pnl["pnl_pct"]], textposition="outside"
                ))
                _fig_pnl.update_layout(
                    title="P&L por posición (%)", xaxis=dict(title="%"),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=380
                )
                st.plotly_chart(_fig_pnl, use_container_width=True)

        # ── Evolución histórica del portfolio ──
        st.subheader("Evolución histórica del portfolio")
        st.caption("Precio de cierre diario × acciones en cartera desde la primera posición")
        with st.spinner("Cargando histórico..."):
            _hist_dfs = []
            for _pos in positions:
                try:
                    _buf = _io.StringIO()
                    with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
                        _h = _yf2.download(_pos["ticker"], start=str(start_date), progress=False, auto_adjust=True)
                    if not _h.empty:
                        _h = _h[["Close"]].rename(columns={"Close": _pos["ticker"]})
                        _h[_pos["ticker"]] *= _pos["shares"]
                        _hist_dfs.append(_h)
                except Exception:
                    pass

        if _hist_dfs:
            _df_hist = pd.concat(_hist_dfs, axis=1).fillna(method="ffill").dropna(how="all")
            _df_hist["Total"] = _df_hist.sum(axis=1)
            _fig_hist = go.Figure()
            _fig_hist.add_trace(go.Scatter(x=_df_hist.index, y=_df_hist["Total"],
                                            name="Portfolio total", fill="tozeroy",
                                            line=dict(color="#3498db", width=2)))
            _fig_hist.update_layout(
                yaxis=dict(title="Valor ($)"),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300
            )
            st.plotly_chart(_fig_hist, use_container_width=True)

        # ── Resumen contextual ──
        _winners = [r for r in _rows if r["pnl_pct"] and r["pnl_pct"] > 0]
        _losers  = [r for r in _rows if r["pnl_pct"] and r["pnl_pct"] < 0]
        _regime_advice = {
            "RISK-ON":  "Régimen Risk-On: considera aumentar exposición en posiciones de crecimiento ganadoras.",
            "NEUTRAL":  "Régimen Neutral: mantén posiciones sólidas, recorta las perdedoras con fundamentales débiles.",
            "RISK-OFF": "Régimen Risk-Off: evalúa reducir exposición en posiciones de alta beta. Prioriza defensivas y liquidez.",
        }.get(_rg3["regime"], "")
        st.info(f"**{len(_winners)} posiciones ganadoras / {len(_losers)} perdedoras.** {_regime_advice}")


# ─────────────────────────────────────────────────────────────
# PÁGINA 7: SCREENER / RESEARCH
# ─────────────────────────────────────────────────────────────
elif "Screener" in page:
    import yfinance as _yf3

    st.title("Screener / Research")
    st.caption("Busca acciones y ETFs por momentum, valoración y fundamentales. Universo ampliable.")

    # Universo de búsqueda
    _UNIVERSE = {
        # S&P 500 selección
        "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet",
        "META":"Meta","TSLA":"Tesla","BRK-B":"Berkshire","JPM":"JPMorgan","V":"Visa",
        "UNH":"UnitedHealth","XOM":"Exxon","JNJ":"J&J","PG":"P&G","KO":"Coca-Cola",
        "PEP":"PepsiCo","ABBV":"AbbVie","MRK":"Merck","CVX":"Chevron","HD":"Home Depot",
        "MA":"Mastercard","LLY":"Eli Lilly","AVGO":"Broadcom","CRM":"Salesforce","AMD":"AMD",
        "COST":"Costco","MCD":"McDonald's","NKE":"Nike","DIS":"Disney","NFLX":"Netflix",
        # IBEX 35
        "SAN.MC":"Santander","BBVA.MC":"BBVA","TEF.MC":"Telefonica","IBE.MC":"Iberdrola",
        "ITX.MC":"Inditex","REP.MC":"Repsol","AMS.MC":"Amadeus","FER.MC":"Ferrovial",
        "CABK.MC":"CaixaBank","ANA.MC":"Acciona",
        # EuroStoxx
        "SAP.DE":"SAP","ASML.AS":"ASML","MC.PA":"LVMH","SIE.DE":"Siemens",
        "NOVO-B.CO":"Novo Nordisk","TTE.PA":"TotalEnergies","AIR.PA":"Airbus",
        # ETFs clave
        "SPY":"S&P 500 ETF","QQQ":"Nasdaq ETF","EEM":"EM ETF","GLD":"Gold ETF",
        "TLT":"20Y Bond ETF","XLK":"Tech ETF","XLE":"Energy ETF","XLF":"Financial ETF",
        "XLV":"Healthcare ETF","XLU":"Utilities ETF",
    }

    # ── Filtros ──
    st.subheader("Filtros de búsqueda")
    _fc1, _fc2, _fc3 = st.columns(3)

    with _fc1:
        st.markdown("**Momentum**")
        _f_roc1m  = st.slider("ROC 1 mes mínimo (%)", -30, 30, 0)
        _f_roc3m  = st.slider("ROC 3 meses mínimo (%)", -50, 50, 0)
        _f_ma200  = st.checkbox("Solo sobre MA200", value=False)

    with _fc2:
        st.markdown("**Valoración (yfinance)**")
        _f_pe_max  = st.number_input("P/E Forward máximo (0 = sin límite)", 0.0, 200.0, 0.0, step=5.0)
        _f_ev_max  = st.number_input("EV/EBITDA máximo (0 = sin límite)",   0.0, 100.0, 0.0, step=2.0)

    with _fc3:
        st.markdown("**Universo**")
        _f_groups = st.multiselect("Mercados", ["S&P 500", "IBEX 35", "EuroStoxx", "ETFs"],
                                   default=["S&P 500"])
        _f_extra  = st.text_input("Tickers adicionales (coma)", "")

    # Construir universo filtrado por mercado
    _SP500_TK  = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V",
                  "UNH","XOM","JNJ","PG","KO","PEP","ABBV","MRK","CVX","HD",
                  "MA","LLY","AVGO","CRM","AMD","COST","MCD","NKE","DIS","NFLX"]
    _IBEX_TK   = ["SAN.MC","BBVA.MC","TEF.MC","IBE.MC","ITX.MC","REP.MC","AMS.MC","FER.MC","CABK.MC","ANA.MC"]
    _EURO_TK   = ["SAP.DE","ASML.AS","MC.PA","SIE.DE","NOVO-B.CO","TTE.PA","AIR.PA"]
    _ETF_TK    = ["SPY","QQQ","EEM","GLD","TLT","XLK","XLE","XLF","XLV","XLU"]

    _active_tickers = []
    if "S&P 500"  in _f_groups: _active_tickers += _SP500_TK
    if "IBEX 35"  in _f_groups: _active_tickers += _IBEX_TK
    if "EuroStoxx" in _f_groups: _active_tickers += _EURO_TK
    if "ETFs"     in _f_groups: _active_tickers += _ETF_TK
    if _f_extra:
        _active_tickers += [t.strip().upper() for t in _f_extra.split(",") if t.strip()]
    _active_tickers = list(dict.fromkeys(_active_tickers))  # deduplicar

    st.caption(f"Universo activo: {len(_active_tickers)} instrumentos")

    if st.button("Ejecutar screener", type="primary"):
        _prog = st.progress(0, text="Descargando datos del universo...")
        _results = []

        # Descarga precios en bloque (mucho más rápido)
        with st.spinner("Descargando precios históricos..."):
            _buf5 = _io.StringIO()
            with contextlib.redirect_stdout(_buf5), contextlib.redirect_stderr(_buf5):
                _raw = _yf3.download(
                    _active_tickers, period="1y", interval="1d",
                    progress=False, auto_adjust=True, group_by="ticker"
                )

        for _i, _tk in enumerate(_active_tickers):
            _prog.progress((_i + 1) / len(_active_tickers), text=f"Analizando {_tk}…")
            try:
                # Extraer serie de precios
                if len(_active_tickers) == 1:
                    _closes = _raw["Close"].dropna() if "Close" in _raw else pd.Series(dtype=float)
                else:
                    _closes = _raw[_tk]["Close"].dropna() if _tk in _raw.columns.get_level_values(0) else pd.Series(dtype=float)

                if len(_closes) < 30:
                    continue

                _price   = float(_closes.iloc[-1])
                _ma200   = float(_closes.rolling(200).mean().iloc[-1]) if len(_closes) >= 200 else None
                _ma50    = float(_closes.rolling(50).mean().iloc[-1]) if len(_closes) >= 50 else None
                _roc1m   = ((_price / float(_closes.iloc[-22])) - 1) * 100 if len(_closes) > 22 else None
                _roc3m   = ((_price / float(_closes.iloc[-63])) - 1) * 100 if len(_closes) > 63 else None
                _roc6m   = ((_price / float(_closes.iloc[-126])) - 1) * 100 if len(_closes) > 126 else None
                _vs_ma200 = ((_price / _ma200) - 1) * 100 if _ma200 else None
                _above_ma200 = (_price > _ma200) if _ma200 else None

                # Filtros de momentum
                if _roc1m is not None and _roc1m < _f_roc1m: continue
                if _roc3m is not None and _roc3m < _f_roc3m: continue
                if _f_ma200 and _above_ma200 is not True: continue

                # Info fundamental (solo si hay filtros de valoración)
                _fwd_pe = _ev_ebitda = _sector = _name = None
                if _f_pe_max > 0 or _f_ev_max > 0 or True:  # siempre fetchear nombre
                    try:
                        _info2 = _yf3.Ticker(_tk).info or {}
                        _fwd_pe   = _info2.get("forwardPE")
                        _ev_ebitda= _info2.get("enterpriseToEbitda")
                        _sector   = _info2.get("sector") or _info2.get("category", "ETF/Otro")
                        _name     = _info2.get("shortName") or _info2.get("longName") or _UNIVERSE.get(_tk, _tk)
                    except Exception:
                        _name = _UNIVERSE.get(_tk, _tk)

                # Filtros de valoración
                if _f_pe_max > 0 and _fwd_pe and _fwd_pe > _f_pe_max: continue
                if _f_ev_max > 0 and _ev_ebitda and _ev_ebitda > _f_ev_max: continue

                # Score combinado: momentum (60%) + valoración (40%)
                _mom_score = 0.0
                if _roc1m is not None: _mom_score += min(max(_roc1m / 20, -1), 1) * 20
                if _roc3m is not None: _mom_score += min(max(_roc3m / 30, -1), 1) * 20
                if _vs_ma200 is not None: _mom_score += min(max(_vs_ma200 / 15, -1), 1) * 20
                _mom_score = max(0, min(60, _mom_score + 30))  # normalizar 0-60

                _val_score = 30.0  # base neutral
                if _fwd_pe:
                    _val_score += (10 if _fwd_pe < 15 else (5 if _fwd_pe < 22 else (0 if _fwd_pe < 35 else -10)))
                if _ev_ebitda:
                    _val_score += (10 if _ev_ebitda < 10 else (5 if _ev_ebitda < 16 else 0))
                _val_score = max(0, min(40, _val_score))

                _combined = round(_mom_score + _val_score, 1)

                _results.append({
                    "Ticker":    _tk,
                    "Nombre":    _name or _UNIVERSE.get(_tk, _tk),
                    "Sector":    _sector or "—",
                    "Precio":    round(_price, 2),
                    "ROC 1M %":  round(_roc1m, 1) if _roc1m else None,
                    "ROC 3M %":  round(_roc3m, 1) if _roc3m else None,
                    "ROC 6M %":  round(_roc6m, 1) if _roc6m else None,
                    "vs MA200 %":round(_vs_ma200, 1) if _vs_ma200 else None,
                    "MA200":     "✅" if _above_ma200 else "❌",
                    "P/E Fwd":   round(_fwd_pe, 1) if _fwd_pe else None,
                    "EV/EBITDA": round(_ev_ebitda, 1) if _ev_ebitda else None,
                    "Score":     _combined,
                })
            except Exception:
                continue

        _prog.empty()

        if not _results:
            st.warning("Ningún instrumento cumple los filtros. Amplía los criterios.")
        else:
            _df_screen = pd.DataFrame(_results).sort_values("Score", ascending=False).reset_index(drop=True)
            _df_screen.insert(0, "Rank", range(1, len(_df_screen)+1))

            st.success(f"{len(_df_screen)} instrumentos encontrados")

            # ── Top 10 visual ──
            _top10 = _df_screen.head(10)
            _fig_screen = go.Figure(go.Bar(
                x=_top10["Score"], y=_top10["Ticker"], orientation="h",
                marker_color="#3498db",
                text=[f"{s:.0f}" for s in _top10["Score"]], textposition="outside"
            ))
            _fig_screen.update_layout(
                title=f"Top 10 — Score combinado (Momentum 60% + Valoración 40%) | Régimen: {_regime_global['regime']}",
                xaxis=dict(title="Score (0-100)"),
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=400,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(_fig_screen, use_container_width=True)

            # ── Scatter momentum vs valoración ──
            _df_scatter = _df_screen.dropna(subset=["ROC 3M %", "P/E Fwd"])
            if not _df_scatter.empty:
                _fig_sc = px.scatter(
                    _df_scatter, x="P/E Fwd", y="ROC 3M %", text="Ticker",
                    color="Score", color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
                    title="Momentum vs Valoración — zona ideal: izquierda-arriba (barato + fuerte)",
                    size_max=12
                )
                _fig_sc.update_traces(textposition="top center", marker=dict(size=10))
                _fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=420)
                _fig_sc.add_vline(x=25, line_dash="dash", line_color="#f39c12", opacity=0.5,
                                  annotation_text="P/E 25")
                _fig_sc.add_hline(y=0, line_color="white", opacity=0.3)
                st.plotly_chart(_fig_sc, use_container_width=True)

            # ── Tabla completa ──
            st.dataframe(_df_screen, use_container_width=True, hide_index=True)

            # Interpretación según régimen
            _rg_screen = _regime_global["regime"]
            _screen_interp = {
                "RISK-ON":  "En Risk-On prioriza los de mayor ROC 3M sobre su MA200. El momentum tiende a persistir.",
                "NEUTRAL":  "En Neutral busca el cuadrante ideal: valoración razonable (P/E <22) + momentum positivo.",
                "RISK-OFF": "En Risk-Off filtra por MA200=✅ y prioriza defensivas (XLU, XLV, KO, JNJ). Evita alta beta.",
            }.get(_rg_screen, "")
            if _screen_interp:
                st.info(f"**Consejo de régimen ({_rg_screen}):** {_screen_interp}")


# ─────────────────────────────────────────────────────────────
# PÁGINA 6: CONDICIONES FINANCIERAS
# ─────────────────────────────────────────────────────────────
elif "Condiciones" in page:
    st.title("Condiciones Financieras")
    st.caption("Indices sinteticos de estres financiero + señales de liquidez interbancaria")

    def chart(df, title, color="#3498db", hline=None, hlabel=None, height=300, shade_rec=True):
        if df is None or df.empty:
            st.info("Sin datos.")
            return None
        fig = go.Figure()
        # Sombreado recesiones
        if shade_rec:
            rec_df = get_series("USREC", start=str(start_date))
            if not rec_df.empty:
                rec_df["date"] = pd.to_datetime(rec_df["date"])
                in_rec = False
                rec_start = None
                for _, row in rec_df.iterrows():
                    if row["value"] == 1 and not in_rec:
                        in_rec = True
                        rec_start = row["date"]
                    elif row["value"] == 0 and in_rec:
                        in_rec = False
                        fig.add_vrect(x0=rec_start, x1=row["date"],
                                     fillcolor="red", opacity=0.08, layer="below", line_width=0)
                if in_rec and rec_start:
                    fig.add_vrect(x0=rec_start, x1=df["date"].max(),
                                 fillcolor="red", opacity=0.08, layer="below", line_width=0)
        fig.add_scatter(x=df["date"], y=df["value"], mode="lines",
                       name=title, line=dict(color=color, width=1.5))
        if hline is not None:
            fig.add_hline(y=hline, line_dash="dash", line_color="red",
                         annotation_text=hlabel or "")
        fig.update_layout(title=title, paper_bgcolor="rgba(0,0,0,0)",
                         font_color="white", height=height,
                         margin=dict(t=40, b=20), showlegend=False)
        return fig

    # ── Métricas clave actuales ──
    nfci_val, nfci_date   = get_latest_value("NFCI")
    stlfsi_val, _         = get_latest_value("STLFSI")
    vix_val, _            = get_latest_value("VIX")
    hy_val, _             = get_latest_value("SPREAD_HY")
    sofr_val, _           = get_latest_value("SOFR")
    onrrp_val, _          = get_latest_value("ON_RRP")

    st.subheader("Indicadores clave de estres financiero")
    cols = st.columns(6)

    def stress_color(val, low, high):
        if val is None: return None
        return "inverse" if val > high else ("normal" if val < low else "off")

    cols[0].metric("NFCI", f"{nfci_val:.3f}" if nfci_val else "N/D",
                  help="<0 = condiciones laxas | >0 = estres | >1 = estres severo")
    cols[1].metric("STLFSI", f"{stlfsi_val:.3f}" if stlfsi_val else "N/D",
                  help="<0 = normal | >0 = estres financiero")
    cols[2].metric("VIX", f"{vix_val:.1f}" if vix_val else "N/D",
                  help="<18 calma | 18-25 alerta | >25 miedo | >35 panico")
    cols[3].metric("Spread HY", f"{hy_val:.2f}%" if hy_val else "N/D",
                  help="<3% = apetito riesgo | >5% = estres crediticio")
    cols[4].metric("SOFR", f"{sofr_val:.3f}%" if sofr_val else "N/D",
                  help="Tipo interbancario overnight (sustituto LIBOR)")
    cols[5].metric("ON RRP", f"${onrrp_val:,.0f}B" if onrrp_val else "N/D",
                  help="Dinero aparcado en la Fed — alta = exceso liquidez")

    # ── Semaforo de estres ──
    stress_score = 0
    signals = []
    if nfci_val is not None:
        if nfci_val > 0.5:   stress_score += 3; signals.append(f"NFCI elevado ({nfci_val:.2f})")
        elif nfci_val > 0:   stress_score += 1; signals.append(f"NFCI ligeramente positivo ({nfci_val:.2f})")
    if stlfsi_val is not None and stlfsi_val > 0:
        stress_score += 2; signals.append(f"STLFSI en zona de estres ({stlfsi_val:.2f})")
    if vix_val is not None:
        if vix_val > 30:     stress_score += 3; signals.append(f"VIX en zona de panico ({vix_val:.0f})")
        elif vix_val > 20:   stress_score += 1; signals.append(f"VIX elevado ({vix_val:.0f})")
    if hy_val is not None and hy_val > 5:
        stress_score += 2; signals.append(f"Spread HY en zona de alerta ({hy_val:.1f}%)")

    stress_label = "BAJO" if stress_score <= 1 else ("MODERADO" if stress_score <= 4 else "ALTO")
    stress_color_map = {"BAJO": "#2ecc71", "MODERADO": "#f39c12", "ALTO": "#e74c3c"}
    sc = stress_color_map[stress_label]
    st.markdown(f"""
    <div style="background:{sc}22; border:2px solid {sc}; border-radius:8px;
                padding:12px 20px; margin:12px 0; display:flex; align-items:center; gap:16px">
        <span style="font-size:1.4rem; font-weight:bold; color:{sc}">
            Nivel de estres financiero: {stress_label}
        </span>
        <span style="color:#ccc; font-size:0.9rem">{" | ".join(signals) if signals else "Sin señales de estres detectadas"}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Graficos ──
    tab1, tab2, tab3 = st.tabs(["Indices de Estres", "Liquidez Interbancaria", "Credito & Volatilidad"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart(get_series("NFCI", start=str(start_date)),
                       "NFCI — Chicago Fed Financial Conditions Index",
                       color="#e74c3c", hline=0, hlabel="Zona estres")
            if fig: st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = chart(get_series("STLFSI", start=str(start_date)),
                       "STLFSI — St. Louis Fed Financial Stress Index",
                       color="#e67e22", hline=0, hlabel="Zona estres")
            if fig: st.plotly_chart(fig, use_container_width=True)

        # Superponer NFCI + VIX normalizado
        nfci_df = get_series("NFCI", start=str(start_date))
        vix_df  = get_series("VIX", start=str(start_date))
        if not nfci_df.empty and not vix_df.empty:
            fig = go.Figure()
            fig.add_scatter(x=nfci_df["date"], y=nfci_df["value"],
                           name="NFCI", line=dict(color="#e74c3c"))
            vix_norm = vix_df.set_index("date")["value"]
            vix_scaled = (vix_norm - vix_norm.mean()) / vix_norm.std()
            fig.add_scatter(x=vix_df["date"], y=vix_scaled.values,
                           name="VIX (normalizado)", line=dict(color="#9b59b6", dash="dot"),
                           yaxis="y2")
            fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
            fig.update_layout(
                title="NFCI vs VIX (normalizado) — correlacion de estres",
                paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=320,
                margin=dict(t=40, b=20), legend=dict(orientation="h"),
                yaxis2=dict(overlaying="y", side="right", showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart(get_series("SOFR", start=str(start_date)),
                       "SOFR — Tipo interbancario overnight (%)",
                       color="#3498db", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = chart(get_series("ON_RRP", start=str(start_date)),
                       "ON RRP — Exceso liquidez aparcado en Fed (miles millones $)",
                       color="#9b59b6", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = chart(get_series("FED_BALANCE", start=str(start_date)),
                       "WALCL — Balance Fed (miles millones $)",
                       color="#e74c3c", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart(get_series("M2_US", start=str(start_date)),
                       "M2 USA — Masa monetaria (miles millones $)",
                       color="#27ae60", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart(get_series("SPREAD_HY", start=str(start_date)),
                       "Spread High Yield — estres crediticio (%)",
                       color="#e74c3c", hline=5, hlabel="Alerta", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart(get_series("SPREAD_IG", start=str(start_date)),
                       "Spread Investment Grade (%)",
                       color="#e67e22", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = chart(get_series("VIX", start=str(start_date)),
                       "VIX — Indice de volatilidad implícita",
                       color="#9b59b6", hline=25, hlabel="Alerta", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart(get_series("TED_SPREAD", start=str(start_date)),
                       "TED Spread — liquidez interbancaria (%)",
                       color="#f39c12", hline=0.5, hlabel="Alerta", shade_rec=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# PÁGINA 7: INDICADORES ADELANTADOS
# ─────────────────────────────────────────────────────────────
elif "Adelantados" in page:
    st.title("Indicadores Adelantados")
    st.caption("Variables que anticipan la direccion de la economia 3-6 meses antes que el PIB")

    def chart_rec(df, title, color="#3498db", hline=None, hlabel=None, yoy=False, height=300):
        if df is None or df.empty:
            st.info("Sin datos.")
            return None
        df = df.copy()
        if yoy:
            df["value"] = df["value"].pct_change(12) * 100
            df = df.dropna()
            title += " (var. anual %)"
        fig = go.Figure()
        rec_df = get_series("USREC", start=str(start_date))
        if not rec_df.empty:
            rec_df["date"] = pd.to_datetime(rec_df["date"])
            in_rec = False; rec_start = None
            for _, row in rec_df.iterrows():
                if row["value"] == 1 and not in_rec:
                    in_rec = True; rec_start = row["date"]
                elif row["value"] == 0 and in_rec:
                    in_rec = False
                    fig.add_vrect(x0=rec_start, x1=row["date"],
                                 fillcolor="red", opacity=0.08, layer="below", line_width=0)
        fig.add_scatter(x=df["date"], y=df["value"], mode="lines",
                       line=dict(color=color, width=1.5), name=title)
        if hline is not None:
            fig.add_hline(y=hline, line_dash="dash", line_color="red",
                         annotation_text=hlabel or "")
        fig.update_layout(title=title, paper_bgcolor="rgba(0,0,0,0)",
                         font_color="white", height=height,
                         margin=dict(t=40, b=20), showlegend=False)
        return fig

    # ── Resumen estado actual ──
    retail_df   = get_series("RETAIL_SALES", start=str(start_date))
    indpro_df   = get_series("INDPRO", start=str(start_date))
    permit_df   = get_series("PERMIT", start=str(start_date))
    claims_df   = get_series("INITIAL_CLAIMS", start=str(start_date))
    cclaims_df  = get_series("CONT_CLAIMS", start=str(start_date))
    caputil_df  = get_series("CAPACITY_UTIL", start=str(start_date))

    def latest_yoy(df):
        if df is None or len(df) < 13: return None, None
        df = df.sort_values("date")
        now = df["value"].iloc[-1]
        ago = df["value"].iloc[-13]
        return round((now/ago - 1)*100, 1) if ago else None, str(df["date"].iloc[-1])[:10]

    r_yoy, r_date = latest_yoy(retail_df)
    i_yoy, i_date = latest_yoy(indpro_df)
    p_yoy, p_date = latest_yoy(permit_df)
    claims_val, claims_date = get_latest_value("INITIAL_CLAIMS")
    cclaims_val, _ = get_latest_value("CONT_CLAIMS")
    cap_val, _     = get_latest_value("CAPACITY_UTIL")

    st.subheader("Estado actual de los indicadores")
    cols = st.columns(6)
    cols[0].metric("Retail Sales YoY", f"{r_yoy:+.1f}%" if r_yoy else "N/D",
                  help=f"Dato: {r_date}")
    cols[1].metric("Prod. Industrial YoY", f"{i_yoy:+.1f}%" if i_yoy else "N/D",
                  help=f"Dato: {i_date}")
    cols[2].metric("Building Permits YoY", f"{p_yoy:+.1f}%" if p_yoy else "N/D",
                  help=f"Dato: {p_date}")
    cols[3].metric("Initial Claims", f"{claims_val:,.0f}K" if claims_val else "N/D",
                  help="Solicitudes desempleo semanales")
    cols[4].metric("Continuing Claims", f"{cclaims_val:,.0f}K" if cclaims_val else "N/D",
                  help="Desempleados que siguen cobrando prestacion")
    cols[5].metric("Capacidad Industrial", f"{cap_val:.1f}%" if cap_val else "N/D",
                  help=">80% = economia cerca de plena capacidad")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Consumo & Produccion", "Mercado Laboral", "Inmobiliario & Capacidad", "Main Street — Salud Financiera"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart_rec(retail_df, "Retail Sales EEUU", color="#2ecc71", yoy=True)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart_rec(indpro_df, "Produccion Industrial EEUU", color="#3498db", yoy=True)
            if fig: st.plotly_chart(fig, use_container_width=True)

        # PCE vs CPI vs Core PCE
        pce_yoy  = get_series("PCE_YOY",      start=str(start_date))
        cpce_yoy = get_series("CORE_PCE_YOY", start=str(start_date))
        cpi_yoy  = get_series("CPI_YOY",      start=str(start_date))
        if not pce_yoy.empty:
            fig = go.Figure()
            fig.add_scatter(x=cpi_yoy["date"], y=cpi_yoy["value"],
                           name="CPI YoY", line=dict(color="#e74c3c"))
            fig.add_scatter(x=pce_yoy["date"], y=pce_yoy["value"],
                           name="PCE YoY", line=dict(color="#f39c12", dash="dot"))
            fig.add_scatter(x=cpce_yoy["date"], y=cpce_yoy["value"],
                           name="Core PCE YoY", line=dict(color="#3498db", dash="dash"))
            fig.add_hline(y=2, line_dash="dash", line_color="green",
                         annotation_text="Objetivo Fed 2%")
            rec_df = get_series("USREC", start=str(start_date))
            if not rec_df.empty:
                in_rec = False; rec_start = None
                for _, row in rec_df.iterrows():
                    if row["value"] == 1 and not in_rec:
                        in_rec = True; rec_start = row["date"]
                    elif row["value"] == 0 and in_rec:
                        in_rec = False
                        fig.add_vrect(x0=rec_start, x1=row["date"],
                                     fillcolor="red", opacity=0.08, layer="below", line_width=0)
            fig.update_layout(title="CPI vs PCE vs Core PCE — Inflacion preferida de la Fed",
                             paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                             height=320, margin=dict(t=40, b=20),
                             legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart_rec(get_series("INITIAL_CLAIMS", start=str(start_date)),
                           "Initial Jobless Claims (miles)", color="#e74c3c")
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart_rec(get_series("CONT_CLAIMS", start=str(start_date)),
                           "Continuing Claims (miles)", color="#e67e22")
            if fig: st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = chart_rec(get_series("UNEMPLOYMENT_US", start=str(start_date)),
                           "Tasa paro EEUU (%)", color="#c0392b")
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart_rec(get_series("JOLTS", start=str(start_date)),
                           "JOLTS — Job Openings (miles)", color="#27ae60")
            if fig: st.plotly_chart(fig, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            fig = chart_rec(get_series("PERMIT", start=str(start_date)),
                           "Building Permits (miles, anualizado)", color="#3498db", yoy=True)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = chart_rec(get_series("CAPACITY_UTIL", start=str(start_date)),
                           "Utilizacion Capacidad Industrial (%)", color="#9b59b6",
                           hline=80, hlabel="Plena capacidad")
            if fig: st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Main Street — Salud Financiera del Ciudadano")
        st.caption("Indicadores de estres financiero de los hogares: impagos, deuda, ahorro y tipo hipotecario.")

        # ── KPIs actuales ──
        _mort_val, _    = get_latest_value("MORT_DELINQ")
        _cc_val, _      = get_latest_value("CC_DELINQ")
        _auto_val, _    = get_latest_value("AUTO_DELINQ")
        _save_val, _    = get_latest_value("SAVING_RATE")
        _debt_svc_val,_ = get_latest_value("DEBT_SERVICE")
        _mort_rate_val,_= get_latest_value("MORTGAGE_RATE")
        _cc_debt_val, _ = get_latest_value("CC_DEBT")
        _tot_credit_val,_=get_latest_value("CONSUMER_CREDIT")

        _ms_cols = st.columns(4)
        _ms_cols[0].metric("Impagos hipotecas",
                           f"{_mort_val:.2f}%" if _mort_val else "N/D",
                           help="<2% normal | >4% estres | >6% crisis (2008: ~11%)")
        _ms_cols[1].metric("Impagos tarjetas",
                           f"{_cc_val:.2f}%" if _cc_val else "N/D",
                           help="<3% normal | >5% alerta — la Fed lo vigila de cerca")
        _ms_cols[2].metric("Impagos auto",
                           f"{_auto_val:.2f}%" if _auto_val else "N/D",
                           help="<2% normal | >3% estres en consumidor medio")
        _ms_cols[3].metric("Tasa de ahorro",
                           f"{_save_val:.1f}%" if _save_val else "N/D",
                           help="<3% familia vive al dia | >8% colchon amplio")

        _ms_cols2 = st.columns(4)
        _ms_cols2[0].metric("Servicio deuda hogares",
                            f"{_debt_svc_val:.1f}%" if _debt_svc_val else "N/D",
                            help="% renta disponible destinada a pagar deudas. >14% = sobreendeudamiento")
        _ms_cols2[1].metric("Tipo hipotecario 30A",
                            f"{_mort_rate_val:.2f}%" if _mort_rate_val else "N/D",
                            help="Tipo fijo 30 años EEUU — impacta directamente en accesibilidad vivienda")
        _ms_cols2[2].metric("Deuda tarjetas",
                            f"${_cc_debt_val:,.0f}B" if _cc_debt_val else "N/D",
                            help="Total deuda revolving en circulacion (miles millones $)")
        _ms_cols2[3].metric("Credito total consumidor",
                            f"${_tot_credit_val:,.0f}B" if _tot_credit_val else "N/D",
                            help="Suma de todo el credito al consumo (tarjetas + auto + personal)")

        # ── Semaforo de estres del ciudadano ──
        _ms_stress = 0
        _ms_signals = []
        if _mort_val and _mort_val > 4:   _ms_stress += 3; _ms_signals.append(f"Impagos hipotecas elevados ({_mort_val:.1f}%)")
        elif _mort_val and _mort_val > 2.5: _ms_stress += 1; _ms_signals.append(f"Impagos hipotecas al alza ({_mort_val:.1f}%)")
        if _cc_val and _cc_val > 5:       _ms_stress += 3; _ms_signals.append(f"Impagos tarjetas en zona de alerta ({_cc_val:.1f}%)")
        elif _cc_val and _cc_val > 3:     _ms_stress += 1; _ms_signals.append(f"Impagos tarjetas subiendo ({_cc_val:.1f}%)")
        if _auto_val and _auto_val > 3:   _ms_stress += 2; _ms_signals.append(f"Impagos auto elevados ({_auto_val:.1f}%)")
        if _save_val and _save_val < 3:   _ms_stress += 2; _ms_signals.append(f"Tasa ahorro muy baja ({_save_val:.1f}%) — familias sin colchon")
        if _debt_svc_val and _debt_svc_val > 14: _ms_stress += 2; _ms_signals.append(f"Carga deuda hogares alta ({_debt_svc_val:.1f}% renta)")

        _ms_label = "BAJO" if _ms_stress <= 1 else ("MODERADO" if _ms_stress <= 4 else "ALTO")
        _ms_color = {"BAJO": "#2ecc71", "MODERADO": "#f39c12", "ALTO": "#e74c3c"}[_ms_label]
        st.markdown(
            f'<div style="background:{_ms_color}22;border:2px solid {_ms_color};border-radius:8px;'
            f'padding:12px 20px;margin:12px 0">'
            f'<span style="color:{_ms_color};font-size:1.3rem;font-weight:bold">Estres financiero ciudadano: {_ms_label}</span><br>'
            f'<span style="color:#ccc;font-size:0.9rem">'
            f'{" | ".join(_ms_signals) if _ms_signals else "Sin señales de estres relevantes en los hogares."}'
            f'</span></div>',
            unsafe_allow_html=True
        )

        st.divider()

        # ── Graficos ──
        _mg1, _mg2 = st.columns(2)

        with _mg1:
            # Impagos superpuestos: hipotecas, tarjetas, auto
            _mort_df  = get_series("MORT_DELINQ",  start=str(start_date))
            _cc_df    = get_series("CC_DELINQ",    start=str(start_date))
            _auto_df  = get_series("AUTO_DELINQ",  start=str(start_date))
            if not _mort_df.empty or not _cc_df.empty:
                _fig_delinq = go.Figure()
                if not _mort_df.empty:
                    _fig_delinq.add_scatter(x=_mort_df["date"], y=_mort_df["value"],
                                            name="Hipotecas", line=dict(color="#e74c3c", width=2))
                if not _cc_df.empty:
                    _fig_delinq.add_scatter(x=_cc_df["date"], y=_cc_df["value"],
                                            name="Tarjetas", line=dict(color="#f39c12", width=2))
                if not _auto_df.empty:
                    _fig_delinq.add_scatter(x=_auto_df["date"], y=_auto_df["value"],
                                            name="Auto", line=dict(color="#9b59b6", width=2))
                # Sombreado recesiones
                _rec_ms = get_series("USREC", start=str(start_date))
                if not _rec_ms.empty:
                    _rec_ms["date"] = pd.to_datetime(_rec_ms["date"])
                    _in_r = False; _rs = None
                    for _, _row in _rec_ms.iterrows():
                        if _row["value"] == 1 and not _in_r: _in_r = True; _rs = _row["date"]
                        elif _row["value"] == 0 and _in_r:
                            _in_r = False
                            _fig_delinq.add_vrect(x0=_rs, x1=_row["date"],
                                                  fillcolor="red", opacity=0.08, layer="below", line_width=0)
                _fig_delinq.add_hline(y=3, line_dash="dash", line_color="#e74c3c", opacity=0.5,
                                      annotation_text="Umbral alerta (3%)")
                _fig_delinq.update_layout(
                    title="Tasas de impago — hipotecas, tarjetas y auto (%)",
                    yaxis=dict(title="% de prestamos en mora"),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=350,
                    legend=dict(orientation="h"), margin=dict(t=40, b=20)
                )
                st.plotly_chart(_fig_delinq, use_container_width=True)
                st.caption("Los impagos suelen subir 6-12 meses DESPUÉS de que el mercado laboral se deteriora — son un indicador retrasado pero definitivo de recesion del consumidor.")
            else:
                st.info("Actualiza los datos para ver las tasas de impago.")

        with _mg2:
            # Tasa de ahorro
            _save_df = get_series("SAVING_RATE", start=str(start_date))
            fig_save = chart_rec(_save_df, "Tasa de Ahorro Personal EEUU (%)",
                                 color="#2ecc71", hline=5, hlabel="Umbral minimo saludable")
            if fig_save:
                st.plotly_chart(fig_save, use_container_width=True)
            st.caption("Una tasa de ahorro baja indica que el consumidor gasta mas de lo que ingresa, a menudo financiado con deuda. Suele caer antes de una recesion de consumo.")

        _mg3, _mg4 = st.columns(2)

        with _mg3:
            # Deuda tarjetas y credito total (eje dual)
            _cc_debt_df   = get_series("CC_DEBT",         start=str(start_date))
            _tot_cred_df  = get_series("CONSUMER_CREDIT", start=str(start_date))
            if not _cc_debt_df.empty:
                _fig_debt = go.Figure()
                _fig_debt.add_scatter(x=_cc_debt_df["date"], y=_cc_debt_df["value"],
                                      name="Deuda tarjetas (B$)", fill="tozeroy",
                                      line=dict(color="#f39c12", width=2))
                if not _tot_cred_df.empty:
                    _fig_debt.add_scatter(x=_tot_cred_df["date"], y=_tot_cred_df["value"],
                                          name="Credito total consumidor (B$)", yaxis="y2",
                                          line=dict(color="#3498db", width=1.5, dash="dot"))
                _fig_debt.update_layout(
                    title="Deuda de tarjetas vs Credito total consumidor (miles millones $)",
                    yaxis=dict(title="Deuda tarjetas (B$)", color="#f39c12"),
                    yaxis2=dict(title="Credito total (B$)", overlaying="y", side="right", color="#3498db"),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=320,
                    legend=dict(orientation="h"), margin=dict(t=40, b=20)
                )
                st.plotly_chart(_fig_debt, use_container_width=True)
                st.caption("Record historico de deuda en tarjetas = consumidores financiando el dia a dia con credito caro (18-24% TAE). Señal de tension aunque el empleo aguante.")
            else:
                st.info("Actualiza los datos para ver la evolucion de la deuda.")

        with _mg4:
            # Servicio de deuda + tipo hipotecario
            _dsvc_df  = get_series("DEBT_SERVICE",  start=str(start_date))
            _mrate_df = get_series("MORTGAGE_RATE", start=str(start_date))
            if not _dsvc_df.empty:
                _fig_svc = go.Figure()
                _fig_svc.add_scatter(x=_dsvc_df["date"], y=_dsvc_df["value"],
                                     name="Servicio deuda (% renta)", fill="tozeroy",
                                     line=dict(color="#e74c3c", width=2))
                if not _mrate_df.empty:
                    _fig_svc.add_scatter(x=_mrate_df["date"], y=_mrate_df["value"],
                                         name="Tipo hipotecario 30A (%)", yaxis="y2",
                                         line=dict(color="#9b59b6", width=1.5, dash="dot"))
                _fig_svc.add_hline(y=14, line_dash="dash", line_color="#e74c3c", opacity=0.5,
                                   annotation_text="Sobreendeudamiento (14%)")
                _fig_svc.update_layout(
                    title="Carga de deuda hogares vs Tipo hipotecario",
                    yaxis=dict(title="% renta disponible", color="#e74c3c"),
                    yaxis2=dict(title="Tipo hipotecario 30A (%)", overlaying="y", side="right", color="#9b59b6"),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=320,
                    legend=dict(orientation="h"), margin=dict(t=40, b=20)
                )
                st.plotly_chart(_fig_svc, use_container_width=True)
                st.caption("Con tipos al 7%, una hipoteca nueva absorbe una fraccion record de la renta. Esto frena el consumo discrecional y el mercado inmobiliario a la vez.")
            else:
                st.info("Actualiza los datos para ver la carga de deuda.")

        # ── Interpretacion integrada con regimen ──
        st.divider()
        _rg_ms = _regime_global["regime"]
        _ms_interp = (
            f"**Main Street + Régimen {_rg_ms}:** "
            + ("Estres bajo en el ciudadano y mercados en Risk-On: el ciclo expansivo tiene soporte real del consumo." if _ms_label=="BAJO" and _rg_ms=="RISK-ON"
               else "Estres moderado en el ciudadano pero mercados Risk-On: la bolsa cotiza adelantada — vigilar que los impagos no sigan subiendo." if _ms_label=="MODERADO" and _rg_ms=="RISK-ON"
               else "Estres ALTO en el ciudadano con mercados Risk-On: divergencia peligrosa — el mercado puede estar ignorando el deterioro del consumidor real." if _ms_label=="ALTO" and _rg_ms=="RISK-ON"
               else "Ciudadano sano pero mercados Risk-Off: la caida puede ser tecnica/financiera, no economica. El consumo puede aguantar." if _ms_label=="BAJO" and _rg_ms=="RISK-OFF"
               else "Doble señal negativa: estres en el ciudadano + Risk-Off en mercados. Entorno recesivo probable. Prioriza liquidez y defensivas." if _ms_label in ("MODERADO","ALTO") and _rg_ms=="RISK-OFF"
               else "Señales mixtas. Monitoriza la evolucion de impagos — son el canario en la mina del ciclo economico real.")
        )
        st.info(_ms_interp)

# ─────────────────────────────────────────────────────────────
# PÁGINA 8: EXPORTAR DATOS
# ─────────────────────────────────────────────────────────────
elif "Exportar" in page:
    st.title("Exportar Datos & Graficos")
    st.caption("Descarga cualquier serie como CSV/Excel o cualquier grafico como imagen PNG.")

    import io as _io

    # ── Catálogo de series disponibles ──
    freshness = get_freshness_status()
    all_series = freshness["series_name"].tolist() if not freshness.empty else []
    all_market = ["SPX", "NASDAQ", "IBEX", "EUROSTOXX", "DAX", "RUSSELL2K",
                  "XLK", "XLF", "XLE", "XLV", "XLU", "XLI", "XLC", "XLRE", "XLP", "XLY", "XLB",
                  "GOLD", "OIL", "COPPER", "BTC", "TLT", "HYG", "LQD"]

    tab1, tab2 = st.tabs(["Series macro (CSV / Excel)", "Graficos (PNG)"])

    with tab1:
        st.subheader("Exportar series temporales")
        col1, col2 = st.columns(2)
        with col1:
            selected_series = st.multiselect(
                "Selecciona series macro", all_series,
                default=["VIX", "SPREAD_HY", "CURVE_SPREAD_2Y10Y", "NFCI"] if all_series else []
            )
            selected_market = st.multiselect(
                "Selecciona instrumentos de mercado", all_market,
                default=["SPX", "NASDAQ", "BTC"]
            )
        with col2:
            export_start = st.date_input("Desde", datetime.now() - timedelta(days=5*365), key="exp_start")
            export_end   = st.date_input("Hasta", datetime.now(), key="exp_end")
            fmt = st.radio("Formato", ["CSV", "Excel"], horizontal=True)

        if st.button("Preparar descarga", type="primary"):
            frames = []
            for s in selected_series:
                df = get_series(s, start=str(export_start))
                if not df.empty:
                    df = df[df["date"] <= str(export_end)][["date", "value"]].copy()
                    df.columns = ["date", s]
                    frames.append(df.set_index("date"))

            for m in selected_market:
                df = get_prices(m, start=str(export_start))
                if not df.empty:
                    df = df[df["date"] <= str(export_end)][["date", "close"]].copy()
                    df.columns = ["date", m]
                    frames.append(df.set_index("date"))

            if frames:
                combined = pd.concat(frames, axis=1).reset_index()
                combined = combined.sort_values("date")

                if fmt == "CSV":
                    csv_bytes = combined.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label=f"Descargar CSV ({len(combined)} filas, {len(combined.columns)-1} series)",
                        data=csv_bytes,
                        file_name=f"financial_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        type="primary",
                    )
                else:
                    buf = _io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        combined.to_excel(writer, sheet_name="Datos", index=False)
                        # Hoja de metadatos
                        meta = freshness[freshness["series_name"].isin(selected_series)]
                        if not meta.empty:
                            meta.to_excel(writer, sheet_name="Metadatos", index=False)
                    st.download_button(
                        label=f"Descargar Excel ({len(combined)} filas, {len(combined.columns)-1} series)",
                        data=buf.getvalue(),
                        file_name=f"financial_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                    )
                st.dataframe(combined.tail(10), use_container_width=True, hide_index=True)
            else:
                st.warning("Selecciona al menos una serie.")

    with tab2:
        st.subheader("Exportar graficos como PNG")
        chart_options = {
            "VIX (indice miedo)":                  ("series", "VIX"),
            "NFCI (condiciones financieras)":       ("series", "NFCI"),
            "STLFSI (estres financiero)":           ("series", "STLFSI"),
            "Spread High Yield":                    ("series", "SPREAD_HY"),
            "Curva 10Y-2Y":                         ("series", "CURVE_SPREAD_2Y10Y"),
            "T10Y3M":                               ("series", "T10Y3M"),
            "CPI YoY":                              ("series", "CPI_YOY"),
            "Core PCE YoY":                         ("series", "CORE_PCE_YOY"),
            "Fed Funds Rate":                       ("series", "FED_FUNDS"),
            "Balance Fed (WALCL)":                  ("series", "FED_BALANCE"),
            "ON RRP":                               ("series", "ON_RRP"),
            "M2 USA":                               ("series", "M2_US"),
            "Retail Sales YoY":                     ("series", "RETAIL_SALES"),
            "Produccion Industrial YoY":            ("series", "INDPRO"),
            "Building Permits YoY":                 ("series", "PERMIT"),
            "Initial Claims":                       ("series", "INITIAL_CLAIMS"),
            "S&P 500":                              ("price", "SPX"),
            "Nasdaq":                               ("price", "NASDAQ"),
            "IBEX 35":                              ("price", "IBEX"),
            "Bitcoin":                              ("price", "BTC"),
            "Oro":                                  ("price", "GOLD"),
            "Brent":                                ("price", "OIL"),
        }

        col1, col2, col3 = st.columns(3)
        selected_chart = col1.selectbox("Selecciona grafico", list(chart_options.keys()))
        chart_start = col2.date_input("Desde", datetime.now() - timedelta(days=5*365), key="ch_start")
        chart_height = col3.slider("Alto (px)", 300, 800, 450, 50)

        if st.button("Generar grafico", type="primary"):
            kind, key = chart_options[selected_chart]
            if kind == "series":
                df = get_series(key, start=str(chart_start))
            else:
                df = get_prices(key, start=str(chart_start))
                if not df.empty:
                    df = df.rename(columns={"close": "value"})

            if df is not None and not df.empty:
                fig = go.Figure()
                # Sombreado recesiones
                rec_df = get_series("USREC", start=str(chart_start))
                if not rec_df.empty:
                    in_rec = False; rec_start = None
                    for _, row in rec_df.iterrows():
                        if row["value"] == 1 and not in_rec:
                            in_rec = True; rec_start = row["date"]
                        elif row["value"] == 0 and in_rec:
                            in_rec = False
                            fig.add_vrect(x0=rec_start, x1=row["date"],
                                         fillcolor="red", opacity=0.08, layer="below", line_width=0)

                if kind == "price":
                    # Añadir medias móviles a precios
                    df2 = df.copy()
                    df2["ma50"]  = df2["value"].rolling(50).mean()
                    df2["ma200"] = df2["value"].rolling(200).mean()
                    fig.add_scatter(x=df2["date"], y=df2["value"],
                                   name=selected_chart, line=dict(color="#3498db", width=1.5))
                    fig.add_scatter(x=df2["date"], y=df2["ma50"],
                                   name="MA 50", line=dict(color="orange", dash="dot", width=1))
                    fig.add_scatter(x=df2["date"], y=df2["ma200"],
                                   name="MA 200", line=dict(color="#e74c3c", dash="dash", width=1))
                else:
                    fig.add_scatter(x=df["date"], y=df["value"],
                                   name=selected_chart, line=dict(color="#3498db", width=1.5))

                fig.update_layout(
                    title=dict(text=selected_chart, font=dict(size=18)),
                    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                    font_color="white", height=chart_height,
                    margin=dict(t=60, b=40, l=60, r=40),
                    legend=dict(orientation="h", y=-0.15),
                    xaxis=dict(showgrid=True, gridcolor="#2a2d3a"),
                    yaxis=dict(showgrid=True, gridcolor="#2a2d3a"),
                )

                st.plotly_chart(fig, use_container_width=True)

                # Descarga PNG via kaleido
                try:
                    img_bytes = fig.to_image(format="png", width=1400, height=chart_height, scale=2)
                    st.download_button(
                        label="Descargar PNG (alta resolucion)",
                        data=img_bytes,
                        file_name=f"{key}_{datetime.now().strftime('%Y%m%d')}.png",
                        mime="image/png",
                        type="primary",
                    )
                except Exception:
                    st.info("Para exportar PNG instala kaleido: pip install kaleido")
            else:
                st.warning("Sin datos para este grafico.")

# ─────────────────────────────────────────────────────────────
# PÁGINA 9: ESTADO DE DATOS (PUNTO 3)
# ─────────────────────────────────────────────────────────────
elif "Estado" in page:
    st.title("Estado & Frescura de Datos")
    st.caption("Monitorización del lag de cada serie para evitar decisiones con datos obsoletos.")

    freshness = get_freshness_status()
    if freshness.empty:
        st.info("No hay datos en la base de datos aún. Ejecuta la actualización desde el menú lateral.")
    else:
        stale = freshness[freshness["is_stale"] == True]
        fresh = freshness[freshness["is_stale"] == False]

        col1, col2, col3 = st.columns(3)
        col1.metric("Series totales", len(freshness))
        col2.metric("Series frescas", len(fresh), delta_color="normal")
        col3.metric("Series obsoletas", len(stale), delta_color="inverse")

        if not stale.empty:
            st.error("**Series con datos obsoletos:**")
            st.dataframe(stale[["series_name", "description", "last_data_date",
                                "data_lag_days", "expected_next"]],
                        use_container_width=True, hide_index=True)

        st.success("**Series actualizadas:**")
        st.dataframe(fresh[["series_name", "description", "last_data_date",
                             "data_lag_days"]],
                    use_container_width=True, hide_index=True)

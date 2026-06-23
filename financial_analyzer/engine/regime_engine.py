"""
Motor de Regimenes Risk-On / Risk-Off.
Sistema de scoring compuesto 0-100 con 6 sub-scores auditables.

Sub-scores:
  Liquidity Score       max 28  (ampliado con deficit fiscal y eurodolar)
  Risk Appetite Score   max 25
  Growth & Activity     max 20
  Valuation             max 12
  Momentum & Technical  max 15

Umbrales: >70 Risk-On | 40-70 Neutral | <40 Risk-Off

v2: Incorpora logica de deficit fiscal como suelo implicito,
    sistema eurodolar (FX swaps, DXY), fontaneria (ON RRP, SOFR),
    y correlacion BTC-liquidez.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RegimeScore:
    liquidity:     float = 0.0   # max 28 (era 25 — ampliado con deficit/eurodolar)
    risk_appetite: float = 0.0   # max 25
    growth:        float = 0.0   # max 20
    valuation:     float = 0.0   # max 12
    momentum:      float = 0.0   # max 15

    details: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)  # señales de alerta critica
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total(self) -> float:
        raw = self.liquidity + self.risk_appetite + self.growth + self.valuation + self.momentum
        # Normalizar a 100 (maximo teorico = 100)
        return min(round(raw, 1), 100.0)

    @property
    def regime(self) -> str:
        if self.total >= 70:
            return "RISK-ON"
        elif self.total >= 40:
            return "NEUTRAL"
        else:
            return "RISK-OFF"

    @property
    def regime_color(self) -> str:
        return {"RISK-ON": "#2ecc71", "NEUTRAL": "#f39c12", "RISK-OFF": "#e74c3c"}[self.regime]

    @property
    def action(self) -> str:
        return {
            "RISK-ON":  "Aumentar beta: growth, small caps, momentum, BTC. Reducir defensivas.",
            "NEUTRAL":  "Mantener exposicion. Rotar hacia calidad. Vigilar cambios de señal.",
            "RISK-OFF": "Reducir beta. Priorizar defensivas (utilities, healthcare, staples) y liquidez.",
        }[self.regime]

    def to_dict(self) -> dict:
        return {
            "total":          round(self.total, 1),
            "regime":         self.regime,
            "regime_color":   self.regime_color,
            "action":         self.action,
            "liquidity":      round(self.liquidity, 1),
            "risk_appetite":  round(self.risk_appetite, 1),
            "growth":         round(self.growth, 1),
            "valuation":      round(self.valuation, 1),
            "momentum":       round(self.momentum, 1),
            "details":        self.details,
            "warnings":       self.warnings,
            "timestamp":      self.timestamp,
        }


def compute_regime_score(inputs: dict) -> RegimeScore:
    """
    Calcula el score de regimen a partir del dict de inputs.

    Inputs esperados (todos opcionales — se calcula con lo disponible):
    --- LIQUIDEZ BASE ---
        m2_growth_pct        Crecimiento M2 anual (%)
        fed_balance_change   Cambio balance Fed 3m (positivo = expansion)
        ted_spread           TED spread (%)
        on_rrp_trend         Tendencia ON RRP: 'draining' | 'stable' | 'rising'
        sofr_spike           Bool: SOFR subio >20bps en 5 dias (estres repo)

    --- DEFICIT FISCAL / EURODOLAR (nuevos) ---
        deficit_pct_gdp      Deficit fiscal EEUU TTM como % del PIB
        deficit_trend        Tendencia deficit: 'widening' | 'stable' | 'narrowing'
        fx_swaps_active      Bool: lineas FX swap de la Fed activadas (>50bn)
        dxy_vs_200dma        DXY relativo a su media 200d (% diferencia)
        dxy_accelerating     Bool: DXY subiendo >2% en 20 dias

    --- APETITO AL RIESGO ---
        vix                  VIX actual
        hy_spread            Spread High Yield actual (%)
        hy_spread_change     Cambio spread HY 3m (negativo = mejora)
        pct_above_200dma     % sectores S&P sobre media 200d (0-100)
        nfci                 Chicago Fed Financial Conditions Index

    --- CRECIMIENTO ---
        pmi_composite        PMI compuesto (>50 expansion)
        consumer_conf_change Cambio confianza consumidor
        unemployment_change  Cambio tasa paro (negativo = mejora)
        gdp_growth           Crecimiento PIB (%)
        retail_sales_yoy     Retail Sales variacion anual (%)

    --- VALORACION ---
        curve_spread         Spread 10Y-2Y (puntos porcentuales)
        t10y3m               Spread 10Y-3M (puntos porcentuales)
        real_rate            Tipo real 10Y (%)

    --- MOMENTUM ---
        spx_vs_200dma        % SPX vs media 200d
        spx_momentum_pos     Bool: ROC 3M positivo
        breadth_strong       Bool: % sectores sobre 200d > 60%
        defensives_leading   Bool: utilities/healthcare liderando (señal negativa)
        btc_corr_liquidity   Correlacion rodante 90d BTC vs Balance Fed
    """
    score = RegimeScore()
    details = {}
    warnings = []

    # ── 1. LIQUIDITY SCORE (max 28) ──────────────────────────────────
    # Ampliado: incluye deficit fiscal estructural y sistema eurodolar
    liq = 0.0

    # M2 crecimiento (max 8 pts)
    m2g = inputs.get("m2_growth_pct")
    if m2g is not None:
        pts = 8 if m2g > 5 else (5 if m2g > 2 else 2)
        liq += pts
        details["m2_growth"] = {"value": round(m2g, 1), "pts": pts,
                                 "label": "M2 crecimiento anual (%)"}

    # Balance Fed tendencia (max 6 pts)
    fed_chg = inputs.get("fed_balance_change", 0)
    if fed_chg is not None:
        pts = 6 if fed_chg > 50 else (3 if fed_chg > 0 else 0)
        liq += pts
        details["fed_balance"] = {"value": round(fed_chg, 0), "pts": pts,
                                   "label": "Balance Fed expandiendose (miles millones $)"}

    # Deficit fiscal como suelo implicito (max 7 pts — NUEVO)
    # Un deficit amplio garantiza inyeccion constante de dolares al sistema
    deficit_pct = inputs.get("deficit_pct_gdp")
    deficit_trend = inputs.get("deficit_trend", "stable")
    if deficit_pct is not None:
        if deficit_pct < -5:          # deficit >5% PIB = suelo fuerte
            pts = 7
            label = f"Deficit fiscal {deficit_pct:.1f}% PIB — suelo implicito fuerte"
        elif deficit_pct < -3:
            pts = 4
            label = f"Deficit fiscal {deficit_pct:.1f}% PIB — suelo moderado"
        else:
            pts = 1
            label = f"Deficit fiscal {deficit_pct:.1f}% PIB — suelo debil"
        if deficit_trend == "widening":
            pts = min(pts + 1, 7)     # deficit ampliandose = mas liquidez entrando
        liq += pts
        details["deficit_fiscal"] = {"value": round(deficit_pct, 1), "pts": pts, "label": label}

    # ON RRP tendencia (max 4 pts)
    # ON RRP cayendo = liquidez saliendo al mercado = positivo para activos
    on_rrp = inputs.get("on_rrp_trend", "stable")
    rrp_pts = {"draining": 4, "stable": 2, "rising": 0}
    liq += rrp_pts.get(on_rrp, 2)
    details["on_rrp"] = {"value": on_rrp, "pts": rrp_pts.get(on_rrp, 2),
                          "label": "ON RRP tendencia (draining = liquidez al mercado)"}

    # Penalizaciones del sistema eurodolar (NUEVO)
    fx_swaps = inputs.get("fx_swaps_active", False)
    if fx_swaps:
        liq -= 8
        warnings.append("ALERTA CRITICA: FX Swap Lines Fed activadas — escasez de eurodolares sistémica")
        details["fx_swaps"] = {"value": True, "pts": -8,
                                "label": "FX Swaps activas — estrés eurodolar"}

    sofr_spike = inputs.get("sofr_spike", False)
    if sofr_spike:
        liq -= 5
        warnings.append("ALERTA: SOFR spike detectado — estres en mercado repo interbancario")
        details["sofr_spike"] = {"value": True, "pts": -5,
                                  "label": "SOFR spike — estrés repo"}

    ted = inputs.get("ted_spread")
    if ted is not None:
        pts = 3 if ted < 0.3 else (1 if ted < 0.5 else -3)
        liq += pts
        details["ted_spread"] = {"value": round(ted, 2), "pts": pts,
                                   "label": "TED Spread (%)"}

    score.liquidity = max(0.0, min(liq, 28.0))

    # ── 2. RISK APPETITE SCORE (max 25) ──────────────────────────────
    risk = 0.0

    # VIX (max 8 pts)
    vix = inputs.get("vix")
    if vix is not None:
        pts = 8 if vix < 15 else (6 if vix < 18 else (4 if vix < 25 else (1 if vix < 35 else 0)))
        risk += pts
        details["vix"] = {"value": round(vix, 1), "pts": pts, "label": "VIX"}
        if vix > 30:
            warnings.append(f"VIX en zona de panico ({vix:.0f}) — posible capitulacion o inicio Risk-Off")

    # HY Spread nivel y tendencia (max 7 pts)
    hy = inputs.get("hy_spread")
    hy_chg = inputs.get("hy_spread_change")
    if hy is not None:
        pts_nivel = 3 if hy < 3 else (2 if hy < 4 else (0 if hy < 6 else -2))
        risk += pts_nivel
        details["hy_level"] = {"value": round(hy, 2), "pts": pts_nivel,
                                "label": "Spread HY nivel (%)"}
        if hy > 6:
            warnings.append(f"Spread HY en zona de estres ({hy:.1f}%) — señal Risk-Off crediticio")
    if hy_chg is not None:
        pts_trend = 4 if hy_chg < -0.2 else (2 if hy_chg < 0 else 0)
        risk += pts_trend
        details["hy_trend"] = {"value": round(hy_chg, 2), "pts": pts_trend,
                                "label": "Spread HY tendencia 3M"}

    # % sectores sobre 200DMA (max 6 pts)
    pct = inputs.get("pct_above_200dma")
    if pct is not None:
        pts = 6 if pct > 65 else (4 if pct > 50 else (2 if pct > 35 else 0))
        risk += pts
        details["pct_200dma"] = {"value": round(pct, 1), "pts": pts,
                                  "label": "% sectores S&P sobre 200DMA"}

    # NFCI (max 4 pts — NUEVO)
    # NFCI negativo = condiciones financieras laxas = Risk-On
    nfci = inputs.get("nfci")
    if nfci is not None:
        pts = 4 if nfci < -0.3 else (2 if nfci < 0 else (0 if nfci < 0.5 else -3))
        risk += pts
        details["nfci"] = {"value": round(nfci, 3), "pts": pts,
                            "label": "NFCI (negativo = condiciones laxas)"}
        if nfci > 0.5:
            warnings.append(f"NFCI en zona de estres ({nfci:.2f}) — condiciones financieras apretadas")

    # DXY eurodolar (penalizacion si dolar se dispara — NUEVO)
    dxy_vs200 = inputs.get("dxy_vs_200dma")
    dxy_accel  = inputs.get("dxy_accelerating", False)
    if dxy_vs200 is not None:
        if dxy_vs200 > 3 and dxy_accel:
            risk -= 4
            warnings.append(f"DXY acelerando +{dxy_vs200:.1f}% vs 200DMA — posible escasez eurodolares")
            details["dxy_eurodolar"] = {"value": round(dxy_vs200, 1), "pts": -4,
                                         "label": "DXY acelerando = escasez de dolares globales"}
        elif dxy_vs200 > 2:
            risk -= 2
            details["dxy_eurodolar"] = {"value": round(dxy_vs200, 1), "pts": -2,
                                         "label": "DXY por encima de 200DMA = presion sobre riesgo"}

    score.risk_appetite = max(0.0, min(risk, 25.0))

    # ── 3. GROWTH & ACTIVITY SCORE (max 20) ──────────────────────────
    growth = 0.0

    pmi = inputs.get("pmi_composite")
    if pmi is not None:
        pts = 6 if pmi > 53 else (4 if pmi > 51 else (2 if pmi > 50 else 0))
        growth += pts
        details["pmi"] = {"value": round(pmi, 1), "pts": pts,
                           "label": "PMI compuesto (>50 = expansion)"}

    conf = inputs.get("consumer_conf_change")
    if conf is not None:
        pts = 4 if conf > 2 else (2 if conf > 0 else 0)
        growth += pts
        details["consumer_conf"] = {"value": round(conf, 1), "pts": pts,
                                     "label": "Confianza consumidor (cambio)"}

    unemp = inputs.get("unemployment_change")
    if unemp is not None:
        pts = 5 if unemp < -0.1 else (2 if unemp < 0 else 0)
        growth += pts
        details["unemployment"] = {"value": round(unemp, 2), "pts": pts,
                                    "label": "Tasa paro (cambio, negativo = mejora)"}

    gdp = inputs.get("gdp_growth")
    if gdp is not None:
        pts = 5 if gdp > 2.5 else (3 if gdp > 1 else (1 if gdp > 0 else 0))
        growth += pts
        details["gdp"] = {"value": round(gdp, 1), "pts": pts,
                           "label": "PIB growth (%)"}

    # Retail Sales (indicador adelantado de consumo — NUEVO)
    retail = inputs.get("retail_sales_yoy")
    if retail is not None:
        pts = 3 if retail > 4 else (2 if retail > 1 else (0 if retail > -1 else -1))
        growth += pts
        details["retail_sales"] = {"value": round(retail, 1), "pts": pts,
                                    "label": "Retail Sales YoY (%)"}

    score.growth = max(0.0, min(growth, 20.0))

    # ── 4. VALUATION & OPPORTUNITY SCORE (max 12) ────────────────────
    val = 0.0

    # Curva de tipos (dos spreads — NUEVO: usar ambos T10Y2Y y T10Y3M)
    curve = inputs.get("curve_spread")
    t10y3m = inputs.get("t10y3m")
    if curve is not None and t10y3m is not None:
        # Ambas curvas: si las dos estan invertidas, señal muy negativa
        if curve > 0 and t10y3m > 0:
            val += 5
            details["curves"] = {"pts": 5, "label": "Ambas curvas (10Y-2Y y 10Y-3M) en positivo"}
        elif curve > 0 or t10y3m > 0:
            val += 3
            details["curves"] = {"pts": 3, "label": "Una curva en positivo, otra invertida"}
        else:
            val += 0
            warnings.append(f"Ambas curvas invertidas (T10Y2Y:{curve:.2f}, T10Y3M:{t10y3m:.2f}) — señal recesion historica")
            details["curves"] = {"pts": 0, "label": "Ambas curvas invertidas — señal recesion"}
    elif curve is not None:
        pts = 4 if curve > 0 else (2 if curve > -0.5 else 0)
        val += pts
        details["curve"] = {"value": round(curve, 2), "pts": pts,
                             "label": "Curva 10Y-2Y"}

    real_rate = inputs.get("real_rate")
    if real_rate is not None:
        pts = 4 if -0.5 < real_rate < 1.5 else (2 if real_rate < 2.5 else 0)
        val += pts
        details["real_rate"] = {"value": round(real_rate, 2), "pts": pts,
                                  "label": "Tipo real 10Y (%)"}

    score.valuation = max(0.0, min(val + 3, 12.0))  # +3 base

    # ── 5. MOMENTUM & TECHNICAL SCORE (max 15) ───────────────────────
    mom = 0.0

    spx_200 = inputs.get("spx_vs_200dma")
    spx_mom = inputs.get("spx_momentum_pos", False)
    if spx_200 is not None:
        if spx_200 > 2 and spx_mom:
            mom += 6
            details["spx_momentum"] = {"value": round(spx_200, 1), "pts": 6,
                                        "label": "SPX +2% vs 200DMA con momentum positivo"}
        elif spx_200 > 0:
            mom += 3
            details["spx_momentum"] = {"value": round(spx_200, 1), "pts": 3,
                                        "label": "SPX sobre 200DMA"}
        else:
            warnings.append(f"SPX por debajo de media 200d ({spx_200:.1f}%) — tendencia deteriorada")

    breadth = inputs.get("breadth_strong", False)
    if breadth:
        mom += 5
        details["breadth"] = {"pts": 5, "label": "Breadth fuerte (>60% sectores sobre 200DMA)"}

    def_lead = inputs.get("defensives_leading", None)
    if def_lead is False:
        mom += 4
        details["defensives"] = {"pts": 4, "label": "Sectores defensivos NO liderando (positivo)"}
    elif def_lead is True:
        warnings.append("Sectores defensivos liderando — rotacion defensiva en marcha")

    # BTC correlacion con liquidez (señal de confirmacion — NUEVO)
    btc_corr = inputs.get("btc_corr_liquidity")
    if btc_corr is not None and btc_corr > 0.6:
        # Alta correlacion BTC-liquidez + regimen Risk-On = señal confirmada
        details["btc_liquidity"] = {"value": round(btc_corr, 2), "pts": 0,
                                     "label": f"BTC correlacion con Balance Fed: {btc_corr:.2f} (confirma señal liquidez)"}

    score.momentum = max(0.0, min(mom, 15.0))
    score.details = details
    score.warnings = warnings

    return score


def build_inputs_from_db(db_path: str, start: str = "2020-01-01") -> dict:
    """
    Construye el dict de inputs para compute_regime_score directamente desde DuckDB.
    Llama a esta funcion desde el dashboard para obtener el score en tiempo real.
    """
    import duckdb
    import pandas as pd

    # Abrir sin read_only para evitar conflictos cuando Streamlit tiene la DB abierta
    try:
        con = duckdb.connect(db_path, read_only=False)
    except Exception:
        try:
            con = duckdb.connect(db_path, read_only=True)
        except Exception:
            return {}

    def latest(series: str):
        try:
            row = con.execute(
                "SELECT value FROM time_series WHERE series_name=? AND value IS NOT NULL "
                "ORDER BY date DESC LIMIT 1", [series]
            ).fetchone()
            return float(row[0]) if row else None
        except Exception as e:
            return None

    def change_3m(series: str):
        """Cambio entre ultimo valor y hace ~63 dias."""
        try:
            rows = con.execute(
                "SELECT value FROM time_series WHERE series_name=? AND value IS NOT NULL "
                "ORDER BY date DESC LIMIT 70", [series]
            ).fetchall()
            if len(rows) >= 63:
                return float(rows[0][0]) - float(rows[62][0])
        except Exception:
            pass
        return None

    def growth_yoy(series: str):
        """Variacion anual del ultimo dato."""
        try:
            rows = con.execute(
                "SELECT value FROM time_series WHERE series_name=? AND value IS NOT NULL "
                "ORDER BY date DESC LIMIT 14", [series]
            ).fetchall()
            now_row = con.execute(
                "SELECT value FROM time_series WHERE series_name=? AND value IS NOT NULL "
                "ORDER BY date DESC LIMIT 1", [series]
            ).fetchone()
            year_ago = con.execute(
                "SELECT value FROM time_series WHERE series_name=? AND value IS NOT NULL "
                "AND date <= date('now', '-11 months') ORDER BY date DESC LIMIT 1", [series]
            ).fetchone()
            if now_row and year_ago:
                now_v = float(now_row[0])
                ago_v = float(year_ago[0])
                return ((now_v / ago_v) - 1) * 100 if ago_v != 0 else None
        except Exception:
            pass
        return None

    def price_vs_ma200(ticker: str):
        try:
            rows = con.execute(
                "SELECT close FROM market_prices WHERE name=? AND close IS NOT NULL "
                "ORDER BY date DESC LIMIT 210", [ticker]
            ).fetchall()
            if len(rows) >= 200:
                current = float(rows[0][0])
                ma200 = sum(float(r[0]) for r in rows[:200]) / 200
                return ((current / ma200) - 1) * 100
        except Exception:
            pass
        return None

    def dxy_vs_200():
        return price_vs_ma200("DXY") if True else None

    def btc_walcl_corr():
        """Correlacion rodante 90 dias BTC vs Balance Fed."""
        try:
            btc = pd.read_sql(
                "SELECT date, close as value FROM market_prices WHERE name='BTC' "
                "AND close IS NOT NULL ORDER BY date DESC LIMIT 120", con
            )
            walcl = pd.read_sql(
                "SELECT date, value FROM time_series WHERE series_name='FED_BALANCE' "
                "AND value IS NOT NULL ORDER BY date DESC LIMIT 120", con
            )
            if btc.empty or walcl.empty:
                return None
            btc["date"] = pd.to_datetime(btc["date"])
            walcl["date"] = pd.to_datetime(walcl["date"])
            merged = pd.merge_asof(
                btc.sort_values("date"),
                walcl.sort_values("date").rename(columns={"value": "walcl"}),
                on="date", direction="nearest"
            ).dropna()
            if len(merged) < 30:
                return None
            return float(merged["value"].corr(merged["walcl"]))
        except Exception:
            return None

    # Precio SPX vs 200DMA
    spx_200 = price_vs_ma200("SPX")

    # Momentum SPX (ROC 3M positivo)
    spx_mom = None
    try:
        rows = con.execute(
            "SELECT close FROM market_prices WHERE name='SPX' AND close IS NOT NULL "
            "ORDER BY date DESC LIMIT 70"
        ).fetchall()
        if len(rows) >= 63:
            spx_mom = float(rows[0][0]) > float(rows[62][0])
    except Exception:
        pass

    # DXY acelerando (>2% en 20 dias)
    dxy_accel = None
    try:
        rows = con.execute(
            "SELECT close FROM market_prices WHERE name='DXY' AND close IS NOT NULL "
            "ORDER BY date DESC LIMIT 25"
        ).fetchall()
        if len(rows) >= 20:
            dxy_accel = ((float(rows[0][0]) / float(rows[19][0])) - 1) * 100 > 2
    except Exception:
        pass

    # ON RRP tendencia
    onrrp_chg = change_3m("ON_RRP")
    if onrrp_chg is not None:
        on_rrp_trend = "draining" if onrrp_chg < -100 else ("rising" if onrrp_chg > 100 else "stable")
    else:
        on_rrp_trend = "stable"

    # FX Swaps activos
    fx_swaps_val = latest("FX_SWAPS")
    fx_swaps_active = fx_swaps_val is not None and fx_swaps_val > 50_000

    # SOFR spike (subida >20bps en 5 dias)
    sofr_spike = False
    try:
        rows = con.execute(
            "SELECT value FROM time_series WHERE series_name='SOFR' AND value IS NOT NULL "
            "ORDER BY date DESC LIMIT 7"
        ).fetchall()
        if len(rows) >= 5:
            sofr_spike = (float(rows[0][0]) - float(rows[4][0])) > 0.20
    except Exception:
        pass

    # Pct sectores sobre 200DMA
    breadth_val = latest("PCT_SECTORS_ABOVE_200DMA")

    # M2 crecimiento YoY
    m2_yoy = growth_yoy("M2_US")

    # Balance Fed cambio 3M (miles millones)
    fed_chg = change_3m("FED_BALANCE")

    # Deficit fiscal
    deficit_pct = latest("DEFICIT_PCT_GDP")
    deficit_chg = change_3m("DEFICIT_PCT_GDP")
    deficit_trend = "widening" if (deficit_chg or 0) < -0.3 else (
        "narrowing" if (deficit_chg or 0) > 0.3 else "stable")

    # HY spread
    hy_val = latest("SPREAD_HY")
    hy_chg = change_3m("SPREAD_HY")

    # Apetito riesgo
    vix_val    = latest("VIX")
    nfci_val   = latest("NFCI")

    # Crecimiento
    unemp_chg  = change_3m("UNEMPLOYMENT_US")
    retail_val = latest("RETAIL_SALES")

    # Valoracion / tipos
    ted_val    = latest("TED_SPREAD")
    curve_val  = latest("CURVE_SPREAD_2Y10Y")
    t10y3m_val = latest("T10Y3M")
    real_val   = latest("REAL_RATE_10Y")

    # DXY
    dxy_200 = dxy_vs_200()

    # Correlacion BTC-liquidez
    btc_corr = btc_walcl_corr()

    con.close()

    return {
        # Liquidez
        "m2_growth_pct":       m2_yoy,
        "fed_balance_change":  fed_chg,
        "ted_spread":          ted_val,
        "on_rrp_trend":        on_rrp_trend,
        "sofr_spike":          sofr_spike,
        # Deficit / Eurodolar
        "deficit_pct_gdp":     deficit_pct,
        "deficit_trend":       deficit_trend,
        "fx_swaps_active":     fx_swaps_active,
        "dxy_vs_200dma":       dxy_200,
        "dxy_accelerating":    dxy_accel,
        # Apetito riesgo
        "vix":                 vix_val,
        "hy_spread":           hy_val,
        "hy_spread_change":    hy_chg,
        "pct_above_200dma":    breadth_val,
        "nfci":                nfci_val,
        # Crecimiento
        "pmi_composite":       None,
        "consumer_conf_change":None,
        "unemployment_change": unemp_chg,
        "gdp_growth":          None,
        "retail_sales_yoy":    retail_val,
        # Valoracion
        "curve_spread":        curve_val,
        "t10y3m":              t10y3m_val,
        "real_rate":           real_val,
        # Momentum
        "spx_vs_200dma":       spx_200,
        "spx_momentum_pos":    spx_mom,
        "breadth_strong":      breadth_val is not None and breadth_val > 60,
        "defensives_leading":  None,
        "btc_corr_liquidity":  btc_corr,
    }

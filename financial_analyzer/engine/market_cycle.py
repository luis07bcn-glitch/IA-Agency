"""
Módulo de Fases del Ciclo Económico de Mercado.
Basado en el Fidelity Investment Clock y el modelo de ciclo económico clásico.

Las 4 fases determinan qué sectores y activos favorece el mercado:
- EARLY RECOVERY: economía saliendo de recesión, bancos centrales expansivos
- MID EXPANSION:  crecimiento sólido, beneficios mejorando, la fase más larga
- LATE CYCLE:     crecimiento desacelerando, inflación alta, BC restrictivos
- RECESSION:      contracción económica, Risk-Off puro

Incluye sectores favorecidos y señales de detección para cada fase.
"""
from dataclasses import dataclass, field
from enum import Enum


class CyclePhase(str, Enum):
    EARLY_RECOVERY = "EARLY RECOVERY"
    MID_EXPANSION  = "MID EXPANSION"
    LATE_CYCLE     = "LATE CYCLE"
    RECESSION      = "RECESSION"
    UNDEFINED      = "INDEFINIDO"


CYCLE_PROFILES = {
    CyclePhase.EARLY_RECOVERY: {
        "description": "Salida de recesión. BC expansivos. Crédito mejorando.",
        "favored_sectors": ["Financiero (XLF)", "Consumo Discrecional (XLY)", "Industriales (XLI)", "Materiales (XLB)"],
        "avoid_sectors":   ["Utilities (XLU)", "Consumer Staples (XLP)"],
        "asset_bias":      "Acciones de alta beta, small caps, high yield, commodities cíclicas",
        "bitcoin_signal":  "Fuerte positivo — liquidez en expansión suele coincidir",
        "color":           "#2ecc71",
    },
    CyclePhase.MID_EXPANSION: {
        "description": "Crecimiento sólido. Beneficios al alza. PMIs en expansión. Fase más rentable.",
        "favored_sectors": ["Tecnología (XLK)", "Industriales (XLI)", "Energía (XLE)", "Comunicaciones (XLC)"],
        "avoid_sectors":   ["Bonos largos", "Utilities (XLU)"],
        "asset_bias":      "Momentum en equities. Sobreponderar growth y quality. Reducir bonos.",
        "bitcoin_signal":  "Positivo — correlación con Nasdaq y apetito al riesgo",
        "color":           "#3498db",
    },
    CyclePhase.LATE_CYCLE: {
        "description": "Crecimiento desacelerando. Inflación persistente. BC restrictivos. Curva aplanándose.",
        "favored_sectors": ["Energía (XLE)", "Materiales (XLB)", "Healthcare (XLV)", "Consumer Staples (XLP)"],
        "avoid_sectors":   ["Tecnología (XLK)", "Consumo Discrecional (XLY)", "Real Estate (XLRE)"],
        "asset_bias":      "Reducir duración. Commodities y value. Empezar a incorporar defensivas.",
        "bitcoin_signal":  "Negativo — BC restrictivos contraen liquidez",
        "color":           "#f39c12",
    },
    CyclePhase.RECESSION: {
        "description": "Contracción económica. PMIs <50. Desempleo subiendo. Risk-Off puro.",
        "favored_sectors": ["Utilities (XLU)", "Healthcare (XLV)", "Consumer Staples (XLP)", "Bonos gobierno"],
        "avoid_sectors":   ["Energía (XLE)", "Financiero (XLF)", "Industriales (XLI)", "Small Caps"],
        "asset_bias":      "Máxima calidad y liquidez. Bonos gobierno. Oro. Reducir renta variable.",
        "bitcoin_signal":  "Muy negativo — correlaciona con activos de riesgo en caídas",
        "color":           "#e74c3c",
    },
    CyclePhase.UNDEFINED: {
        "description": "Señales contradictorias. Transición entre fases o datos insuficientes.",
        "favored_sectors": [],
        "avoid_sectors":   [],
        "asset_bias":      "Mantener posicionamiento neutral. Esperar confirmación de señales.",
        "bitcoin_signal":  "Neutral",
        "color":           "#95a5a6",
    },
}


@dataclass
class CycleDetection:
    phase: CyclePhase = CyclePhase.UNDEFINED
    confidence: float = 0.0
    signals_supporting: list = field(default_factory=list)
    signals_against: list = field(default_factory=list)

    @property
    def profile(self) -> dict:
        return CYCLE_PROFILES[self.phase]

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "confidence": round(self.confidence, 1),
            "description": self.profile["description"],
            "favored_sectors": self.profile["favored_sectors"],
            "avoid_sectors": self.profile["avoid_sectors"],
            "asset_bias": self.profile["asset_bias"],
            "bitcoin_signal": self.profile["bitcoin_signal"],
            "color": self.profile["color"],
            "signals_supporting": self.signals_supporting,
            "signals_against": self.signals_against,
        }


def detect_cycle_phase(inputs: dict) -> CycleDetection:
    """
    Detecta la fase del ciclo económico basándose en las señales disponibles.

    inputs esperados (todos opcionales, más señales = más confianza):
        pmi_composite       - PMI compuesto (>52 expansión, <50 contracción)
        pmi_trend           - Tendencia PMI: 'rising' | 'falling'
        unemployment_change - Cambio tasa paro (negativo = mejora)
        gdp_growth          - Crecimiento PIB (%)
        gdp_trend           - Tendencia PIB: 'accelerating' | 'decelerating'
        inflation_rate      - Tasa de inflación (%)
        inflation_trend     - Tendencia inflación: 'rising' | 'falling'
        curve_spread        - Spread 10Y-2Y (invertida = <0)
        cb_stance           - Política banco central: 'expansive' | 'neutral' | 'restrictive'
        credit_spread_trend - Tendencia spreads: 'tightening' | 'widening'
        leading_sector      - Sector con mejor RS: 'defensive' | 'cyclical' | 'growth'
    """
    scores = {phase: 0.0 for phase in CyclePhase if phase != CyclePhase.UNDEFINED}
    supporting = {phase: [] for phase in scores}

    pmi = inputs.get("pmi_composite", 50)
    pmi_trend = inputs.get("pmi_trend", "stable")
    gdp_growth = inputs.get("gdp_growth", 1.5)
    gdp_trend = inputs.get("gdp_trend", "stable")
    inflation = inputs.get("inflation_rate", 2.0)
    inflation_trend = inputs.get("inflation_trend", "stable")
    curve = inputs.get("curve_spread", 0.0)
    cb_stance = inputs.get("cb_stance", "neutral")
    credit_trend = inputs.get("credit_spread_trend", "stable")
    unemp_chg = inputs.get("unemployment_change", 0)
    leading = inputs.get("leading_sector", "mixed")

    # ── EARLY RECOVERY signals ──
    if pmi_trend == "rising" and pmi < 52:
        scores[CyclePhase.EARLY_RECOVERY] += 2
        supporting[CyclePhase.EARLY_RECOVERY].append("PMI subiendo desde niveles bajos")
    if cb_stance == "expansive":
        scores[CyclePhase.EARLY_RECOVERY] += 2
        supporting[CyclePhase.EARLY_RECOVERY].append("Política monetaria expansiva")
    if credit_trend == "tightening":
        scores[CyclePhase.EARLY_RECOVERY] += 1.5
        supporting[CyclePhase.EARLY_RECOVERY].append("Spreads crédito estrechándose")
    if unemp_chg < -0.1:
        scores[CyclePhase.EARLY_RECOVERY] += 1.5
        supporting[CyclePhase.EARLY_RECOVERY].append("Desempleo cayendo")
    if leading == "cyclical":
        scores[CyclePhase.EARLY_RECOVERY] += 1
        supporting[CyclePhase.EARLY_RECOVERY].append("Sectores cíclicos liderando")

    # ── MID EXPANSION signals ──
    if 50 < pmi < 55 and pmi_trend != "falling":
        scores[CyclePhase.MID_EXPANSION] += 2
        supporting[CyclePhase.MID_EXPANSION].append("PMI en zona de expansión sostenida")
    if gdp_growth > 2 and gdp_trend != "decelerating":
        scores[CyclePhase.MID_EXPANSION] += 2
        supporting[CyclePhase.MID_EXPANSION].append("PIB creciendo >2% con tendencia estable")
    if 1 < inflation < 3.5 and inflation_trend == "stable":
        scores[CyclePhase.MID_EXPANSION] += 1.5
        supporting[CyclePhase.MID_EXPANSION].append("Inflación moderada y estable")
    if curve > 0.5:
        scores[CyclePhase.MID_EXPANSION] += 1.5
        supporting[CyclePhase.MID_EXPANSION].append("Curva de tipos positiva y empinada")
    if leading == "growth":
        scores[CyclePhase.MID_EXPANSION] += 1
        supporting[CyclePhase.MID_EXPANSION].append("Sectores growth liderando")

    # ── LATE CYCLE signals ──
    if pmi > 52 and pmi_trend == "falling":
        scores[CyclePhase.LATE_CYCLE] += 2
        supporting[CyclePhase.LATE_CYCLE].append("PMI alto pero cayendo (pico de ciclo)")
    if inflation > 3.5:
        scores[CyclePhase.LATE_CYCLE] += 2
        supporting[CyclePhase.LATE_CYCLE].append("Inflación elevada y persistente")
    if cb_stance == "restrictive":
        scores[CyclePhase.LATE_CYCLE] += 2
        supporting[CyclePhase.LATE_CYCLE].append("BC restrictivos (subidas de tipos)")
    if -0.5 < curve < 0.5:
        scores[CyclePhase.LATE_CYCLE] += 1.5
        supporting[CyclePhase.LATE_CYCLE].append("Curva aplanándose")
    if gdp_trend == "decelerating":
        scores[CyclePhase.LATE_CYCLE] += 1.5
        supporting[CyclePhase.LATE_CYCLE].append("Crecimiento desacelerando")

    # ── RECESSION signals ──
    if pmi < 50:
        scores[CyclePhase.RECESSION] += 2.5
        supporting[CyclePhase.RECESSION].append("PMI en contracción (<50)")
    if gdp_growth < 0:
        scores[CyclePhase.RECESSION] += 3
        supporting[CyclePhase.RECESSION].append("PIB negativo")
    if curve < -0.5:
        scores[CyclePhase.RECESSION] += 2
        supporting[CyclePhase.RECESSION].append("Curva de tipos invertida fuertemente")
    if unemp_chg > 0.3:
        scores[CyclePhase.RECESSION] += 2
        supporting[CyclePhase.RECESSION].append("Desempleo subiendo")
    if credit_trend == "widening":
        scores[CyclePhase.RECESSION] += 1.5
        supporting[CyclePhase.RECESSION].append("Spreads crédito ampliándose")
    if leading == "defensive":
        scores[CyclePhase.RECESSION] += 1
        supporting[CyclePhase.RECESSION].append("Sectores defensivos liderando")

    # ── Selección de fase ganadora ──
    total_signals = sum(scores.values())
    if total_signals == 0:
        return CycleDetection(phase=CyclePhase.UNDEFINED, confidence=0)

    best_phase = max(scores, key=scores.get)
    best_score = scores[best_phase]
    confidence = round((best_score / (total_signals + 1e-9)) * 100, 1)

    # Si la confianza es muy baja, marcar como indefinido
    if confidence < 30:
        return CycleDetection(phase=CyclePhase.UNDEFINED, confidence=confidence)

    # Señales en contra = las de las otras fases con score > 0
    signals_against = []
    for phase, sigs in supporting.items():
        if phase != best_phase and sigs:
            signals_against.extend([f"[{phase.value}] {s}" for s in sigs])

    return CycleDetection(
        phase=best_phase,
        confidence=confidence,
        signals_supporting=supporting[best_phase],
        signals_against=signals_against[:5],  # máx 5 señales en contra
    )

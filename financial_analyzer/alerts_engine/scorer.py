"""
Scorer unificado: combina régimen macro + fundamentales + técnico → 0-100.

Pesos:
  Régimen macro    0-25 pts  (contexto global: Risk-On/Off)
  Fundamentales    0-40 pts  (calidad del negocio)
  Técnico          0-35 pts  (timing y setup de entrada)
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UnifiedScore:
    ticker: str
    macro_pts: float      # 0-25
    fund_pts: float       # 0-40
    tech_pts: float       # 0-35
    regime: str
    fund_score: float     # 0-100 del scorer fundamental original
    tech_features: dict

    @property
    def total(self) -> float:
        return round(min(self.macro_pts + self.fund_pts + self.tech_pts, 100.0), 1)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "total": self.total,
            "macro_pts": round(self.macro_pts, 1),
            "fund_pts": round(self.fund_pts, 1),
            "tech_pts": round(self.tech_pts, 1),
            "regime": self.regime,
            "fund_score": round(self.fund_score, 1),
            **{f"tech_{k}": v for k, v in self.tech_features.items() if k != "ticker"},
        }


def _score_technical(tech: dict) -> float:
    """Calcula 0-35 puntos de la componente técnica."""
    pts = 0.0

    rsi = tech.get("rsi")
    vs200 = tech.get("vs_sma200_pct")
    vs50 = tech.get("vs_sma50_pct")
    vol_ratio = tech.get("volume_ratio")
    roc_20 = tech.get("roc_20d")

    # RSI (0-12 pts): favorece zonas de posible rebote o momentum sano
    if rsi is not None:
        if rsi < 30:       pts += 12   # muy sobrevendido — alta probabilidad de rebote
        elif rsi < 40:     pts += 10
        elif rsi < 50:     pts += 7
        elif rsi < 60:     pts += 8    # momentum sano, tendencia alcista controlada
        elif rsi < 70:     pts += 5
        else:              pts += 1    # sobrecomprado — menor margen de seguridad

    # Tendencia de SMAs (0-15 pts)
    if vs200 is not None and vs50 is not None:
        if vs200 > 0 and vs50 > 0:
            pts += 15   # precio > SMA50 > SMA200 — tendencia alcista sólida
        elif vs200 > 0:
            pts += 8    # sobre SMA200 pero bajo SMA50 — recuperando fuerza
        elif vs200 > -8:
            pts += 5    # cerca de SMA200 — posible soporte clave
        else:
            pts += 2    # tendencia dañada
    elif vs50 is not None:
        pts += 8 if vs50 > 0 else 3

    # Volumen (0-5 pts): volumen elevado confirma el movimiento
    if vol_ratio is not None:
        if vol_ratio > 2.0:    pts += 5
        elif vol_ratio > 1.5:  pts += 3
        elif vol_ratio > 1.0:  pts += 1

    # Momentum 20d (0-3 pts)
    if roc_20 is not None:
        if roc_20 > 5:     pts += 3
        elif roc_20 > 0:   pts += 2
        elif roc_20 > -5:  pts += 1

    return min(pts, 35.0)


def compute_unified_score(
    ticker: str,
    regime_score,          # RegimeScore | None
    fund_score_obj,        # FundamentalScore | None
    tech_features: dict,
) -> UnifiedScore:
    """
    Combina las tres componentes en un score unificado 0-100.

    Args:
        regime_score:   RegimeScore de engine.regime_engine (puede ser None si la DB no existe)
        fund_score_obj: FundamentalScore de fundamentals.scorer
        tech_features:  dict de alerts_engine.technical.get_technical_features
    """
    # Componente macro (0-25 pts)
    regime = regime_score.regime if regime_score else "NEUTRAL"
    macro_pts = {"RISK-ON": 25.0, "NEUTRAL": 15.0, "RISK-OFF": 5.0}.get(regime, 15.0)

    # Componente fundamental (0-40 pts): normaliza el score 0-100 al rango 0-40
    fund_raw = fund_score_obj.total if fund_score_obj else 50.0
    fund_pts = (fund_raw / 100.0) * 40.0

    # Componente técnica (0-35 pts)
    tech_pts = _score_technical(tech_features) if tech_features else 0.0

    return UnifiedScore(
        ticker=ticker,
        macro_pts=macro_pts,
        fund_pts=fund_pts,
        tech_pts=tech_pts,
        regime=regime,
        fund_score=fund_raw,
        tech_features=tech_features or {},
    )

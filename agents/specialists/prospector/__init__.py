from .prospector_agent import ProspectorAgent
from .models import Business, ProspectorResult, PainPoint, Resena, ChecklistWeb
from .pricing import PricingCalculator, ServicioRecomendado, ROI, PerdidaDolor, CATALOGO
from .scorecard import (
    Scorecard, Dimension, WinProbability,
    construir_scorecard, calcular_win_probability, aplicar_benchmark,
)
from .techstack import detectar_tech_stack, resumen_oportunidad_tech
from .pagespeed import PageSpeedAnalyzer, PageSpeedResult
from .competitive import analisis_competitivo, aplicar_competitivo
from .crm import CRM, ESTADOS, ESTADO_COLORS

__all__ = [
    "ProspectorAgent",
    "Business",
    "ProspectorResult",
    "PainPoint",
    "Resena",
    "ChecklistWeb",
    "PricingCalculator",
    "ServicioRecomendado",
    "ROI",
    "PerdidaDolor",
    "CATALOGO",
    "Scorecard",
    "Dimension",
    "WinProbability",
    "construir_scorecard",
    "calcular_win_probability",
    "aplicar_benchmark",
    "detectar_tech_stack",
    "resumen_oportunidad_tech",
    "PageSpeedAnalyzer",
    "PageSpeedResult",
    "analisis_competitivo",
    "aplicar_competitivo",
    "CRM",
    "ESTADOS",
    "ESTADO_COLORS",
]

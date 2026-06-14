from .prospector_agent import ProspectorAgent
from .models import Business, ProspectorResult, PainPoint, Resena, ChecklistWeb
from .pricing import (
    PricingCalculator, ServicioRecomendado, ROI, PerdidaDolor, CATALOGO,
    Paquete, PaqueteCotizado, PAQUETES,
)
from .scorecard import (
    Scorecard, Dimension, WinProbability,
    construir_scorecard, calcular_win_probability, aplicar_benchmark,
)
from .techstack import detectar_tech_stack, resumen_oportunidad_tech
from .pagespeed import PageSpeedAnalyzer, PageSpeedResult
from .competitive import analisis_competitivo, aplicar_competitivo
from .automation import analizar_automatizacion, PerfilAutomatizacion
from .report import generar_informe_html
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
    "Paquete",
    "PaqueteCotizado",
    "PAQUETES",
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
    "analizar_automatizacion",
    "PerfilAutomatizacion",
    "generar_informe_html",
    "CRM",
    "ESTADOS",
    "ESTADO_COLORS",
]

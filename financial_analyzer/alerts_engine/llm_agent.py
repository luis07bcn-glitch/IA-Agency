"""
Agente LLM (Claude) que genera análisis explicativo para oportunidades detectadas.
Solo se invoca cuando el score unificado supera el umbral — controla el coste de API.
"""
import os
import json
import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada en .env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate_analysis(unified_score, regime_score, company_name: str = "") -> dict:
    """
    Llama a Claude con el contexto completo del ticker y devuelve un dict JSON.

    Returns:
        dict con keys: analisis, sesgo, catalizadores, riesgos, niveles, confianza_llm
    """
    t = unified_score
    name_str = f"({company_name})" if company_name else ""

    warnings_str = (
        "\n".join(f"  ⚠ {w}" for w in (regime_score.warnings or []))
        if regime_score
        else "  Sin datos de régimen macro"
    )

    prompt = f"""Eres un analista senior de mercados financieros con 20 años de experiencia en análisis cuantitativo y fundamental.

Analiza la siguiente oportunidad detectada por nuestro sistema de alertas IA y genera un informe objetivo.

═══ TICKER: {t.ticker} {name_str} ═══

CONTEXTO MACRO (Régimen de mercado):
  Régimen actual: {t.regime}
  Score macro: {regime_score.total if regime_score else 'N/A'}/100
  Alertas críticas del régimen:
{warnings_str}

ANÁLISIS FUNDAMENTAL (Score propio: {t.fund_score:.0f}/100):
  Score calculado internamente con datos de yfinance: rentabilidad, crecimiento, balance, cashflow y valoración.

INDICADORES TÉCNICOS:
  Precio actual: {t.tech_features.get('price', 'N/A')}
  RSI(14): {t.tech_features.get('rsi', 'N/A')}
  Precio vs SMA50: {t.tech_features.get('vs_sma50_pct', 'N/A')}%
  Precio vs SMA200: {t.tech_features.get('vs_sma200_pct', 'N/A')}%
  Ratio de volumen (vs media 20d): {t.tech_features.get('volume_ratio', 'N/A')}x
  Momentum 20d: {t.tech_features.get('roc_20d', 'N/A')}%
  Momentum 5d: {t.tech_features.get('roc_5d', 'N/A')}%

SCORING UNIFICADO DEL SISTEMA: {t.total}/100
  - Componente macro: {t.macro_pts:.0f}/25
  - Componente fundamental: {t.fund_pts:.0f}/40
  - Componente técnica: {t.tech_pts:.0f}/35

════════════════════════════════════

Instrucciones:
1. Evalúa si existe una oportunidad real o si el sistema puede estar generando un falso positivo.
2. Integra las tres dimensiones (macro + fundamental + técnico) en tu análisis.
3. Identifica el tipo de setup: dip buying, momentum, breakout, rotación sectorial, etc.
4. Sugiere niveles orientativos de entrada, stop y objetivo basándote en los datos técnicos.
5. Sé directo, concreto y equilibrado. No seas ni demasiado optimista ni pesimista.

Responde SOLO con un JSON válido con esta estructura exacta (sin markdown, sin texto antes o después del JSON):
{{
  "analisis": "explicación de 5-7 frases integrando macro + fundamental + técnico",
  "sesgo": "ALCISTA",
  "catalizadores": ["catalizador 1", "catalizador 2", "catalizador 3"],
  "riesgos": ["riesgo 1", "riesgo 2"],
  "niveles": {{
    "entrada": <número o null>,
    "stop": <número o null>,
    "target1": <número o null>,
    "horizonte": "corto plazo (1-4 semanas)"
  }},
  "confianza_llm": <número 0-100>
}}

El campo "sesgo" debe ser exactamente uno de: "ALCISTA", "BAJISTA" o "NEUTRO"."""

    _fallback = {
        "analisis": "Error al generar análisis.",
        "sesgo": "NEUTRO",
        "catalizadores": [],
        "riesgos": ["Error en el agente LLM"],
        "niveles": {"entrada": None, "stop": None, "target1": None, "horizonte": None},
        "confianza_llm": 0,
    }

    try:
        client = _get_client()
        model = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-6")

        message = client.messages.create(
            model=model,
            max_tokens=900,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()

        # Limpiar posibles bloques de código markdown
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        _fallback["analisis"] = f"Error de parseo JSON en respuesta de Claude: {e}"
        return _fallback
    except Exception as e:
        _fallback["analisis"] = f"Error llamando a Claude: {e}"
        _fallback["riesgos"] = [str(e)]
        return _fallback

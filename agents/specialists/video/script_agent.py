import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from anthropic import Anthropic
from config import settings

# ── Nicho → configuración ────────────────────────────────────────────────────

NICHE_CONFIG = {
    "biohacking": {
        "tone": "científico pero cercano, como un amigo médico que te explica algo fascinante",
        "hook_style": "dato científico contraintuitivo o estudio sorprendente",
        "cta_style": "invitar a probar el protocolo descrito y suscribirse para más hacks",
        "voice_pace": "moderada con pausas dramáticas en los datos clave",
        "examples": ["optimizar el sueño", "ayuno intermitente", "suplementación", "frío terapéutico"],
    },
    "finanzas": {
        "tone": "autoridad accesible, directo, sin jerga innecesaria",
        "hook_style": "error financiero común que la mayoría comete sin saberlo",
        "cta_style": "descargar checklist / suscribirse para la estrategia completa",
        "voice_pace": "media-alta, con énfasis en los números clave",
        "examples": ["inversión para principiantes", "libertad financiera", "errores de dinero"],
    },
    "motivacion": {
        "tone": "enérgico, empático, como un mentor que cree en ti",
        "hook_style": "pregunta que golpea una inseguridad real de la audiencia",
        "cta_style": "comprometerse con una acción concreta hoy y compartir",
        "voice_pace": "dinámica, variable, con subidas de energía en los puntos clave",
        "examples": ["superar el miedo al fracaso", "hábitos de éxito", "mentalidad ganadora"],
    },
    "tecnologia": {
        "tone": "experto entusiasta, curioso, sin ser condescendiente",
        "hook_style": "tecnología que ya está cambiando el mundo sin que lo sepas",
        "cta_style": "explorar la tecnología mencionada y suscribirse para seguir al día",
        "voice_pace": "media, clara, con ejemplos concretos",
        "examples": ["IA en 2025", "gadgets ocultos", "herramientas de productividad"],
    },
    "curiosidades": {
        "tone": "fascinante y ligero, como contarle algo increíble a un amigo",
        "hook_style": "hecho que desafía la lógica o la historia oficial",
        "cta_style": "comentar cuál fue el dato más sorprendente y suscribirse",
        "voice_pace": "rápida en la intro, moderada en el desarrollo",
        "examples": ["misterios históricos", "ciencia extraña", "récords mundiales"],
    },
}

SYSTEM_PROMPT = """Eres VideoScriptAgent, especialista en guiones para YouTube y TikTok que generan alta retención y monetización.

Conoces en profundidad:
- Psicología del espectador digital y patrones de abandono
- Técnicas de copywriting persuasivo (PAS, AIDA, storytelling)
- SEO para YouTube: títulos, descripciones y tags de alta conversión
- Formato óptimo para cada plataforma (YouTube largo vs TikTok corto)
- Cómo estructurar contenido para pasar los filtros algorítmicos

Tu salida es SIEMPRE un JSON válido con la estructura exacta que se te indique. Sin texto fuera del JSON."""


# ── Modelos de datos ─────────────────────────────────────────────────────────

@dataclass
class ScriptSection:
    section_id: int
    title: str
    duration_seconds: int
    narration: str
    visual_keywords: list[str]
    re_hook: Optional[str] = None   # frase de re-enganche al inicio de sección (cada ~2 min)


@dataclass
class VideoScript:
    topic: str
    niche: str
    platform: str                   # "youtube" | "tiktok" | "both"
    total_duration_seconds: int
    youtube_title: str
    youtube_description: str
    youtube_tags: list[str]
    tiktok_caption: str
    thumbnail_concept: str          # descripción visual del thumbnail
    hook: str                       # primeros 3-15 segundos
    sections: list[ScriptSection]
    outro: str                      # CTA final
    target_audience: str
    estimated_cpm_range: str

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def total_words(self) -> int:
        words = len(self.hook.split()) + len(self.outro.split())
        for s in self.sections:
            words += len(s.narration.split())
        return words

    def full_narration(self) -> str:
        parts = [self.hook]
        for s in self.sections:
            if s.re_hook:
                parts.append(s.re_hook)
            parts.append(s.narration)
        parts.append(self.outro)
        return "\n\n".join(parts)


# ── Agente ───────────────────────────────────────────────────────────────────

class ScriptAgent:
    name = "ScriptAgent"
    description = "Genera guiones estructurados para videos de 1–20 min optimizados para YouTube y TikTok"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        topic: str,
        niche: str = "biohacking",
        duration_minutes: int = 10,
        platform: str = "both",
        language: str = "es",
        brief: dict = None,
    ) -> VideoScript:
        """Genera un VideoScript completo listo para producción.

        Args:
            topic: Tema del video, ej: "Los 5 hacks de sueño que usan los CEOs"
            niche: biohacking | finanzas | motivacion | tecnologia | curiosidades
            duration_minutes: Duración objetivo en minutos (1–20)
            platform: youtube | tiktok | both
            language: Código de idioma, ej: "es", "en"
            brief: dict opcional con directrices creativas del usuario:
                - key_points: list[str]  — puntos obligatorios a incluir
                - reference_text: str    — texto de papers/artículos a citar
                - visual_cues: dict      — {"tema": "pexels search query"}
                - avoid: list[str]       — temas a evitar
                - tone_notes: str        — notas de tono extra
        """
        niche = niche.lower().strip()
        cfg = NICHE_CONFIG.get(niche, NICHE_CONFIG["biohacking"])

        n_sections, section_duration = self._calc_structure(duration_minutes)
        prompt = self._build_prompt(topic, niche, cfg, duration_minutes, n_sections, section_duration, platform, language, brief)

        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # Extraer JSON si viene envuelto en ```json ... ```
        if "```" in raw:
            raw = raw.split("```json")[-1].split("```")[0].strip()

        data = json.loads(raw)
        return self._parse_response(data, topic, niche, platform)

    def generate_tiktok_short(self, topic: str, niche: str = "curiosidades") -> VideoScript:
        """Atajo para videos cortos de TikTok (30-90 segundos)."""
        return self.run(topic, niche=niche, duration_minutes=1, platform="tiktok")

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _calc_structure(self, duration_minutes: int) -> tuple[int, int]:
        """Devuelve (n_secciones, segundos_por_sección)."""
        total_seconds = duration_minutes * 60
        # Hook (~15s) + Outro (~30s) → resto para secciones
        content_seconds = total_seconds - 45
        if duration_minutes <= 1:
            return 2, content_seconds // 2
        elif duration_minutes <= 3:
            return 3, content_seconds // 3
        elif duration_minutes <= 7:
            return 4, content_seconds // 4
        else:
            return 5, content_seconds // 5

    def _build_brief_section(self, brief: dict) -> str:
        """Convierte el dict de brief en texto para inyectar en el prompt."""
        if not brief:
            return ""
        lines = ["\n── DIRECTRICES DEL CREADOR (OBLIGATORIO CUMPLIR) ──────────────────────────"]

        if brief.get("key_points"):
            lines.append("\nPUNTOS CLAVE OBLIGATORIOS A INCLUIR (distribúyelos a lo largo del guión):")
            for pt in brief["key_points"]:
                lines.append(f"  • {pt}")

        if brief.get("reference_text"):
            text = brief["reference_text"][:8000]
            lines.append(f"\nMATERIAL DE REFERENCIA (cita datos exactos, estudios o afirmaciones de aquí — prioridad sobre tu conocimiento general):\n{text}")

        if brief.get("avoid"):
            avoid = brief["avoid"] if isinstance(brief["avoid"], list) else [brief["avoid"]]
            lines.append(f"\nTEMAS A EVITAR: {', '.join(avoid)}")

        if brief.get("tone_notes"):
            lines.append(f"\nNOTAS DE TONO: {brief['tone_notes']}")

        if brief.get("visual_cues"):
            lines.append("\nPISTAS VISUALES (usa estas búsquedas en visual_keywords cuando el tema aparezca):")
            for trigger, query in brief["visual_cues"].items():
                lines.append(f"  • Cuando menciones '{trigger}' → visual_keywords debe incluir: \"{query}\"")

        lines.append("────────────────────────────────────────────────────────────────────────────\n")
        return "\n".join(lines)

    def _build_prompt(self, topic, niche, cfg, duration_minutes, n_sections, section_duration, platform, language, brief=None) -> str:
        lang_instruction = "en español neutro latino (válido para España y LATAM)" if language == "es" else f"in {language}"

        platform_notes = {
            "youtube": "Optimizado para YouTube: título SEO largo (60 chars), descripción de 300+ palabras, 15+ tags.",
            "tiktok": "Optimizado para TikTok: caption de máx 150 chars con 3-5 hashtags trending, gancho visual en primeros 2s.",
            "both": "Optimizado para ambas plataformas: versión YouTube con SEO completo + versión TikTok de la sección más viral.",
        }.get(platform, "")

        brief_block = self._build_brief_section(brief)

        return f"""Genera un guión de video completo para el siguiente tema.

TEMA: {topic}
NICHO: {niche}
DURACIÓN OBJETIVO: {duration_minutes} minutos
PLATAFORMA: {platform}
IDIOMA: {lang_instruction}

CONFIGURACIÓN DEL NICHO:
- Tono: {cfg['tone']}
- Estilo del hook: {cfg['hook_style']}
- Estilo del CTA: {cfg['cta_style']}
- Ritmo de voz: {cfg['voice_pace']}

ESTRUCTURA REQUERIDA: {n_sections} secciones de ~{section_duration} segundos cada una.
{platform_notes}
{brief_block}

REGLAS ALGORÍTMICAS OBLIGATORIAS:
1. El hook (primeros 15s) debe generar una pregunta en la mente del espectador que solo se responde viendo todo el video
2. Cada sección de más de 2 minutos debe empezar con un re_hook que reactive la atención
3. Cambiar el ritmo narrativo cada 60-90 segundos (dato → historia → pregunta → solución)
4. El CTA final debe ser específico (una acción concreta), no genérico
5. Los visual_keywords deben ser términos en INGLÉS aptos para buscar en Pexels/Pixabay (imágenes libres de derechos)

Devuelve ÚNICAMENTE este JSON (sin texto adicional):

{{
  "youtube_title": "título SEO atractivo de 50-60 caracteres",
  "youtube_description": "descripción YouTube de 300+ palabras con palabras clave naturales",
  "youtube_tags": ["tag1", "tag2", ...],
  "tiktok_caption": "caption TikTok ≤150 chars con hashtags",
  "thumbnail_concept": "descripción visual del thumbnail: elementos, texto, colores, emoción",
  "target_audience": "descripción del espectador ideal",
  "estimated_cpm_range": "rango CPM estimado en dólares",
  "hook": "texto narrado de los primeros 15 segundos — directo, potente, sin presentaciones",
  "sections": [
    {{
      "section_id": 1,
      "title": "título interno de la sección",
      "duration_seconds": {section_duration},
      "narration": "texto completo a narrar en esta sección",
      "visual_keywords": ["keyword1", "keyword2", "keyword3"],
      "re_hook": "frase de re-enganche (solo si la sección empieza después del minuto 2, si no: null)"
    }}
  ],
  "outro": "texto del CTA final de 20-30 segundos"
}}"""

    def _parse_response(self, data: dict, topic: str, niche: str, platform: str) -> VideoScript:
        sections = [
            ScriptSection(
                section_id=s["section_id"],
                title=s["title"],
                duration_seconds=s["duration_seconds"],
                narration=s["narration"],
                visual_keywords=s["visual_keywords"],
                re_hook=s.get("re_hook"),
            )
            for s in data["sections"]
        ]

        total = sum(s.duration_seconds for s in sections) + 45  # hook(15) + outro(30)

        return VideoScript(
            topic=topic,
            niche=niche,
            platform=platform,
            total_duration_seconds=total,
            youtube_title=data["youtube_title"],
            youtube_description=data["youtube_description"],
            youtube_tags=data["youtube_tags"],
            tiktok_caption=data["tiktok_caption"],
            thumbnail_concept=data["thumbnail_concept"],
            hook=data["hook"],
            sections=sections,
            outro=data["outro"],
            target_audience=data["target_audience"],
            estimated_cpm_range=data["estimated_cpm_range"],
        )

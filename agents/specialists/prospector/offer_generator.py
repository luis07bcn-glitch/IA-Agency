"""
Genera outreach hiper-personalizado usando copywriting emocional.
Principio clave: el cliente debe sentir que ya sabemos exactamente qué le duele
y que tenemos la solución, antes de que leamos el segundo párrafo.

Frameworks usados:
- PAS (Problem → Agitate → Solution): nombrar el dolor, amplificarlo con coste real, ofrecer la solución
- Evidence-first: empezar con datos reales suyos (su reseña, su web, su rating)
- Competitor mirror: "tu competidor ya tiene X, tú no"
- Low-risk CTA: pedir solo 15 minutos, sin compromiso
"""
from typing import List, Optional, Tuple
import anthropic

from .models import Business, PainPoint, Resena


class OfferGenerator:
    def __init__(self, client: anthropic.Anthropic, nombre_agencia: str = "MerakIA"):
        self.client = client
        self.nombre_agencia = nombre_agencia

    # ── Email principal ────────────────────────────────────────────────────────

    def generar_email(
        self,
        business: Business,
        pains: List[PainPoint],
        resenas_negativas: List[Resena],
        nombre_destinatario: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Devuelve (asunto, cuerpo).
        El email usa evidencias reales del análisis para hacer la oferta irresistible.
        """
        nombre = nombre_destinatario or f"responsable de {business.nombre}"
        contexto = self._contexto_outreach(business, pains, resenas_negativas)

        prompt = f"""Eres un copywriter experto en prospección B2B para agencias de marketing digital.
Escribes emails que generan respuesta porque van directamente al dolor real del negocio.

DATOS DEL PROSPECTO:
{contexto}

REGLAS ESTRICTAS PARA EL EMAIL:
1. Primera frase: prueba de que analizaste su negocio ESPECÍFICAMENTE (cita algo real y concreto)
2. Segunda parte: cuantifica el coste del dolor en euros/clientes perdidos (usa estimaciones realistas del sector)
3. Tercera parte: ofrece resolver UN problema concreto, no "todo lo digital"
4. Menciona al menos UNA cita textual de sus reseñas negativas si las hay (entre comillas, con el número de estrella)
5. Si tienen competidores con ventaja, mencionarlo crea urgencia
6. CTA único: solo pedir 15 minutos esta semana, sin compromiso
7. P.D.: añade algo que aumente la urgencia o la prueba social
8. Máximo 200 palabras en el cuerpo
9. Tono: directo, de igual a igual, cercano pero profesional
10. PROHIBIDO empezar con "Espero que estés bien" o frases genéricas

FORMATO DE RESPUESTA (exactamente así, con los separadores):
ASUNTO: [asunto impactante, máx 65 chars, que genere curiosidad o urgencia, específico para este negocio]
---
Hola {nombre},

[Cuerpo del email — máx 200 palabras]

Un saludo,
[Tu nombre]
{self.nombre_agencia}

P.D. [Una línea de urgencia o prueba social específica para este negocio]"""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1800,
            messages=[{"role": "user", "content": prompt}],
        )

        texto = msg.content[0].text.strip()
        return self._parsear_email(texto, business)

    # ── WhatsApp ───────────────────────────────────────────────────────────────

    def generar_whatsapp(
        self,
        business: Business,
        pains: List[PainPoint],
        resenas_negativas: List[Resena],
    ) -> str:
        """Mensaje de WhatsApp corto, directo y con hook emocional fuerte."""
        pain_principal = pains[0] if pains else None
        cita = next(
            (r.texto[:120] for r in resenas_negativas if r.texto),
            None
        )

        prompt = f"""Escribe un mensaje de WhatsApp de prospección para este negocio local.

NEGOCIO: {business.nombre} ({business.tipo}) en {business.ciudad}
DOLOR PRINCIPAL: {pain_principal.descripcion if pain_principal else "falta de presencia digital"}
EVIDENCIA REAL: {f'Reseña reciente: "{cita}..."' if cita else f'Rating de {business.rating}/5 en Google con {business.total_resenas} reseñas'}
{'SIN WEB PROPIA' if not business.tiene_web else f'Web: {business.web}'}
AGENCIA: {self.nombre_agencia}

REGLAS:
- Máximo 6 líneas en total
- Primera línea: hook que mencione algo específico de su negocio que descubriste
- Segunda línea: el coste real del problema (en clientes o euros que pierde)
- Tercera-cuarta: lo que podemos hacer en concreto
- Última: CTA simple (¿15 min esta semana?)
- Máximo 2 emojis, bien colocados
- Sin saludos formales, directo al grano
- Habla de lo que PIERDEN, no de lo que vendemos

Solo el mensaje, sin explicaciones ni etiquetas."""

        msg = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Script de llamada ──────────────────────────────────────────────────────

    def generar_script_llamada(
        self,
        business: Business,
        pains: List[PainPoint],
        resenas_negativas: List[Resena],
    ) -> str:
        """Guión de cold call con apertura, cualificación, propuesta y objeciones."""
        pain_top = pains[0] if pains else None
        cita = next((r.texto[:150] for r in resenas_negativas if r.texto), None)

        prompt = f"""Genera un guión de cold call para prospectar este negocio.

NEGOCIO: {business.nombre} — {business.tipo} en {business.ciudad}
DOLOR DETECTADO: {pain_top.descripcion if pain_top else "problemas de presencia digital"}
EVIDENCIA: {f'Reseña real: "{cita}"' if cita else f'Análisis de su perfil online (rating {business.rating}/5)'}
{'⚠️ SIN WEB PROPIA' if not business.tiene_web else ''}
AGENCIA: {self.nombre_agencia}

ESTRUCTURA DEL GUIÓN (con tiempos orientativos):
1. APERTURA (0-10 seg): Presentación + prueba de investigación específica
2. GANCHO (10-30 seg): El problema que encontramos y cuánto les cuesta
3. CUALIFICACIÓN (30-60 seg): 2 preguntas para confirmar que el dolor es real
4. PROPUESTA (60-80 seg): Solución concreta en una frase, resultado esperado
5. CIERRE (80-90 seg): Pedir la reunión de 20 minutos

OBJECIONES FRECUENTES + RESPUESTA:
- "No me interesa"
- "Ya tenemos alguien para eso"
- "Ahora no es buen momento"
- "¿Cuánto cuesta?"

Tono: natural, conversacional, como si fuera una conversación entre conocidos del sector."""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Propuesta PDF (texto estructurado) ────────────────────────────────────

    def generar_propuesta_texto(
        self,
        business: Business,
        pains: List[PainPoint],
        resumen_oportunidad: str,
    ) -> str:
        """Genera el texto de una propuesta de servicios estructurada."""
        pain_list = "\n".join(
            f"  {i+1}. {p.descripcion} → {p.servicio}"
            for i, p in enumerate(pains[:5])
        )

        prompt = f"""Genera una propuesta de servicios profesional para este negocio.

NEGOCIO: {business.nombre} ({business.tipo}) en {business.ciudad}
ANÁLISIS: {resumen_oportunidad}
PROBLEMAS DETECTADOS Y SOLUCIONES:
{pain_list}
AGENCIA: {self.nombre_agencia}

ESTRUCTURA:
1. Diagnóstico (2-3 párrafos): qué encontramos, qué significa en términos de pérdida
2. Soluciones propuestas (lista detallada con descripción y beneficio medible de cada una)
3. Cómo trabajamos (3 pasos simples)
4. Inversión estimada (rangos generales, no precios exactos)
5. ROI proyectado (conservador, con datos del sector)
6. Próximos pasos (una sola acción clara)

Tono: consultivo, datos > opiniones, hablar de resultados concretos."""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Demo "caballo de Troya" ────────────────────────────────────────────────

    def generar_demo_prompt(
        self,
        business: Business,
        pains: List[PainPoint],
        tipo_demo: str = "WhatsApp",
        objetivo: str = "agendar citas",
    ) -> str:
        """
        Genera el PROMPT listo para montar un agente demo del negocio
        (caballo de Troya): un agente IA de WhatsApp/voz/chat que atiende como
        si fuera el propio negocio. Llegar a la reunión con la demo funcionando
        es lo que más cierra. Usa los datos reales ya scrapeados del negocio.
        """
        pain_top = pains[0] if pains else None
        prompt = f"""Genera un PROMPT DE SISTEMA completo y listo para copiar/pegar
en una plataforma de agentes IA (tipo SignalCore, Voiceflow, un GPT, etc.),
para crear un agente DEMO que atienda como si fuera este negocio real.

NEGOCIO: {business.nombre} — {business.tipo} en {business.ciudad}
{f'WEB: {business.web}' if business.web else 'SIN WEB (el agente es su única presencia digital)'}
{f'TELÉFONO: {business.telefono}' if business.telefono else ''}
CANAL DE LA DEMO: {tipo_demo}
OBJETIVO PRINCIPAL DEL AGENTE: {objetivo}
DOLOR QUE RESUELVE LA DEMO: {pain_top.descripcion if pain_top else 'atención inmediata 24/7'}

El prompt de sistema que generes debe incluir:
1. ROL e identidad del agente (habla EN NOMBRE de {business.nombre}, tono acorde al sector)
2. Objetivo de negocio (cualificar y {objetivo}) y qué datos pedir al cliente
3. Conocimiento base realista del sector {business.tipo} (servicios típicos, horarios ejemplo, FAQs)
4. Flujo de conversación paso a paso hasta lograr el objetivo
5. Reglas de estilo (mensajes cortos, cercano, sin tecnicismos, máximo X líneas)
6. Manejo de objeciones y derivación a humano cuando proceda
7. Una conversación de EJEMPLO (cliente ↔ agente) que demuestre el valor

Devuelve SOLO el prompt de sistema, formateado y listo para usar."""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Prompt de Landing Page ─────────────────────────────────────────────────

    def generar_landing_prompt(
        self,
        business: Business,
        pains: List[PainPoint],
        propuesta_valor: str = "",
    ) -> str:
        """
        Genera el prompt para construir una landing de alta conversión para el
        negocio (usable en Base44, Framer, Lovable, v0, Claude, etc.).
        """
        problemas = "\n".join(f"  - {p.descripcion} (→ {p.servicio})" for p in pains[:4])
        prompt = f"""Genera un PROMPT completo para construir una LANDING PAGE de alta
conversión para este negocio, listo para pegar en un constructor con IA
(Base44 / Framer / Lovable / v0).

NEGOCIO: {business.nombre} — {business.tipo} en {business.ciudad}
{f'WEB ACTUAL: {business.web}' if business.web else 'NO TIENE WEB — esta sería su primera'}
RATING: {business.rating}/5 ({business.total_resenas} reseñas)
{f'PROPUESTA DE VALOR: {propuesta_valor}' if propuesta_valor else ''}
PROBLEMAS A RESOLVER CON LA LANDING:
{problemas or '  - Presencia profesional y captación de clientes'}

El prompt que generes debe especificar:
1. Estructura de secciones (hero, beneficios, prueba social, servicios, CTA, contacto)
2. Copy concreto y persuasivo para cada sección (titulares, subtítulos, CTAs) — en español
3. Estrategia de conversión (formulario/WhatsApp/reserva visible, urgencia, confianza)
4. Estilo visual sugerido acorde al sector {business.tipo} (paleta, tono, imágenes)
5. Elementos de confianza (reseñas reales, valoración Google, garantías)
6. SEO local básico (título, meta, palabras clave de {business.ciudad})

Devuelve SOLO el prompt, estructurado y listo para usar."""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Prompt de Presentación (Gamma) ─────────────────────────────────────────

    def generar_presentacion_prompt(
        self,
        business: Business,
        pains: List[PainPoint],
        resumen_oportunidad: str,
        roi_resumen: str = "",
    ) -> str:
        """
        Genera el prompt para crear una presentación profesional persuasiva
        (Gamma / Tome / Beautiful.ai) lista para la reunión con el cliente.
        Combina diagnóstico + dolores + solución + ROI.
        """
        problemas = "\n".join(f"  {i+1}. {p.descripcion} → {p.servicio}" for i, p in enumerate(pains[:4]))
        prompt = f"""Genera un PROMPT completo para Gamma (IA que crea presentaciones)
que produzca una presentación profesional y persuasiva para vender nuestros
servicios a este cliente en una reunión.

AGENCIA: {self.nombre_agencia}
CLIENTE: {business.nombre} — {business.tipo} en {business.ciudad}
DIAGNÓSTICO: {resumen_oportunidad}
DOLORES Y SOLUCIONES:
{problemas}
{f'ROI PROYECTADO: {roi_resumen}' if roi_resumen else ''}

El prompt para Gamma debe pedir una presentación con estas diapositivas:
1. Portada (nombre del cliente + "Diagnóstico digital por {self.nombre_agencia}")
2. "Qué hemos encontrado" (el diagnóstico, con datos reales)
3. "Lo que te está costando" (el dolor traducido a euros/clientes perdidos)
4. "La solución" (servicios propuestos, uno por bloque, con beneficio medible)
5. "Resultados esperados" (la tabla/numero de ROI, antes vs después)
6. "Cómo trabajamos" (3 pasos simples)
7. "Siguiente paso" (CTA único: arrancar con una acción concreta)

Indica también tono (consultivo, datos > opiniones) y estilo visual profesional.
Devuelve SOLO el prompt para Gamma, listo para pegar."""

        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    # ── Helpers ────────────────────────────────────────────────────────────────

    # ── Secuencia de seguimiento multicanal ────────────────────────────────────

    def generar_secuencia(
        self,
        business: Business,
        pains: List[PainPoint],
        resenas_negativas: List[Resena],
    ) -> List[dict]:
        """
        Genera una secuencia de seguimiento de 5 toques en 14 días (cadencia
        probada: aportar valor, no solo "¿lo viste?"). Devuelve una lista de
        toques: {dia, canal, titulo, mensaje}.
        """
        import json
        contexto = self._contexto_outreach(business, pains, resenas_negativas)
        prompt = f"""Eres un experto en ventas B2B para agencias que venden a negocios locales.
Diseña una SECUENCIA DE SEGUIMIENTO de 5 toques en 14 días para este prospecto,
tras un primer email ya enviado. Cada toque debe APORTAR VALOR (un dato, un
recurso, una prueba social, una pregunta concreta), nunca solo "¿lo viste?".

{contexto}
AGENCIA: {self.nombre_agencia}

Cadencia recomendada: Día 2 (WhatsApp breve), Día 4 (email con caso/valor),
Día 7 (llamada — guion), Día 10 (WhatsApp con prueba social), Día 14 (email de
ruptura educada que reactiva).

Responde ÚNICAMENTE con JSON válido, sin texto adicional:
{{"secuencia": [
  {{"dia": 2, "canal": "WhatsApp", "titulo": "...", "mensaje": "mensaje listo para copiar/pegar, en español, tono cercano"}}
]}}"""
        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("```"))
            data = json.loads(raw)
            toques = []
            for t in data.get("secuencia", []):
                toques.append({
                    "dia": int(t.get("dia", 0)),
                    "canal": t.get("canal", ""),
                    "titulo": t.get("titulo", ""),
                    "mensaje": t.get("mensaje", ""),
                })
            return toques
        except Exception:
            # Fallback mínimo si Claude falla
            return [
                {"dia": 2, "canal": "WhatsApp", "titulo": "Recordatorio con valor",
                 "mensaje": f"Hola, soy de {self.nombre_agencia}. Te envié un análisis de {business.nombre}. ¿Te paso el dato concreto que más te puede interesar?"},
                {"dia": 7, "canal": "Llamada", "titulo": "Llamada de seguimiento",
                 "mensaje": "Llamar para ofrecer 15 minutos sin compromiso y comentar el principal hallazgo."},
                {"dia": 14, "canal": "Email", "titulo": "Email de ruptura",
                 "mensaje": "Cierro el tema por mi parte, pero te dejo el diagnóstico por si lo quieres retomar más adelante."},
            ]

    def _contexto_outreach(
        self,
        business: Business,
        pains: List[PainPoint],
        resenas_negativas: List[Resena],
    ) -> str:
        lines = [
            f"Negocio: {business.nombre} ({business.tipo}) en {business.ciudad}",
            f"Rating Google: {business.rating}/5 con {business.total_resenas} reseñas totales",
        ]

        if not business.tiene_web:
            lines.append("⚠️ SIN SITIO WEB PROPIO — Solo perfil de Google Maps")
        else:
            lines.append(f"Web: {business.web}")

        if pains:
            lines.append("\nDolores detectados (mayor a menor urgencia):")
            for i, p in enumerate(pains[:3], 1):
                lines.append(f"  {i}. {p.descripcion}")
                lines.append(f"     → Evidencia: {p.evidencia}")
                lines.append(f"     → Solución: {p.servicio}")

        if resenas_negativas:
            lines.append("\nReseñas negativas para citar en el email:")
            for r in resenas_negativas[:2]:
                lines.append(f"  [{r.rating}★] \"{r.texto[:180]}\"")

        return "\n".join(lines)

    def _parsear_email(self, texto: str, business: Business) -> Tuple[str, str]:
        """Extrae asunto y cuerpo del texto generado por Claude."""
        if "ASUNTO:" in texto and "---" in texto:
            partes = texto.split("---", 1)
            asunto = partes[0].replace("ASUNTO:", "").strip()
            cuerpo = partes[1].strip()
        elif "ASUNTO:" in texto:
            lineas = texto.splitlines()
            asunto = ""
            cuerpo_lines = []
            encontrado = False
            for l in lineas:
                if l.startswith("ASUNTO:") and not encontrado:
                    asunto = l.replace("ASUNTO:", "").strip()
                    encontrado = True
                elif encontrado:
                    cuerpo_lines.append(l)
            cuerpo = "\n".join(cuerpo_lines).strip()
        else:
            asunto = f"Hemos analizado {business.nombre} — encontramos algo importante"
            cuerpo = texto

        return asunto, cuerpo

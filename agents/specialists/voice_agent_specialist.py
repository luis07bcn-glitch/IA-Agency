"""
Voice Agent Specialist.

Genera un system prompt optimizado para agentes de voz (Vapi.ai, Bland.ai, etc.):
- Respuestas cortas (max 2-3 frases, sin markdown)
- Flujo de recepción: saludar → identificar necesidad → recoger datos → confirmar
- Manejo de no-shows con recordatorios automáticos
- Escalado a humano para casos complejos

El output incluye el system prompt de voz + primer mensaje + mensaje de cierre.
"""
from anthropic import Anthropic
from config import settings

_SYSTEM = """Eres un especialista senior en agentes de voz con IA para negocios locales españoles.

Tu trabajo es crear el SYSTEM PROMPT completo para un agente de voz telefónico,
basado en la información real del negocio.

Un agente de voz es RADICALMENTE diferente a un chatbot de texto:
- Las respuestas deben ser MUY CORTAS (máximo 2-3 frases por turno)
- NADA de markdown, bullet points, asteriscos ni listas
- El agente habla en voz alta: nada de "consulta nuestra web" como respuesta principal
- Usa pausas naturales con comas y puntos
- El objetivo principal SIEMPRE es agendar la cita o tomar el recado

El resultado debe incluir estas secciones exactas:

## 1. SYSTEM PROMPT DEL AGENTE DE VOZ
Un bloque entre ``` ``` con el system prompt completo optimizado para voz. Debe incluir:
- Identidad del asistente (nombre, negocio al que pertenece)
- Tono y personalidad (cálido, profesional, eficiente)
- Flujo de llamada: saludo → detectar necesidad → recoger datos (nombre + teléfono + motivo) → confirmar cita o tomar nota
- Servicios principales con precios si se proporcionaron
- Horarios disponibles
- Cómo manejar cuando no hay huecos (ofrecer lista de espera, fecha alternativa)
- Cuándo escalar a humano: quejas, urgencias médicas, preguntas muy específicas
- Instrucción clave: si el usuario pide hablar con una persona, transfer inmediato sin debate
- Restricción de formato: NUNCA usar listas, NUNCA usar markdown, frases cortas

## 2. PRIMER MENSAJE (firstMessage)
La frase exacta con la que el agente abre la llamada. Natural, cálida, 1 frase.

## 3. MENSAJE DE CIERRE (endCallMessage)
La frase exacta con la que el agente despide al cliente. 1-2 frases.

## 4. FLUJOS DE LLAMADA EJEMPLO
3 conversaciones reales de ejemplo (cada turno en una línea):
- Ejemplo 1: llamada para pedir cita con éxito
- Ejemplo 2: llamada cuando no hay huecos disponibles
- Ejemplo 3: llamada de alguien que quiere saber precio de un servicio

## 5. PALABRAS DE ACTIVACIÓN DE ESCALADO
Lista de 8-10 frases que si el usuario dice, el agente DEBE transferir a humano inmediatamente.
(urgencias, amenazas, quejas graves, etc.)

IMPORTANTE: el system prompt debe sonar como si fuera una recepcionista real del negocio,
no un robot genérico. Usa el nombre del negocio, los servicios reales y los horarios reales."""


def _truncar(texto: str, max_chars: int = 10000) -> str:
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars] + f"\n\n[... truncado a {max_chars} caracteres]"


class VoiceAgentSpecialist:
    name = "VoiceAgentSpecialist"
    description = "Diseña agentes de voz telefónicos con IA para negocios locales"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.history: list[dict] = []

    def run(self, task: str) -> str:
        self.history.append({"role": "user", "content": task})
        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=8000,
            system=_SYSTEM,
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history.clear()

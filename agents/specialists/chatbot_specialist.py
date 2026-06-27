"""
Chatbot Specialist Agent.

Genera un system prompt completo y listo para desplegar, personalizado con:
- Datos del negocio (nombre, sector, objetivos, tono)
- Base de conocimiento real extraída de archivos subidos (PDF, TXT)

El output es un system prompt exportable que funciona en cualquier plataforma
(ManyChat, Landbot, Voiceflow, Claude API, OpenAI, etc.).
"""
from anthropic import Anthropic
from config import settings

_SYSTEM = """Eres un especialista senior en chatbots de IA para negocios locales.

Tu trabajo es crear un SYSTEM PROMPT completo y listo para usar, basado en la
información real del negocio que te proporcionan.

El resultado debe incluir:

## 1. SYSTEM PROMPT DEL CHATBOT
Un bloque de texto claramente delimitado (entre ``` ```) que el cliente pueda
copiar y pegar directamente en cualquier plataforma (ManyChat, Landbot, Claude
API, OpenAI, etc.). Debe incluir:
- Identidad y nombre del asistente
- Personalidad y tono exacto
- Catálogo completo de servicios/productos con precios si se proporcionaron
- Horarios, ubicación y datos de contacto si se proporcionaron
- Instrucciones de qué hacer cuando no sabe algo (escalar a humano)
- Instrucciones de cómo capturar datos del lead (nombre, teléfono, motivo)

## 2. FLUJOS CLAVE (ejemplos de conversación)
3-5 conversaciones reales de ejemplo que muestren cómo responde el bot
en los casos más frecuentes del sector.

## 3. PREGUNTAS FRECUENTES DETECTADAS
Lista de las FAQs más probables para ese negocio, con respuesta exacta
del bot basada en la información proporcionada.

## 4. CASOS DE ESCALACIÓN
Cuándo y cómo debe pasar la conversación a un humano.

IMPORTANTE: usa SIEMPRE la información real proporcionada. Si hay precios,
úsalos. Si hay tratamientos, nómbralos. El system prompt debe sonar como si
lo hubiera escrito el propio negocio, no genérico."""


def _truncar(texto: str, max_chars: int = 12000) -> str:
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars] + f"\n\n[... documento truncado a {max_chars} caracteres por límite de contexto]"


class ChatbotSpecialist:
    name = "ChatbotSpecialist"
    description = "Designs and implements intelligent chatbots for businesses"

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

from anthropic import Anthropic
from config import settings

_SYSTEM = """Eres un especialista en chatbots de IA-Agency con experiencia diseñando
conversaciones naturales y efectivas para negocios.

Cuando te pidan crear o diseñar un chatbot, entrega:
1. **Personalidad y tono** del chatbot
2. **Flujos de conversación** principales (con ejemplos de mensajes)
3. **Preguntas frecuentes** y respuestas sugeridas
4. **Casos de escalación** (cuándo pasar a un humano)
5. **Código de implementación** básico si se solicita

Eres experto en adaptar el chatbot al sector del cliente (restaurantes, e-commerce,
salud, inmobiliaria, etc.)."""


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
            max_tokens=4096,
            system=_SYSTEM,
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history.clear()

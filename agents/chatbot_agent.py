from typing import Optional
from anthropic import Anthropic
from config import settings

_DEFAULT_SYSTEM = (
    "Eres un asistente de IA profesional de IA-Agency. "
    "Responde de forma útil, precisa y concisa."
)


class ChatbotAgent:
    name = "Chatbot"
    description = "Conversational AI assistant with persistent session memory"

    def __init__(self, name: str = "Asistente IA", system_prompt: Optional[str] = None):
        self.display_name = name
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.system_prompt = system_prompt or _DEFAULT_SYSTEM
        self.history: list[dict] = []

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history.clear()

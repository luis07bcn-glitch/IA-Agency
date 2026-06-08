import json
from anthropic import Anthropic
from config import settings
from tools import TOOL_SCHEMAS, execute_tool

_SYSTEM = """Eres un agente autónomo de IA-Agency. Tienes acceso a herramientas que usas
de forma estratégica para completar tareas complejas de forma independiente.
Razona sobre los resultados de cada herramienta y entrega una respuesta final clara."""


class AutonomousAgent:
    name = "Autonomous"
    description = "Self-directed agent that uses tools in a loop to complete complex tasks"

    def __init__(self, max_iterations: int = 10):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.max_iterations = max_iterations

    def run(self, task: str) -> str:
        messages = [{"role": "user", "content": task}]

        for _ in range(self.max_iterations):
            response = self.client.messages.create(
                model=settings.default_model,
                max_tokens=4096,
                system=_SYSTEM,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return ""

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                messages.append({"role": "user", "content": tool_results})

        return "Tarea incompleta: se alcanzó el límite de iteraciones."

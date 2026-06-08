import json
from anthropic import Anthropic
from config import settings
from agents.specialists import ChatbotSpecialist, WebDeveloperAgent, ContentMarketingAgent

_SYSTEM = """Eres el Project Manager principal de IA-Agency. Tu rol es:

1. **Analizar** los requisitos del cliente en profundidad
2. **Planificar** el proyecto de forma estructurada
3. **Orquestar** a los agentes especialistas para ejecutar las tareas
4. **Sintetizar** los resultados en una entrega profesional

Cuando recibas un proyecto de cliente, primero usa la herramienta `analyze_project`
para descomponerlo en subtareas y asignarlas a los agentes correctos.

Agentes disponibles:
- **chatbot_specialist**: diseño e implementación de chatbots
- **web_developer**: landing pages, sitios web, código frontend
- **content_marketing**: contenido, copy, redes sociales, emails

Responde siempre de forma profesional como si hablaras directamente con el cliente."""

_TOOLS = [
    {
        "name": "analyze_project",
        "description": (
            "Analyzes a client project and returns a structured plan with assigned agents."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_title": {"type": "string", "description": "Short project title"},
                "tasks": {
                    "type": "array",
                    "description": "List of tasks to execute",
                    "items": {
                        "type": "object",
                        "properties": {
                            "agent": {
                                "type": "string",
                                "enum": ["chatbot_specialist", "web_developer", "content_marketing"],
                                "description": "Agent to assign this task to",
                            },
                            "task": {
                                "type": "string",
                                "description": "Detailed task description for the agent",
                            },
                        },
                        "required": ["agent", "task"],
                    },
                },
                "timeline": {"type": "string", "description": "Estimated project timeline"},
            },
            "required": ["project_title", "tasks"],
        },
    }
]

_AGENT_MAP = {
    "chatbot_specialist": ChatbotSpecialist,
    "web_developer": WebDeveloperAgent,
    "content_marketing": ContentMarketingAgent,
}


class ProjectManagerAgent:
    name = "ProjectManager"
    description = "Main orchestrator — analyzes client requirements and coordinates specialists"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.project_history: list[dict] = []

    def run(self, client_request: str, verbose: bool = True) -> dict:
        """
        Orchestrate the full project pipeline.
        Returns a dict with: plan, specialist_outputs, final_delivery.
        """
        messages = [{"role": "user", "content": client_request}]
        plan = None
        specialist_outputs = {}

        # Step 1: PM analyzes and creates plan via tool_use
        response = self.client.messages.create(
            model=settings.default_model,
            max_tokens=2048,
            system=_SYSTEM,
            tools=_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use" and block.name == "analyze_project":
                    plan = block.input
                    break

            # Step 2: Execute specialist tasks
            if plan and plan.get("tasks"):
                for item in plan["tasks"]:
                    agent_key = item["agent"]
                    task_text = item["task"]
                    if verbose:
                        print(f"  → {agent_key}: {task_text[:60]}...")
                    agent = _AGENT_MAP[agent_key]()
                    specialist_outputs[agent_key] = agent.run(task_text)

            # Step 3: PM synthesizes results
            tool_result_content = [
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(plan),
                }
                for block in response.content
                if block.type == "tool_use"
            ]
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_result_content})

            synthesis_prompt = (
                "El equipo ha completado las tareas. Aquí están los resultados:\n\n"
                + "\n\n---\n\n".join(
                    f"**{k}**:\n{v}" for k, v in specialist_outputs.items()
                )
                + "\n\nGenera una entrega ejecutiva profesional para el cliente."
            )
            messages.append({"role": "user", "content": synthesis_prompt})

            final_response = self.client.messages.create(
                model=settings.default_model,
                max_tokens=4096,
                system=_SYSTEM,
                messages=messages,
            )
            final_delivery = final_response.content[0].text
        else:
            # No tool use — PM responded directly
            final_delivery = response.content[0].text

        self.project_history.append({
            "request": client_request,
            "plan": plan,
            "outputs": specialist_outputs,
        })

        return {
            "plan": plan,
            "specialist_outputs": specialist_outputs,
            "final_delivery": final_delivery,
        }

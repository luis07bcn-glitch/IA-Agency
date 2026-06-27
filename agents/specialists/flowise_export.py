"""
Genera el JSON de Flowise listo para importar (File → Load Chatflow).

Crea un chatflow con:
  - ChatAnthropic (Claude) como modelo
  - BufferWindowMemory para historial de conversación
  - ConversationChain con el system prompt del negocio

Uso:
    from agents.specialists.flowise_export import generar_chatflow_json
    json_str = generar_chatflow_json(system_prompt, nombre_negocio)
"""
import json
import uuid


def _id(base: str) -> str:
    return f"{base}_{uuid.uuid4().hex[:6]}"


def generar_chatflow_json(system_prompt: str, nombre_negocio: str = "Negocio") -> str:
    """
    Devuelve el JSON del chatflow de Flowise como string.
    El usuario importa este archivo desde Flowise → File → Load Chatflow.
    Después solo necesita añadir su credencial de Anthropic.
    """
    llm_id = "chatAnthropic_0"
    mem_id = "bufferWindowMemory_0"
    chain_id = "conversationChain_0"

    # Limpiar el system prompt para JSON (escapar comillas dobles internas)
    sp_clean = system_prompt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    nodes = [
        # ── Nodo 1: ChatAnthropic ─────────────────────────────────────────
        {
            "id": llm_id,
            "position": {"x": 480, "y": 200},
            "type": "customNode",
            "data": {
                "id": llm_id,
                "label": "ChatAnthropic",
                "version": 3,
                "name": "chatAnthropic",
                "type": "ChatAnthropic",
                "baseClasses": ["ChatAnthropic", "BaseChatModel", "BaseLanguageModel"],
                "category": "Chat Models",
                "description": "Wrapper around Anthropic large language models that use the Chat endpoint.",
                "inputParams": [
                    {
                        "label": "Connect Credential",
                        "name": "credentialInput",
                        "type": "credential",
                        "credentialNames": ["anthropicApi"],
                        "id": f"{llm_id}-input-credentialInput-credential",
                    },
                    {
                        "label": "Model Name",
                        "name": "modelName",
                        "type": "string",
                        "default": "claude-haiku-4-5-20251001",
                        "id": f"{llm_id}-input-modelName-string",
                    },
                    {
                        "label": "Temperature",
                        "name": "temperature",
                        "type": "number",
                        "default": 0.7,
                        "optional": True,
                        "id": f"{llm_id}-input-temperature-number",
                    },
                    {
                        "label": "Max Tokens",
                        "name": "maxTokensToSample",
                        "type": "number",
                        "optional": True,
                        "default": 1024,
                        "id": f"{llm_id}-input-maxTokensToSample-number",
                    },
                ],
                "inputAnchors": [],
                "inputs": {
                    "modelName": "claude-haiku-4-5-20251001",
                    "temperature": "0.5",
                    "maxTokensToSample": "1024",
                },
                "outputAnchors": [
                    {
                        "id": f"{llm_id}-output-{llm_id}-ChatAnthropic|BaseChatModel|BaseLanguageModel",
                        "name": llm_id,
                        "label": "ChatAnthropic",
                        "type": "ChatAnthropic | BaseChatModel | BaseLanguageModel",
                    }
                ],
                "outputs": {},
                "selected": False,
            },
            "width": 300,
            "height": 430,
            "positionAbsolute": {"x": 480, "y": 200},
            "selected": False,
            "dragging": False,
        },
        # ── Nodo 2: BufferWindowMemory ────────────────────────────────────
        {
            "id": mem_id,
            "position": {"x": 80, "y": 380},
            "type": "customNode",
            "data": {
                "id": mem_id,
                "label": "Buffer Window Memory",
                "version": 1,
                "name": "bufferWindowMemory",
                "type": "BufferWindowMemory",
                "baseClasses": ["BufferWindowMemory", "BaseChatMemory", "BaseMemory"],
                "category": "Memory",
                "description": "Uses a Window of size k to surface the last k back-and-forth to use as memory.",
                "inputParams": [
                    {
                        "label": "Memory Key",
                        "name": "memoryKey",
                        "type": "string",
                        "default": "chat_history",
                        "id": f"{mem_id}-input-memoryKey-string",
                    },
                    {
                        "label": "Input Key",
                        "name": "inputKey",
                        "type": "string",
                        "default": "input",
                        "id": f"{mem_id}-input-inputKey-string",
                    },
                    {
                        "label": "Size",
                        "name": "k",
                        "type": "number",
                        "default": 10,
                        "id": f"{mem_id}-input-k-number",
                    },
                ],
                "inputAnchors": [],
                "inputs": {
                    "memoryKey": "chat_history",
                    "inputKey": "input",
                    "k": "10",
                },
                "outputAnchors": [
                    {
                        "id": f"{mem_id}-output-{mem_id}-BufferWindowMemory|BaseChatMemory|BaseMemory",
                        "name": mem_id,
                        "label": "BufferWindowMemory",
                        "type": "BufferWindowMemory | BaseChatMemory | BaseMemory",
                    }
                ],
                "outputs": {},
                "selected": False,
            },
            "width": 300,
            "height": 370,
            "positionAbsolute": {"x": 80, "y": 380},
            "selected": False,
            "dragging": False,
        },
        # ── Nodo 3: ConversationChain ──────────────────────────────────────
        {
            "id": chain_id,
            "position": {"x": 900, "y": 280},
            "type": "customNode",
            "data": {
                "id": chain_id,
                "label": "Conversation Chain",
                "version": 3,
                "name": "conversationChain",
                "type": "ConversationChain",
                "baseClasses": ["ConversationChain", "LLMChain", "BaseChain"],
                "category": "Chains",
                "description": "Chat models specific chain with memory and ability to use a System Prompt.",
                "inputParams": [
                    {
                        "label": "System Message",
                        "name": "systemMessagePrompt",
                        "type": "string",
                        "rows": 4,
                        "placeholder": "You are a helpful assistant",
                        "id": f"{chain_id}-input-systemMessagePrompt-string",
                    }
                ],
                "inputAnchors": [
                    {
                        "label": "Language Model",
                        "name": "model",
                        "type": "BaseChatModel",
                        "id": f"{chain_id}-input-model-BaseChatModel",
                    },
                    {
                        "label": "Memory",
                        "name": "memory",
                        "type": "BaseMemory",
                        "id": f"{chain_id}-input-memory-BaseMemory",
                    },
                ],
                "inputs": {
                    "model": f"{{{{{llm_id}.data.instance}}}}",
                    "memory": f"{{{{{mem_id}.data.instance}}}}",
                    "systemMessagePrompt": system_prompt,
                },
                "outputAnchors": [
                    {
                        "id": f"{chain_id}-output-{chain_id}-ConversationChain|LLMChain|BaseChain",
                        "name": chain_id,
                        "label": "ConversationChain",
                        "type": "ConversationChain | LLMChain | BaseChain",
                    }
                ],
                "outputs": {},
                "selected": False,
            },
            "width": 300,
            "height": 530,
            "positionAbsolute": {"x": 900, "y": 280},
            "selected": False,
            "dragging": False,
        },
    ]

    edges = [
        {
            "source": llm_id,
            "sourceHandle": f"{llm_id}-output-{llm_id}-ChatAnthropic|BaseChatModel|BaseLanguageModel",
            "target": chain_id,
            "targetHandle": f"{chain_id}-input-model-BaseChatModel",
            "type": "buttonedge",
            "id": f"edge_{llm_id}_{chain_id}",
            "data": {"label": ""},
        },
        {
            "source": mem_id,
            "sourceHandle": f"{mem_id}-output-{mem_id}-BufferWindowMemory|BaseChatMemory|BaseMemory",
            "target": chain_id,
            "targetHandle": f"{chain_id}-input-memory-BaseMemory",
            "type": "buttonedge",
            "id": f"edge_{mem_id}_{chain_id}",
            "data": {"label": ""},
        },
    ]

    chatflow = {
        "nodes": nodes,
        "edges": edges,
        "viewport": {"x": 0, "y": 0, "zoom": 0.75},
    }

    return json.dumps(chatflow, ensure_ascii=False, indent=2)


def generar_snippet_base44(chatflow_url: str, nombre_negocio: str = "Asistente", color: str = "#4f46e5") -> str:
    """
    Genera el snippet HTML para pegar en Base44 u otra web.
    chatflow_url: URL pública del chatflow en Railway, ej:
      https://tu-flowise.up.railway.app/api/v1/prediction/CHATFLOW_ID
    """
    return f"""<!-- Chatbot {nombre_negocio} — generado por MerakIA -->
<script type="module">
  import Chatbot from "https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js";
  Chatbot.init({{
    chatflowid: "CHATFLOW_ID",
    apiHost: "https://tu-flowise.up.railway.app",
    theme: {{
      button: {{
        backgroundColor: "{color}",
        right: 20,
        bottom: 20,
        size: 48,
        iconColor: "white",
        customIconSrc: "",
      }},
      chatWindow: {{
        welcomeMessage: "¡Hola! Soy el asistente de {nombre_negocio}. ¿En qué puedo ayudarte?",
        backgroundColor: "#ffffff",
        height: 600,
        width: 380,
        fontSize: 15,
        botMessage: {{
          backgroundColor: "#f1f5f9",
          textColor: "#1e293b",
        }},
        userMessage: {{
          backgroundColor: "{color}",
          textColor: "#ffffff",
        }},
        textInput: {{
          placeholder: "Escribe tu pregunta...",
          backgroundColor: "#ffffff",
          textColor: "#1e293b",
          sendButtonColor: "{color}",
        }},
      }},
    }},
  }});
</script>"""

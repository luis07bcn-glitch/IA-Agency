# IA-Agency

> **La agencia de Inteligencia Artificial que trabaja por ti**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Claude](https://img.shields.io/badge/Powered_by-Claude_AI-D97706)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)

---

## ¿Qué es IA-Agency?

IA-Agency es una plataforma multi-agente de Inteligencia Artificial que automatiza proyectos complejos de negocio. Un equipo de agentes especializados trabaja en coordinación para entregar resultados profesionales: desde chatbots personalizados hasta landing pages completas con su estrategia de marketing.

---

## Servicios

| Servicio | Agente | Descripción |
|---|---|---|
| 🤖 **Chatbots Inteligentes** | `ChatbotSpecialist` | Diseño, flujos conversacionales e implementación de chatbots para cualquier negocio |
| 🌐 **Desarrollo Web** | `WebDeveloperAgent` | Landing pages modernas, responsive y optimizadas para conversión |
| 📣 **Contenido & Marketing** | `ContentMarketingAgent` | Copy, posts, emails y estrategia de contenidos para todos los canales |
| 📋 **Gestión de Proyectos** | `ProjectManagerAgent` | Orquestador principal — analiza, planifica y coordina todo el equipo |
| 🤖 **Agente Autónomo** | `AutonomousAgent` | Ejecuta tareas complejas de forma independiente usando herramientas |
| 💬 **Chat Interactivo** | `ChatbotAgent` | Asistente conversacional con memoria de sesión |

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luis07bcn-glitch/IA-Agency.git
cd IA-Agency

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env
# Edita .env y añade tu ANTHROPIC_API_KEY
```

---

## Uso rápido

```bash
# Ver todos los agentes disponibles
python main.py agents list

# Ejecutar un proyecto completo (PM + equipo)
python main.py project "Crear chatbot para restaurante italiano"

# Diseñar un chatbot específico
python main.py chatbot "Chatbot de soporte para e-commerce de ropa"

# Generar una landing page
python main.py webdev "Landing page para academia de inglés online" --output landing.html

# Crear contenido de marketing
python main.py content "5 posts de Instagram para cafetería de especialidad"

# Chat interactivo
python main.py chat --name "Ana" --system "Eres una asistente de ventas amable"

# Agente autónomo con herramientas
python main.py autonomous "Calcula el ROI de invertir 5000€ con un retorno del 23% y guárdalo en roi.txt"
```

---

## Estructura del Proyecto

```
IA-Agency/
├── agents/
│   ├── chatbot_agent.py          # Chat interactivo con memoria
│   ├── pm_agent.py               # Project Manager (orquestador)
│   ├── autonomous_agent.py       # Agente autónomo con tool-use
│   └── specialists/
│       ├── chatbot_specialist.py # Diseño de chatbots
│       ├── web_developer.py      # Desarrollo web
│       └── content_marketing.py  # Contenido y marketing
├── tools/
│   ├── calculator_tool.py        # Cálculos matemáticos seguros
│   ├── datetime_tool.py          # Fecha y hora
│   └── file_tool.py              # Lectura/escritura de archivos
├── workflows/
│   └── agency_workflow.py        # Pipelines multi-agente
├── memory/
│   └── conversation_memory.py    # Memoria persistente en JSON
├── config/
│   └── settings.py               # Configuración via .env
├── tests/                        # Suite de pruebas (pytest)
├── outputs/                      # Archivos generados por agentes
└── main.py                       # CLI principal
```

---

## Arquitectura

```
Cliente → main.py CLI
              │
              ▼
     ProjectManagerAgent  ←── analiza y planifica
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
ChatbotSpec  WebDev  ContentMkt
              │
              ▼
     Entrega final sintetizada
```

El `ProjectManagerAgent` actúa como cerebro: recibe la solicitud del cliente, usa **tool_use** de Claude para estructurar un plan, delega a los especialistas y sintetiza la entrega final.

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| LLM | Claude (claude-sonnet-4-6) vía Anthropic SDK |
| Orquestación | Agent loop personalizado + LangGraph |
| CLI | Typer + Rich |
| Configuración | Pydantic Settings |
| Testing | Pytest |

---

## Configuración (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_MODEL=claude-sonnet-4-6
LOG_LEVEL=INFO
DEBUG=false
```

---

## Contribuir

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nuevo-agente`
3. Commit: `git commit -m "feat: add nuevo agente"`
4. Push: `git push origin feature/nuevo-agente`
5. Abre un Pull Request

---

## Licencia

MIT © 2025 IA-Agency · [luis07bcn-glitch](https://github.com/luis07bcn-glitch)

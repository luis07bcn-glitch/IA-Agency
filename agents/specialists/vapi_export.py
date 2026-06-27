"""
Genera el JSON de configuración de Vapi.ai listo para importar.

Vapi.ai es la plataforma líder para agentes de voz en 2026:
- Soporte nativo en castellano (Deepgram nova-2 transcriber)
- Integración ElevenLabs para voz natural
- Webhook para conectar con n8n/Google Calendar
- Import directo desde dashboard.vapi.ai → Assistants → Import

Uso:
    from agents.specialists.vapi_export import generar_vapi_assistant
    json_str = generar_vapi_assistant(system_prompt, first_message, ...)
"""
import json


# Voces ElevenLabs en castellano — las más naturales disponibles
VOCES_ELEVENLABS = {
    "mujer_profesional": {
        "voiceId": "EXAVITQu4vr4xnSDxMaL",
        "nombre": "Sarah (mujer, profesional)",
    },
    "mujer_calida": {
        "voiceId": "21m00Tcm4TlvDq8ikWAM",
        "nombre": "Rachel (mujer, cálida)",
    },
    "hombre_profesional": {
        "voiceId": "pNInz6obpgDQGcFmaJgB",
        "nombre": "Adam (hombre, profesional)",
    },
    "hombre_jovial": {
        "voiceId": "TxGEqnHWrfWFTfGW9XjX",
        "nombre": "Josh (hombre, jovial)",
    },
}


def _tools_agenda(webhook_url: str) -> list:
    """
    Define las herramientas de function calling para el agente de voz.
    El agente las llama en mitad de la conversación — Vapi las envía al webhook
    de n8n como POST con {message: {functionCall: {name, parameters}}}.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": (
                    "Consulta los huecos libres en el calendario del negocio para una fecha concreta. "
                    "DEBES llamar a esta función ANTES de proponer o confirmar cualquier hora. "
                    "Nunca inventes horarios disponibles."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha": {
                            "type": "string",
                            "description": "Fecha en formato YYYY-MM-DD, por ejemplo 2026-06-20. Si el paciente dice 'mañana' o 'el martes', conviértelo a fecha exacta.",
                        },
                        "preferencia_horaria": {
                            "type": "string",
                            "enum": ["mañana", "tarde", "cualquiera"],
                            "description": "Preferencia horaria del paciente.",
                        },
                    },
                    "required": ["fecha"],
                },
            },
            "server": {"url": webhook_url},
            "messages": [
                {
                    "type": "request-start",
                    "content": "Un momento, consulto la agenda.",
                },
                {
                    "type": "request-failed",
                    "content": "Lo siento, no puedo consultar la agenda ahora mismo. Por favor llame en unos minutos.",
                },
            ],
        },
        {
            "type": "function",
            "function": {
                "name": "book_appointment",
                "description": (
                    "Crea la cita en el calendario del negocio. "
                    "Llama a esta función SOLO cuando el paciente haya confirmado explícitamente el día y la hora. "
                    "Pide siempre nombre completo y teléfono antes de reservar."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_iso": {
                            "type": "string",
                            "description": "Fecha y hora exacta en ISO 8601, por ejemplo 2026-06-20T10:00:00",
                        },
                        "nombre": {
                            "type": "string",
                            "description": "Nombre completo del paciente o cliente.",
                        },
                        "telefono": {
                            "type": "string",
                            "description": "Número de teléfono de contacto.",
                        },
                        "servicio": {
                            "type": "string",
                            "description": "Nombre del servicio o tratamiento que solicita.",
                        },
                    },
                    "required": ["fecha_iso", "nombre", "telefono", "servicio"],
                },
            },
            "server": {"url": webhook_url},
            "messages": [
                {
                    "type": "request-start",
                    "content": "Perfecto, le registro la cita ahora mismo.",
                },
                {
                    "type": "request-complete",
                    "content": "Listo, la cita queda confirmada.",
                },
                {
                    "type": "request-failed",
                    "content": "Ha habido un problema al guardar la cita. Por favor llámenos directamente.",
                },
            ],
        },
    ]


def generar_vapi_assistant(
    system_prompt: str,
    first_message: str,
    end_call_message: str,
    nombre_negocio: str = "Negocio",
    voz_clave: str = "mujer_profesional",
    webhook_url: str = "",
    max_duracion_segundos: int = 300,
) -> str:
    """
    Devuelve el JSON del assistant de Vapi.ai como string.
    El usuario importa este archivo desde:
    dashboard.vapi.ai → Assistants → botón Import (↑) → selecciona el .json
    Después solo necesita:
    1. Añadir su API key de ElevenLabs en Settings → Providers
    2. Conectar un número de teléfono en Phone Numbers
    """
    voz = VOCES_ELEVENLABS.get(voz_clave, VOCES_ELEVENLABS["mujer_profesional"])

    assistant = {
        "name": f"Recepcionista IA — {nombre_negocio}",
        "model": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ],
            "temperature": 0.6,
            "maxTokens": 200,
            "emotionRecognitionEnabled": True,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": voz["voiceId"],
            "stability": 0.5,
            "similarityBoost": 0.75,
            "style": 0.0,
            "useSpeakerBoost": True,
            "optimizeStreamingLatency": 3,
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "es",
            "smartFormat": True,
            "keywords": ["cita", "reserva", "cancelar", "precio", "horario"],
        },
        "firstMessage": first_message,
        "endCallMessage": end_call_message,
        "endCallFunctionEnabled": True,
        "hipaaEnabled": False,
        "silenceTimeoutSeconds": 10,
        "maxDurationSeconds": max_duracion_segundos,
        "backgroundSound": "off",
        "backchannelingEnabled": True,
        "backgroundDenoisingEnabled": True,
        "analysisPlan": {
            "summaryPrompt": (
                "Resume la llamada en 2-3 frases: motivo, resultado "
                "(cita confirmada / no disponible / escalado) y datos recogidos."
            ),
            "successEvaluationPrompt": (
                "¿El agente resolvió satisfactoriamente la necesidad del cliente? "
                "Responde 'true' o 'false'."
            ),
            "successEvaluationRubric": "DescriptiveScale",
        },
        **({"serverUrl": webhook_url} if webhook_url else {}),
        **({"tools": _tools_agenda(webhook_url)} if webhook_url else {}),
    }

    return json.dumps(assistant, ensure_ascii=False, indent=2)


def _seccion_telefono(nombre_negocio: str, sector: str) -> str:
    """
    Genera la sección de conexión al teléfono del negocio según el sector.
    Detecta si el sector usa móvil, centralita o VoIP y adapta las instrucciones.
    """
    # Sectores que típicamente solo tienen móvil
    sectores_movil = {"peluquería / barbería", "restaurante / bar", "taller mecánico", "otro"}
    # Sectores que suelen tener centralita
    sectores_centralita = {
        "clínica dental", "clínica estética / medicina estética",
        "centro de fisioterapia", "psicología / terapia",
        "despacho profesional (asesoría, abogado)",
    }

    sector_lower = sector.lower()
    es_centralita = any(s in sector_lower for s in sectores_centralita)
    es_movil = any(s in sector_lower for s in sectores_movil)

    if es_centralita:
        perfil = "centralita"
        recomendacion = "**Opción recomendada: desvío desde centralita VoIP**"
        contexto = f"Las {sector.lower()}s suelen tener centralita (3CX, Asterisk, Ringover, Fonvirtual). El desvío se configura directamente en la centralita sin tocar el número principal."
        pasos_principal = """**Configuración en centralita VoIP (3CX / Asterisk / Ringover):**
1. Accede al panel de administración de tu centralita
2. Ve a **Rutas de llamada saliente** o **Call Routing**
3. Crea una regla: _"Si no contesta en 15 segundos → transferir a [número Vapi]"_
4. Crea otra regla: _"Fuera de horario → transferir a [número Vapi] inmediatamente"_
5. Guarda y prueba llamando desde un móvil externo

**Con Ringover** (muy común en clínicas):
1. Panel → Flujos de llamada → Editar
2. Añade nodo "Fuera de horario" → acción "Transferir a número externo"
3. Introduce el número de Vapi.ai
4. Activa el horario de atención humana en el mismo flujo"""
    elif es_movil:
        perfil = "móvil"
        recomendacion = "**Opción recomendada: desvío de llamadas en el móvil**"
        contexto = f"Los {sector.lower()}s normalmente usan un móvil de empresa como línea principal. El desvío se activa con un código USSD directo desde el móvil, sin apps ni configuración técnica."
        pasos_principal = """**Activar desvío en el móvil (funciona en Movistar, Vodafone, Orange, Yoigo):**

Desvío cuando no contestan (recomendado para horario de atención):
```
**61*+34XXXXXXXXX# [LLAMAR]
```
_(sustituye XXXXXXXXX por el número de Vapi.ai)_

Desvío incondicional — TODAS las llamadas van al agente (para negocios sin recepción):
```
**21*+34XXXXXXXXX# [LLAMAR]
```

Desvío cuando está ocupado o sin cobertura:
```
**67*+34XXXXXXXXX# [LLAMAR]
**62*+34XXXXXXXXX# [LLAMAR]
```

Para cancelar cualquier desvío:
```
##002# [LLAMAR]
```

> **Consejo:** configura los 3 desvíos (no contesta + ocupado + sin cobertura) para que ninguna llamada se pierda."""
    else:
        perfil = "general"
        recomendacion = "**Elige la opción según la infraestructura del negocio**"
        contexto = "Detecta si el negocio usa móvil, centralita física o centralita VoIP y aplica la opción correspondiente."
        pasos_principal = """**Si solo tienen móvil:**
Desvío cuando no contestan:
```
**61*+34XXXXXXXXX# [LLAMAR]
```

**Si tienen centralita VoIP (3CX, Ringover, Asterisk):**
1. Panel de administración → Rutas de llamada
2. Regla: "fuera de horario o sin respuesta → transferir a [número Vapi]"

**Si tienen centralita física (DECT, analógica):**
Consultar con su operador de telefonía para añadir desvío condicional."""

    return f"""---

## 📞 Conectar el agente al teléfono real de {nombre_negocio}

{recomendacion}

{contexto}

### ¿Cómo funciona el flujo?

```
Cliente llama al número de {nombre_negocio}
    │
    ├─ Si es horario de atención y alguien contesta → llamada normal (humano)
    │
    └─ Si no contestan en 15s / fuera de horario / ocupado
         └─ Desvío automático al número de Vapi.ai
              └─ El agente de voz atiende la llamada
                   ├─ Agenda cita → notifica por email / Google Calendar
                   ├─ Responde preguntas de precio, horario, servicios
                   └─ Urgencia o petición de humano → indica horario de atención
```

### Configuración paso a paso

{pasos_principal}

### Obtener el número de Vapi.ai

1. En **dashboard.vapi.ai → Phone Numbers → Buy Number**
2. Selecciona el prefijo **+34** (España) si está disponible
   - Si no hay +34, usa un número +44 (UK) — funciona igual para recibir desvíos
3. Coste: ~$2/mes + consumo de llamadas ($0.05-0.10/min)
4. Asigna tu assistant "{nombre_negocio}" a ese número

### Probar que funciona

1. Activa el desvío con el código correspondiente
2. Llama desde otro móvil al número del negocio
3. Deja que suene sin contestar → debe transferir al agente en ~15 segundos
4. El agente debe saludar y atender la llamada
5. Comprueba que la cita queda registrada en Google Calendar (si tienes n8n conectado)

### Para el cliente: qué decirle exactamente

> *"Hemos configurado una recepcionista virtual con IA que atiende las llamadas cuando estás ocupado o fuera de horario. Los clientes que llamen y no puedas atender serán atendidos automáticamente, podrán pedir cita y recibirás la notificación en tu calendario. No tienes que cambiar tu número ni instalar nada."*

"""


def generar_guia_vapi(
    nombre_negocio: str,
    webhook_url: str = "",
    tiene_n8n: bool = True,
    sector: str = "",
) -> str:
    """
    Guía paso a paso para desplegar el agente en Vapi.ai.
    """
    pasos_webhook = ""
    if tiene_n8n and webhook_url:
        pasos_webhook = f"""
### Conectar con n8n (reservas automáticas)
1. En el JSON importado, ya está configurado el webhook: `{webhook_url}`
2. En n8n, crea un nodo **Webhook** con esa URL
3. El agente enviará JSON con: `{{nombre, telefono, servicio, fecha_preferida}}`
4. Conecta ese webhook a tu Google Calendar para crear la cita
"""
    elif tiene_n8n:
        pasos_webhook = """
### Conectar con n8n (reservas automáticas)
1. Crea el workflow en n8n (usa la tab "Automatización" del Chatbot Specialist)
2. Copia la URL del nodo Webhook de n8n
3. En Vapi.ai → tu Assistant → Edit → Server URL → pega la URL
4. El agente enviará los datos de la cita como JSON
"""

    seccion_tel = _seccion_telefono(nombre_negocio, sector) if sector else ""

    return f"""## Cómo desplegar el Agente de Voz en Vapi.ai

### Paso 1 — Crear cuenta
1. Ve a **dashboard.vapi.ai** y crea una cuenta gratuita
2. El plan gratuito incluye ~$10 de crédito de prueba (≈ 60 min de llamadas)
3. El plan de pago cuesta ~$0.05-0.10/min según el volumen

### Paso 2 — Importar el Assistant
1. En el dashboard, ve a **Assistants** (menú izquierdo)
2. Haz clic en el botón **Import** (icono de flecha arriba ↑)
3. Selecciona el archivo `.json` que descargaste
4. El assistant "{nombre_negocio}" aparecerá en tu lista

### Paso 3 — Configurar credenciales de voz
1. Ve a **Settings → Providers**
2. Añade tu API key de **ElevenLabs** (elevenlabs.io → Profile → API Keys)
   - El plan gratuito de ElevenLabs da 10.000 caracteres/mes
   - El plan Starter (5€/mes) da 30.000 caracteres/mes ≈ 150 llamadas cortas
3. Opcional: añade tu key de **Deepgram** para mayor control del transcriptor

### Paso 4 — Conectar número de teléfono
**Opción A — Número Vapi (más rápido):**
1. Ve a **Phone Numbers** → **Buy Number**
2. Selecciona España (+34) si está disponible, o usa un número de EE.UU./UK
3. Asigna el assistant "{nombre_negocio}" a ese número
4. Coste: ~$2/mes + $0.10/min de llamada

**Opción B — Número propio del cliente (más profesional):**
1. El cliente mantiene su número actual con Twilio o Vonage
2. Configura call forwarding: las llamadas redirigen al número de Vapi
3. Ve a **Phone Numbers → Import** y conecta el SIP trunk
{pasos_webhook}
### Paso 5 — Probar
1. En el dashboard, haz clic en el botón **▶ Test** del assistant
2. El navegador abre un widget de llamada en tiempo real
3. Prueba al menos: pedir cita, preguntar precio, pedir hablar con persona
4. Ajusta el system prompt si alguna respuesta no es natural

### Costes orientativos para el cliente final
| Concepto | Coste |
|---|---|
| Setup MerakIA (configuración + pruebas) | 497-997 € (único) |
| Vapi.ai mensual (~200 llamadas/mes) | ~20-40 €/mes |
| ElevenLabs voz natural | 5-22 €/mes |
| Número de teléfono | 2-5 €/mes |
| **Total recurrente cliente** | **~30-70 €/mes** |
| **Margen sugerido MerakIA** | **+150-200 €/mes gestión** |
{seccion_tel}"""

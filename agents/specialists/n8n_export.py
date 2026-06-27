"""
Genera workflows de n8n listos para importar (File → Import → From JSON).

Workflow: Chatbot → Doctoralia iCal → Google Calendar → Confirmación email
Flujo:
  1. Webhook recibe datos del chatbot (nombre, teléfono, fecha, servicio)
  2. Descarga el iCal de Doctoralia y comprueba si el hueco está libre
  3. Si libre  → crea evento en Google Calendar + envía email de confirmación
  4. Si ocupado → devuelve las 3 próximas franjas disponibles
"""
import json
import uuid


def _uid() -> str:
    return str(uuid.uuid4())


def generar_workflow_doctoralia(
    nombre_clinica: str = "Clínica",
    google_calendar_id: str = "primary",
    ical_url: str = "https://www.doctoralia.es/ical/XXXXXXXX.ics",
    email_clinica: str = "clinica@ejemplo.com",
    duracion_cita_min: int = 30,
) -> str:
    """
    Devuelve el JSON del workflow de n8n como string.
    El usuario importa desde n8n → File → Import → From JSON.
    """

    # ── IDs de los nodos ──────────────────────────────────────────────────
    id_webhook      = _uid()
    id_fetch_ical   = _uid()
    id_parse        = _uid()
    id_if           = _uid()
    id_gcal         = _uid()
    id_email        = _uid()
    id_resp_ok      = _uid()
    id_resp_no      = _uid()

    # ── Código JavaScript para parsear iCal ───────────────────────────────
    parse_code = r"""
// Parsea el iCal de Doctoralia y comprueba si el hueco pedido está libre
const icalText = $('Obtener iCal Doctoralia').first().json.data;
const inputData = $('Webhook Citas').first().json.body;

const nombrePaciente   = inputData.nombre    || 'Paciente';
const telefonoPaciente = inputData.telefono  || '';
const emailPaciente    = inputData.email     || '';
const servicio         = inputData.servicio  || 'Consulta';
const fechaDeseadaStr  = inputData.fecha_iso; // formato: "2026-06-20T10:00:00"
const DURACION_MS      = """ + str(duracion_cita_min * 60 * 1000) + r""";

const fechaDeseada = new Date(fechaDeseadaStr);
const fechaFin     = new Date(fechaDeseada.getTime() + DURACION_MS);

// ── Parsear VEVENT ────────────────────────────────────────────────────────
function parseDate(s) {
  if (!s) return null;
  // Formato básico: 20260620T100000Z o 20260620T100000
  const m = s.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/);
  if (!m) return null;
  return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}Z`);
}

const events = [];
const blocks = icalText.split('BEGIN:VEVENT');
for (let i = 1; i < blocks.length; i++) {
  const b    = blocks[i];
  const dtStart = parseDate((b.match(/DTSTART[^:]*:(\S+)/) || [])[1]);
  const dtEnd   = parseDate((b.match(/DTEND[^:]*:(\S+)/)   || [])[1]);
  if (dtStart && dtEnd) events.push({ start: dtStart, end: dtEnd });
}

// ── Comprobar solapamiento ────────────────────────────────────────────────
function solapan(s1, e1, s2, e2) {
  return s1 < e2 && e1 > s2;
}

const libre = !events.some(ev => solapan(fechaDeseada, fechaFin, ev.start, ev.end));

// ── Buscar próximas 3 franjas libres (si está ocupada) ────────────────────
const alternativas = [];
if (!libre) {
  let cursor = new Date(fechaDeseada);
  cursor.setMinutes(0, 0, 0);
  const limite = new Date(cursor.getTime() + 7 * 24 * 60 * 60 * 1000); // 7 días
  while (alternativas.length < 3 && cursor < limite) {
    const h = cursor.getHours();
    if (h >= 9 && h < 19) { // horario laboral
      const fin = new Date(cursor.getTime() + DURACION_MS);
      const ocupada = events.some(ev => solapan(cursor, fin, ev.start, ev.end));
      if (!ocupada) alternativas.push(cursor.toISOString());
    }
    cursor = new Date(cursor.getTime() + DURACION_MS);
  }
}

return [{
  json: {
    libre,
    fechaDeseadaISO: fechaDeseada.toISOString(),
    fechaFinISO:     fechaFin.toISOString(),
    alternativas,
    nombrePaciente,
    telefonoPaciente,
    emailPaciente,
    servicio,
  }
}];
""".strip()

    nodes = [
        # ── 1. Webhook ────────────────────────────────────────────────────
        {
            "parameters": {
                "httpMethod": "POST",
                "path": "doctoralia-cita",
                "responseMode": "responseNode",
                "options": {},
            },
            "id": id_webhook,
            "name": "Webhook Citas",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [240, 380],
            "webhookId": _uid(),
        },
        # ── 2. Obtener iCal de Doctoralia ─────────────────────────────────
        {
            "parameters": {
                "url": ical_url,
                "method": "GET",
                "options": {"response": {"response": {"responseFormat": "text"}}},
            },
            "id": id_fetch_ical,
            "name": "Obtener iCal Doctoralia",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [460, 380],
        },
        # ── 3. Parsear y verificar disponibilidad ─────────────────────────
        {
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": parse_code,
            },
            "id": id_parse,
            "name": "Comprobar disponibilidad",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [680, 380],
        },
        # ── 4. IF disponible ──────────────────────────────────────────────
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": _uid(),
                            "leftValue": "={{ $json.libre }}",
                            "rightValue": True,
                            "operator": {"type": "boolean", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": id_if,
            "name": "¿Hueco libre?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [900, 380],
        },
        # ── 5. Crear evento en Google Calendar ────────────────────────────
        {
            "parameters": {
                "operation": "create",
                "calendar": {"__rl": True, "value": google_calendar_id, "mode": "id"},
                "start": "={{ $json.fechaDeseadaISO }}",
                "end": "={{ $json.fechaFinISO }}",
                "additionalFields": {
                    "summary": f"={{'Cita ' + $json.servicio + ' — ' + $json.nombrePaciente}}",
                    "description": "={{ 'Paciente: ' + $json.nombrePaciente + '\\nTeléfono: ' + $json.telefonoPaciente + '\\nServicio: ' + $json.servicio }}",
                },
            },
            "id": id_gcal,
            "name": "Crear cita Google Calendar",
            "type": "n8n-nodes-base.googleCalendar",
            "typeVersion": 1,
            "position": [1120, 240],
        },
        # ── 6. Enviar email de confirmación ───────────────────────────────
        {
            "parameters": {
                "sendTo": f"={{{{ $json.emailPaciente || '{email_clinica}' }}}}",
                "subject": f"={{'✅ Cita confirmada en {nombre_clinica} — ' + $json.servicio}}",
                "message": f"={{{{ 'Hola ' + $json.nombrePaciente + ',\\n\\nTu cita para ' + $json.servicio + ' en {nombre_clinica} ha sido confirmada.\\n\\nFecha: ' + new Date($json.fechaDeseadaISO).toLocaleString('es-ES') + '\\n\\nSi necesitas cancelar o cambiar la cita, llámanos a {email_clinica}.\\n\\nHasta pronto,\\n{nombre_clinica}' }}}}",
                "options": {"appendAttribution": False},
            },
            "id": id_email,
            "name": "Email confirmación",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2,
            "position": [1340, 240],
        },
        # ── 7. Respuesta OK al chatbot ────────────────────────────────────
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ JSON.stringify({ ok: true, mensaje: 'Cita confirmada para ' + new Date($json.fechaDeseadaISO).toLocaleString('es-ES', {dateStyle:'full', timeStyle:'short'}) + '. Recibirás un email de confirmación.' }) }}",
                "options": {},
            },
            "id": id_resp_ok,
            "name": "Responder OK",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [1560, 240],
        },
        # ── 8. Respuesta NO disponible con alternativas ───────────────────
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ JSON.stringify({ ok: false, mensaje: 'Ese horario no está disponible. Aquí tienes los próximos huecos libres:', alternativas: $json.alternativas.map(d => new Date(d).toLocaleString('es-ES', {dateStyle:'full', timeStyle:'short'})) }) }}",
                "options": {},
            },
            "id": id_resp_no,
            "name": "Responder alternativas",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [1120, 520],
        },
    ]

    connections = {
        "Webhook Citas": {
            "main": [[{"node": "Obtener iCal Doctoralia", "type": "main", "index": 0}]]
        },
        "Obtener iCal Doctoralia": {
            "main": [[{"node": "Comprobar disponibilidad", "type": "main", "index": 0}]]
        },
        "Comprobar disponibilidad": {
            "main": [[{"node": "¿Hueco libre?", "type": "main", "index": 0}]]
        },
        "¿Hueco libre?": {
            "main": [
                [{"node": "Crear cita Google Calendar", "type": "main", "index": 0}],
                [{"node": "Responder alternativas",      "type": "main", "index": 0}],
            ]
        },
        "Crear cita Google Calendar": {
            "main": [[{"node": "Email confirmación", "type": "main", "index": 0}]]
        },
        "Email confirmación": {
            "main": [[{"node": "Responder OK", "type": "main", "index": 0}]]
        },
    }

    workflow = {
        "name": f"Citas {nombre_clinica} — Doctoralia + Google Calendar",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "versionId": _uid(),
        "meta": {"templateCredsSetupCompleted": False},
        "tags": [],
    }

    return json.dumps(workflow, ensure_ascii=False, indent=2)


def generar_workflow_voz_agenda(
    nombre_negocio: str = "Negocio",
    google_calendar_id: str = "primary",
    email_negocio: str = "negocio@ejemplo.com",
    duracion_cita_min: int = 30,
    hora_inicio: int = 9,
    hora_fin: int = 20,
    dias_laborables: str = "1,2,3,4,5",  # lunes=1 … domingo=7
) -> str:
    """
    Workflow de n8n para agente de voz con disponibilidad en tiempo real.

    Recibe function calls de Vapi.ai durante la conversación:
      • check_availability  → consulta Google Calendar y devuelve huecos libres
      • book_appointment    → crea el evento en Google Calendar (solo cuando el
                              paciente confirma explícitamente)

    El agente nunca promete una hora sin haber consultado primero.
    """

    id_webhook   = _uid()
    id_router    = _uid()
    id_gcal_get  = _uid()
    id_slots     = _uid()
    id_resp_slots = _uid()
    id_gcal_create = _uid()
    id_resp_book  = _uid()
    id_resp_err   = _uid()

    # ── Código: calcular huecos libres ────────────────────────────────────────
    slots_code = f"""
// Recibe los eventos de Google Calendar para el día pedido
// y calcula los huecos libres dentro del horario del negocio
const body        = $('Webhook Voz Agenda').first().json.body;
const functionCall = body.message?.functionCall || body;
const params       = functionCall.parameters || {{}};

const fechaStr         = params.fecha;           // "2026-06-20"
const preferencia      = params.preferencia_horaria || 'cualquiera';
const DURACION_MS      = {duracion_cita_min} * 60 * 1000;
const HORA_INICIO      = {hora_inicio};
const HORA_FIN         = {hora_fin};
const DIAS_LAB         = [{dias_laborables}];     // 1=lun … 7=dom

// Día de la semana pedido (1=lun … 7=dom)
const fecha = new Date(fechaStr + 'T00:00:00');
const diaSemana = fecha.getDay() === 0 ? 7 : fecha.getDay();

if (!DIAS_LAB.includes(diaSemana)) {{
  return [{{ json: {{ huecos: [], mensaje: 'Ese día no tenemos consulta. ¿Te va bien otro día de la semana?' }} }}];
}}

// Eventos existentes del Google Calendar
const eventos = $input.all().map(item => item.json).filter(e => e.start);
const ocupados = eventos.map(e => ({{
  inicio: new Date(e.start.dateTime || e.start.date),
  fin:    new Date(e.end.dateTime   || e.end.date),
}}));

// Generar todos los posibles slots del día
const huecos = [];
let cursor = new Date(fechaStr + `T${{String(HORA_INICIO).padStart(2,'0')}}:00:00`);
const limFin = new Date(fechaStr + `T${{String(HORA_FIN).padStart(2,'0')}}:00:00`);

while (cursor.getTime() + DURACION_MS <= limFin.getTime()) {{
  const slotFin = new Date(cursor.getTime() + DURACION_MS);
  const libre = !ocupados.some(o => cursor < o.fin && slotFin > o.inicio);

  if (libre) {{
    const hora = cursor.toLocaleTimeString('es-ES', {{ hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid' }});
    // Filtrar por preferencia horaria
    const h = cursor.getHours();
    const esMañana = h < 14;
    const esTarde  = h >= 14;
    if (
      preferencia === 'cualquiera' ||
      (preferencia === 'mañana' && esMañana) ||
      (preferencia === 'tarde'  && esTarde)
    ) {{
      huecos.push({{ iso: cursor.toISOString(), hora, label: hora }});
    }}
  }}
  cursor = new Date(cursor.getTime() + DURACION_MS);
}}

const mensaje = huecos.length > 0
  ? `Tengo disponibles: ${{huecos.slice(0,5).map(h => h.hora).join(', ')}}. ¿Qué hora le va mejor?`
  : 'Lo siento, ese día no tenemos huecos disponibles. ¿Le va bien otro día?';

return [{{ json: {{ huecos: huecos.slice(0, 8), mensaje, fecha: fechaStr }} }}];
""".strip()

    # ── Código: confirmar reserva ─────────────────────────────────────────────
    book_code = f"""
const body         = $('Webhook Voz Agenda').first().json.body;
const functionCall = body.message?.functionCall || body;
const params       = functionCall.parameters || {{}};

return [{{
  json: {{
    fecha_iso:  params.fecha_iso,
    fecha_fin:  new Date(new Date(params.fecha_iso).getTime() + {duracion_cita_min} * 60000).toISOString(),
    nombre:     params.nombre    || 'Paciente',
    telefono:   params.telefono  || '',
    servicio:   params.servicio  || 'Consulta',
    titulo:     `${{params.servicio || 'Cita'}} — ${{params.nombre || 'Paciente'}}`,
    descripcion: `Paciente: ${{params.nombre}}\\nTeléfono: ${{params.telefono}}\\nServicio: ${{params.servicio}}\\nAgendado por: Agente de Voz IA`,
  }}
}}];
""".strip()

    id_gcal_book = _uid()

    nodes = [
        # ── 1. Webhook único ──────────────────────────────────────────────────
        {
            "parameters": {
                "httpMethod": "POST",
                "path": "voz-agenda",
                "responseMode": "responseNode",
                "options": {},
            },
            "id": id_webhook,
            "name": "Webhook Voz Agenda",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [240, 400],
            "webhookId": _uid(),
        },
        # ── 2. Router: check_availability vs book_appointment ─────────────────
        {
            "parameters": {
                "rules": {
                    "values": [
                        {
                            "conditions": {
                                "options": {"caseSensitive": False},
                                "conditions": [{
                                    "leftValue": "={{ $json.body.message.functionCall.name }}",
                                    "rightValue": "check_availability",
                                    "operator": {"type": "string", "operation": "equals"},
                                }],
                            },
                            "renameOutput": True,
                            "outputKey": "disponibilidad",
                        },
                        {
                            "conditions": {
                                "options": {"caseSensitive": False},
                                "conditions": [{
                                    "leftValue": "={{ $json.body.message.functionCall.name }}",
                                    "rightValue": "book_appointment",
                                    "operator": {"type": "string", "operation": "equals"},
                                }],
                            },
                            "renameOutput": True,
                            "outputKey": "reservar",
                        },
                    ]
                },
                "options": {"fallbackOutput": "extra"},
            },
            "id": id_router,
            "name": "¿Qué acción?",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3,
            "position": [460, 400],
        },
        # ── 3a. Google Calendar: obtener eventos del día ──────────────────────
        {
            "parameters": {
                "operation": "getAll",
                "calendar": {"__rl": True, "value": google_calendar_id, "mode": "id"},
                "returnAll": True,
                "options": {
                    "timeMin": "={{ new Date($json.body.message.functionCall.parameters.fecha + 'T00:00:00').toISOString() }}",
                    "timeMax": "={{ new Date($json.body.message.functionCall.parameters.fecha + 'T23:59:59').toISOString() }}",
                },
            },
            "id": id_gcal_get,
            "name": "Obtener eventos del día",
            "type": "n8n-nodes-base.googleCalendar",
            "typeVersion": 1,
            "position": [700, 260],
        },
        # ── 3b. Calcular huecos libres ────────────────────────────────────────
        {
            "parameters": {"mode": "runOnceForAllItems", "jsCode": slots_code},
            "id": id_slots,
            "name": "Calcular huecos libres",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [920, 260],
        },
        # ── 3c. Responder con huecos disponibles ──────────────────────────────
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": '={{ JSON.stringify({ result: $json.mensaje, huecos: $json.huecos }) }}',
                "options": {},
            },
            "id": id_resp_slots,
            "name": "Responder huecos",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [1140, 260],
        },
        # ── 4a. Preparar datos de la cita ─────────────────────────────────────
        {
            "parameters": {"mode": "runOnceForAllItems", "jsCode": book_code},
            "id": id_gcal_create,
            "name": "Preparar cita",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [700, 540],
        },
        # ── 4b. Crear evento en Google Calendar ───────────────────────────────
        {
            "parameters": {
                "operation": "create",
                "calendar": {"__rl": True, "value": google_calendar_id, "mode": "id"},
                "start": "={{ $json.fecha_iso }}",
                "end":   "={{ $json.fecha_fin }}",
                "additionalFields": {
                    "summary": "={{ $json.titulo }}",
                    "description": "={{ $json.descripcion }}",
                    "sendUpdates": "none",
                },
            },
            "id": id_gcal_book,
            "name": "Crear cita Google Calendar",
            "type": "n8n-nodes-base.googleCalendar",
            "typeVersion": 1,
            "position": [920, 540],
        },
        # ── 4c. Responder confirmación al agente de voz ───────────────────────
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": (
                    '={{ JSON.stringify({ result: "Cita confirmada para " +'
                    ' new Date($json.fecha_iso).toLocaleString("es-ES",{"dateStyle":"full","timeStyle":"short"}) +'
                    ' ". Le enviaremos un recordatorio." }) }}'
                ),
                "options": {},
            },
            "id": id_resp_book,
            "name": "Responder confirmación",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [1140, 540],
        },
        # ── 5. Fallback: acción desconocida ───────────────────────────────────
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": '{"result": "Acción no reconocida. Por favor intenta de nuevo."}',
                "options": {},
            },
            "id": id_resp_err,
            "name": "Responder error",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [700, 740],
        },
    ]

    connections = {
        "Webhook Voz Agenda": {
            "main": [[{"node": "¿Qué acción?", "type": "main", "index": 0}]]
        },
        "¿Qué acción?": {
            "main": [
                [{"node": "Obtener eventos del día", "type": "main", "index": 0}],
                [{"node": "Preparar cita",           "type": "main", "index": 0}],
                [{"node": "Responder error",          "type": "main", "index": 0}],
            ]
        },
        "Obtener eventos del día": {
            "main": [[{"node": "Calcular huecos libres", "type": "main", "index": 0}]]
        },
        "Calcular huecos libres": {
            "main": [[{"node": "Responder huecos", "type": "main", "index": 0}]]
        },
        "Preparar cita": {
            "main": [[{"node": "Crear cita Google Calendar", "type": "main", "index": 0}]]
        },
        "Crear cita Google Calendar": {
            "main": [[{"node": "Responder confirmación", "type": "main", "index": 0}]]
        },
    }

    workflow = {
        "name": f"Agente de Voz — Agenda {nombre_negocio}",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "versionId": _uid(),
        "meta": {"templateCredsSetupCompleted": False},
        "tags": ["voz", "agenda", "google-calendar"],
    }

    return json.dumps(workflow, ensure_ascii=False, indent=2)


def generar_workflow_recordatorios(
    nombre_negocio: str = "Negocio",
    google_calendar_id: str = "primary",
    canal: str = "whatsapp",          # "whatsapp" (Twilio) | "email" (Gmail)
    horas_antes: int = 24,
    mensaje_recordatorio: str = "",
    twilio_whatsapp_from: str = "whatsapp:+14155238886",
    telefono_negocio: str = "",
) -> str:
    """
    Workflow de n8n que envía recordatorios automáticos de cita.

    Cada día (Schedule Trigger) lee los eventos de Google Calendar de las próximas
    `horas_antes` horas, parsea nombre/teléfono/servicio del evento (mismo formato
    que escribe el agente de voz) y envía un recordatorio por WhatsApp o email.

    Reduce no-shows de forma automática sin tocar nada manualmente.
    """
    id_cron     = _uid()
    id_gcal     = _uid()
    id_parse    = _uid()
    id_filter   = _uid()
    id_send     = _uid()

    msg_default = (
        mensaje_recordatorio
        or f"¡Hola {{nombre}}! Te recordamos tu cita en {nombre_negocio} "
           f"el {{fecha}} a las {{hora}} para {{servicio}}. "
           f"Responde SÍ para confirmar o llámanos al {telefono_negocio or '[teléfono]'} si necesitas cambiarla. ¡Te esperamos!"
    )

    # ── Código: parsear eventos y construir el mensaje de cada paciente ───────
    parse_code = r"""
// Lee los eventos del calendario y extrae nombre, teléfono y servicio
// del cuerpo del evento (formato que escribe el agente de voz):
//   Paciente: Juan López
//   Teléfono: 600123456
//   Servicio: Limpieza
const eventos = $input.all().map(i => i.json);
const salida = [];

for (const ev of eventos) {
  const desc = ev.description || '';
  const nombre   = (desc.match(/(?:Paciente|Cliente|Nombre):\s*(.+)/i) || [])[1] || (ev.summary || '').split('—').pop().trim() || 'Cliente';
  const telefono = (desc.match(/(?:Tel[eé]fono|M[oó]vil|Phone):\s*([+\d\s]+)/i) || [])[1] || '';
  const servicio = (desc.match(/Servicio:\s*(.+)/i) || [])[1] || (ev.summary || 'tu cita');

  const inicio = new Date(ev.start.dateTime || ev.start.date);
  const fecha  = inicio.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Europe/Madrid' });
  const hora   = inicio.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid' });

  if (!telefono.trim()) continue; // sin teléfono no se puede recordar por WhatsApp

  const tel = telefono.replace(/\s/g, '');
  const telE164 = tel.startsWith('+') ? tel : '+34' + tel;

  salida.push({
    json: {
      nombre: nombre.trim(),
      telefono: telE164,
      servicio: servicio.trim(),
      fecha,
      hora,
      eventId: ev.id,
    }
  });
}

return salida;
""".strip()

    nodes = [
        # ── 1. Schedule Trigger (cada día por la mañana) ──────────────────────
        {
            "parameters": {
                "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]},
            },
            "id": id_cron,
            "name": "Cada hora",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [240, 380],
        },
        # ── 2. Google Calendar: eventos en la ventana de recordatorio ─────────
        {
            "parameters": {
                "operation": "getAll",
                "calendar": {"__rl": True, "value": google_calendar_id, "mode": "id"},
                "returnAll": True,
                "options": {
                    "timeMin": f"={{{{ new Date(Date.now() + {horas_antes} * 3600000).toISOString() }}}}",
                    "timeMax": f"={{{{ new Date(Date.now() + ({horas_antes} + 1) * 3600000).toISOString() }}}}",
                    "singleEvents": True,
                    "orderBy": "startTime",
                },
            },
            "id": id_gcal,
            "name": "Citas próximas",
            "type": "n8n-nodes-base.googleCalendar",
            "typeVersion": 1,
            "position": [460, 380],
        },
        # ── 3. Parsear datos del paciente ─────────────────────────────────────
        {
            "parameters": {"mode": "runOnceForAllItems", "jsCode": parse_code},
            "id": id_parse,
            "name": "Preparar recordatorios",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [680, 380],
        },
        # ── 4. Filtrar: solo los que tienen teléfono ──────────────────────────
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "typeValidation": "loose"},
                    "conditions": [{
                        "id": _uid(),
                        "leftValue": "={{ $json.telefono }}",
                        "rightValue": "",
                        "operator": {"type": "string", "operation": "notEmpty"},
                    }],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": id_filter,
            "name": "¿Tiene teléfono?",
            "type": "n8n-nodes-base.filter",
            "typeVersion": 2,
            "position": [900, 380],
        },
    ]

    # ── 5. Nodo de envío (WhatsApp Twilio o Email Gmail) ──────────────────────
    if canal == "email":
        send_node = {
            "parameters": {
                "sendTo": "={{ $json.email || $json.telefono }}",
                "subject": f"Recordatorio de tu cita en {nombre_negocio}",
                "message": f"={{{{ `{msg_default}`"
                           ".replace('{nombre}', $json.nombre)"
                           ".replace('{fecha}', $json.fecha)"
                           ".replace('{hora}', $json.hora)"
                           ".replace('{servicio}', $json.servicio) }}}}",
                "options": {"appendAttribution": False},
            },
            "id": id_send,
            "name": "Enviar recordatorio (Email)",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2,
            "position": [1120, 380],
        }
    else:
        send_node = {
            "parameters": {
                "resource": "message",
                "operation": "send",
                "from": twilio_whatsapp_from,
                "to": "=whatsapp:{{ $json.telefono }}",
                "message": f"={{{{ `{msg_default}`"
                           ".replace('{nombre}', $json.nombre)"
                           ".replace('{fecha}', $json.fecha)"
                           ".replace('{hora}', $json.hora)"
                           ".replace('{servicio}', $json.servicio) }}}}",
                "options": {},
            },
            "id": id_send,
            "name": "Enviar recordatorio (WhatsApp)",
            "type": "n8n-nodes-base.twilio",
            "typeVersion": 1,
            "position": [1120, 380],
        }
    nodes.append(send_node)

    send_name = send_node["name"]
    connections = {
        "Cada hora": {
            "main": [[{"node": "Citas próximas", "type": "main", "index": 0}]]
        },
        "Citas próximas": {
            "main": [[{"node": "Preparar recordatorios", "type": "main", "index": 0}]]
        },
        "Preparar recordatorios": {
            "main": [[{"node": "¿Tiene teléfono?", "type": "main", "index": 0}]]
        },
        "¿Tiene teléfono?": {
            "main": [[{"node": send_name, "type": "main", "index": 0}]]
        },
    }

    workflow = {
        "name": f"Recordatorios automáticos — {nombre_negocio}",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "versionId": _uid(),
        "meta": {"templateCredsSetupCompleted": False},
        "tags": ["recordatorios", "no-show", "fidelizacion"],
    }

    return json.dumps(workflow, ensure_ascii=False, indent=2)


def generar_workflow_resenas(
    nombre_negocio: str = "Mi Negocio",
    place_id: str = "",
    google_api_key: str = "TU_GOOGLE_API_KEY",
    email_negocio: str = "negocio@ejemplo.com",
    horas_check: int = 6,
    min_stars_alerta: int = 3,
) -> str:
    """
    Workflow n8n para monitorización automática de reseñas de Google.

    Flujo cada N horas:
      1. Schedule Trigger → llama a Google Places API para obtener reseñas recientes
      2. Filtra y clasifica: positiva (>=4★) o negativa (<=min_stars_alerta★)
      3. Para negativas → alerta email inmediata al negocio
      4. Genera respuesta automática con Claude IA
      5. Guarda respuesta en Google Sheets para revisión manual antes de publicar
    """
    uid_schedule = _uid()
    uid_places   = _uid()
    uid_filter   = _uid()
    uid_classify = _uid()
    uid_alert    = _uid()
    uid_ia_resp  = _uid()
    uid_sheets   = _uid()

    nodes = {
        "Cada 6 horas": {
            "id": uid_schedule,
            "name": "Cada 6 horas",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [200, 300],
            "parameters": {
                "rule": {
                    "interval": [{"field": "hours", "hoursInterval": horas_check}]
                }
            },
        },
        "Obtener reseñas Google": {
            "id": uid_places,
            "name": "Obtener reseñas Google",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [420, 300],
            "parameters": {
                "method": "GET",
                "url": "https://maps.googleapis.com/maps/api/place/details/json",
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [
                        {"name": "place_id", "value": place_id or "PLACE_ID_DEL_NEGOCIO"},
                        {"name": "fields",   "value": "reviews,rating,user_ratings_total"},
                        {"name": "key",      "value": google_api_key},
                        {"name": "language", "value": "es"},
                    ]
                },
                "options": {},
            },
        },
        "Clasificar reseñas": {
            "id": uid_filter,
            "name": "Clasificar reseñas",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [640, 300],
            "parameters": {
                "jsCode": (
                    "const result = $input.first().json;\n"
                    "const reviews = result.result?.reviews || [];\n"
                    f"const MIN_STARS = {min_stars_alerta};\n"
                    f"const NEGOCIO = '{nombre_negocio}';\n"
                    "const processed = reviews.slice(0, 5).map(r => ({\n"
                    "  autor: r.author_name,\n"
                    "  rating: r.rating,\n"
                    "  texto: r.text || '(sin texto)',\n"
                    "  fecha: new Date(r.time * 1000).toLocaleDateString('es-ES'),\n"
                    "  tipo: r.rating >= 4 ? 'positiva' : 'negativa',\n"
                    "  alerta: r.rating <= MIN_STARS,\n"
                    "  negocio: NEGOCIO,\n"
                    "  relative_time: r.relative_time_description,\n"
                    "}));\n"
                    "return processed.map(r => ({json: r}));"
                ),
            },
        },
        "¿Reseña negativa?": {
            "id": uid_classify,
            "name": "¿Reseña negativa?",
            "type": "n8n-nodes-base.filter",
            "typeVersion": 2,
            "position": [860, 300],
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "leftValue": "={{ $json.alerta }}",
                            "rightValue": True,
                            "operator": {"type": "boolean", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                },
                "looseTypeValidation": True,
            },
        },
        "Alerta email negativa": {
            "id": uid_alert,
            "name": "Alerta email negativa",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2.1,
            "position": [1080, 180],
            "parameters": {
                "operation": "send",
                "sendTo": email_negocio,
                "subject": "=⚠️ Reseña negativa en Google — {{ $json.rating }}★ de {{ $json.autor }}",
                "emailType": "html",
                "message": (
                    "=<h2 style='color:#c0392b;'>⚠️ Nueva reseña negativa</h2>"
                    "<p><strong>Cliente:</strong> {{ $json.autor }}</p>"
                    "<p><strong>Rating:</strong> {{ $json.rating }}★</p>"
                    "<p><strong>Fecha:</strong> {{ $json.fecha }}</p>"
                    "<p><strong>Reseña:</strong></p>"
                    "<blockquote style='border-left:4px solid #e74c3c;padding-left:12px;color:#555;'>"
                    "{{ $json.texto }}</blockquote>"
                    "<p>La respuesta sugerida por IA se guardará en tu Google Sheet para revisión.</p>"
                    "<p><em>MerakIA — Gestor de Reputación</em></p>"
                ),
            },
        },
        "Generar respuesta con IA": {
            "id": uid_ia_resp,
            "name": "Generar respuesta con IA",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1080, 420],
            "parameters": {
                "method": "POST",
                "url": "https://api.anthropic.com/v1/messages",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "x-api-key",        "value": "={{ $env.ANTHROPIC_API_KEY }}"},
                        {"name": "anthropic-version", "value": "2023-06-01"},
                        {"name": "content-type",      "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "contentType": "json",
                "body": {
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 300,
                    "system": (
                        f"Eres el community manager de {nombre_negocio}. "
                        "Genera respuestas profesionales, cálidas y empáticas a reseñas de Google. "
                        "Para negativas: empatía → reconocer → solución → invitar a volver. "
                        "Para positivas: agradecimiento específico → invitar a repetir. "
                        "Máximo 80 palabras. Sin markdown."
                    ),
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "=Genera una respuesta a esta reseña de Google:\n\n"
                                "Cliente: {{ $json.autor }}\n"
                                "Rating: {{ $json.rating }}★\n"
                                "Reseña: {{ $json.texto }}\n"
                                "Tipo: {{ $json.tipo }}\n\n"
                                "Responde en el mismo idioma que la reseña."
                            ),
                        }
                    ],
                },
                "options": {},
            },
        },
        "Guardar en Google Sheets": {
            "id": uid_sheets,
            "name": "Guardar en Google Sheets",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.5,
            "position": [1300, 420],
            "parameters": {
                "operation": "append",
                "documentId": {"__rl": True, "mode": "list", "value": "TU_SPREADSHEET_ID"},
                "sheetName":  {"__rl": True, "mode": "list", "value": "Reseñas"},
                "columns": {
                    "mappingMode": "defineBelow",
                    "value": {
                        "Fecha":           "={{ $('Clasificar reseñas').item.json.fecha }}",
                        "Autor":           "={{ $('Clasificar reseñas').item.json.autor }}",
                        "Rating":          "={{ $('Clasificar reseñas').item.json.rating }}",
                        "Tipo":            "={{ $('Clasificar reseñas').item.json.tipo }}",
                        "Reseña":          "={{ $('Clasificar reseñas').item.json.texto }}",
                        "Respuesta IA":    "={{ $json.content[0].text }}",
                        "Estado":          "Pendiente revisión",
                    },
                },
                "options": {},
            },
        },
    }

    connections = {
        "Cada 6 horas":           {"main": [[{"node": "Obtener reseñas Google",  "type": "main", "index": 0}]]},
        "Obtener reseñas Google":  {"main": [[{"node": "Clasificar reseñas",      "type": "main", "index": 0}]]},
        "Clasificar reseñas":      {"main": [[{"node": "¿Reseña negativa?",       "type": "main", "index": 0}]]},
        "¿Reseña negativa?":       {"main": [[
            {"node": "Alerta email negativa",    "type": "main", "index": 0},
            {"node": "Generar respuesta con IA", "type": "main", "index": 0},
        ]]},
        "Generar respuesta con IA": {"main": [[{"node": "Guardar en Google Sheets", "type": "main", "index": 0}]]},
    }

    workflow = {
        "name": f"Gestor de Reseñas Google — {nombre_negocio}",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "versionId": _uid(),
        "meta": {"templateCredsSetupCompleted": False},
        "tags": ["resenas", "reputacion", "google-reviews"],
    }

    return json.dumps(workflow, ensure_ascii=False, indent=2)

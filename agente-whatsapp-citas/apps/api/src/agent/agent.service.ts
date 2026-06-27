import { Injectable, Logger } from '@nestjs/common';
import { Agent } from '@mastra/core/agent';
import { ConfigService } from '../config/config.service';
import { AppointmentsService } from '../appointments/appointments.service';
import { Patient } from '../patients/patient.entity';
import { buildTools, ToolDeps } from './agent.tools';
import { getMastra } from './mastra';
import { AgentConfig } from '../config/agent-config.entity';

@Injectable()
export class AgentService {
  private readonly logger = new Logger('AgentService');

  constructor(
    private readonly config: ConfigService,
    private readonly appointments: AppointmentsService,
  ) {
    // Touch the Mastra instance so its @mastra/pg storage is initialised.
    getMastra();
  }

  private buildSystemPrompt(cfg: AgentConfig, knowledgeBase?: string | null): string {
    const now = new Intl.DateTimeFormat('es-ES', {
      timeZone: cfg.timezone,
      dateStyle: 'full',
      timeStyle: 'short',
    }).format(new Date());

    const services = (cfg.services ?? [])
      .map((s) => `- ${s.name} (${s.durationMin} min)`)
      .join('\n');

    const dayNames = [
      'domingo',
      'lunes',
      'martes',
      'miércoles',
      'jueves',
      'viernes',
      'sábado',
    ];
    const schedule = (cfg.schedule ?? [])
      .map(
        (d) =>
          `- ${dayNames[d.weekday]}: ${
            d.intervals.length
              ? d.intervals.map((i) => `${i.start}-${i.end}`).join(', ')
              : 'cerrado'
          }`,
      )
      .join('\n');

    return `Eres el asistente de citas de "${cfg.centerName}".
${cfg.description ? cfg.description + '\n' : ''}
Tono: ${cfg.tone}. Hablas en español, de forma breve y natural (es WhatsApp).
Zona horaria del centro: ${cfg.timezone}. Fecha y hora actuales: ${now}.

SERVICIOS DISPONIBLES:
${services || '- (sin servicios configurados)'}

HORARIOS DE ATENCIÓN:
${schedule || '- (sin horarios configurados)'}

QUÉ HACES:
- Gestionas citas: consultas disponibilidad, reservas, listas y cancelas.
- Usa SIEMPRE la herramienta check_availability antes de ofrecer una hora. NUNCA inventes huecos.
- Confirma el servicio y la hora con el paciente antes de reservar con book_appointment.
- Para cancelar, primero usa list_appointments para localizar la cita correcta.

SALVAGUARDA CLÍNICA (OBLIGATORIA E INNEGOCIABLE):
- NO eres personal sanitario. NO das diagnósticos, NO das consejo médico, NO interpretas síntomas y NO recomiendas tratamientos.
- Si el paciente describe una dolencia o síntoma, responde con empatía y ofrécele reservar una "Primera valoración" para que un fisioterapeuta lo valore en persona.
- Tu único ámbito es la gestión de citas. Si te piden algo médico, redirige amablemente a reservar una valoración.

ESTILO:
- Mensajes cortos, cálidos y claros. Una sola pregunta o acción por mensaje.
- No uses markdown ni listas largas; escribe como en un chat.${
      knowledgeBase
        ? `\n\nINFORMACIÓN DEL CENTRO (usa esto para responder preguntas sobre precios, protocolos, políticas, etc.):\n${knowledgeBase}`
        : ''
    }`;
  }

  /**
   * Generates the agent's reply for a given patient and conversation, using the
   * provided history. Tools are scoped to that patient.
   */
  async generateReply(params: {
    conversationId: string;
    patient: Patient;
    history: { role: 'user' | 'assistant'; content: string }[];
    userText: string;
  }): Promise<string> {
    const cfg = await this.config.getRaw();
    const knowledgeBase = await this.config.getKnowledgeBase();

    if (!cfg.enabled) {
      return 'En este momento la atención automática está desactivada. Un miembro del equipo te responderá en cuanto pueda.';
    }

    const apiKey = await this.config.resolveApiKey();
    if (!apiKey) {
      this.logger.warn('No hay API key configurada.');
      return 'Gracias por tu mensaje. Ahora mismo no puedo responder automáticamente; el equipo te atenderá en breve.';
    }
    const modelId = await this.config.resolveModel();

    const toolDeps: ToolDeps = {
      appointments: this.appointments,
      timezone: cfg.timezone,
      patient: params.patient,
    };

    const messages = [
      ...params.history,
      { role: 'user' as const, content: params.userText },
    ];

    try {
      const systemPrompt = this.buildSystemPrompt(cfg, knowledgeBase);

      if (apiKey.startsWith('sk-ant-')) {
        return await this.generateWithAnthropic(
          apiKey,
          modelId,
          systemPrompt,
          messages,
          toolDeps,
        );
      }

      // OpenRouter path (OpenAI-compatible).
      const tools = buildTools(toolDeps);
      const agent = new Agent({
        id: 'citas-agent',
        name: 'Agente de Citas',
        instructions: systemPrompt,
        model: { providerId: 'openrouter', modelId, url: 'https://openrouter.ai/api/v1', apiKey },
        tools,
      });
      const result = await agent.generate(messages as any, { maxSteps: 6 });
      return (result.text || '').trim() || 'Perdona, ¿puedes repetirlo?';
    } catch (e) {
      this.logger.error(
        `Error generando respuesta del agente: ${e instanceof Error ? e.message : e}`,
      );
      return 'Disculpa, he tenido un problema técnico. ¿Puedes intentarlo de nuevo en un momento?';
    }
  }

  /** Calls Anthropic Messages API directly via fetch — avoids SDK version issues. */
  private async generateWithAnthropic(
    apiKey: string,
    modelId: string,
    system: string,
    history: { role: 'user' | 'assistant'; content: string }[],
    deps: ToolDeps,
  ): Promise<string> {
    const ANTHROPIC_TOOLS = [
      {
        name: 'check_availability',
        description: 'Consulta los huecos libres para un servicio en una fecha concreta. Usar SIEMPRE antes de proponer una hora.',
        input_schema: {
          type: 'object',
          properties: {
            service: { type: 'string', description: 'Nombre del servicio' },
            date: { type: 'string', description: 'Fecha YYYY-MM-DD' },
          },
          required: ['service', 'date'],
        },
      },
      {
        name: 'book_appointment',
        description: 'Reserva una cita para el paciente actual. Solo tras confirmar servicio y hora exacta.',
        input_schema: {
          type: 'object',
          properties: {
            service: { type: 'string' },
            startsAt: { type: 'string', description: 'ISO 8601 UTC obtenido de check_availability' },
          },
          required: ['service', 'startsAt'],
        },
      },
      {
        name: 'list_appointments',
        description: 'Lista las próximas citas del paciente actual.',
        input_schema: { type: 'object', properties: {} },
      },
      {
        name: 'cancel_appointment',
        description: 'Cancela una cita del paciente actual por su id.',
        input_schema: {
          type: 'object',
          properties: { appointmentId: { type: 'string' } },
          required: ['appointmentId'],
        },
      },
    ];

    const { appointments, timezone, patient } = deps;
    const { formatHuman } = await import('../common/timezone');

    const runTool = async (name: string, input: Record<string, string>): Promise<string> => {
      if (name === 'check_availability') {
        const slots = await appointments.availability(input.service, input.date);
        return slots.length
          ? `Huecos libres: ${slots.map((s) => s.label).join(', ')}`
          : 'No hay huecos libres ese día.';
      }
      if (name === 'book_appointment') {
        try {
          const appt = await appointments.create(
            { patientId: patient.id, serviceName: input.service, startsAt: input.startsAt },
            'agent',
          );
          return `Cita confirmada: ${appt.serviceName} el ${formatHuman(appt.startsAt, timezone)}.`;
        } catch (e) {
          return e instanceof Error ? e.message : 'No se pudo reservar esa hora.';
        }
      }
      if (name === 'list_appointments') {
        const all = await appointments.findForPatient(patient.id);
        const upcoming = all.filter((a) => a.status === 'scheduled' && a.startsAt.getTime() > Date.now());
        return upcoming.length
          ? upcoming.map((a) => `${a.id}: ${a.serviceName} el ${formatHuman(a.startsAt, timezone)}`).join('\n')
          : 'No hay citas próximas.';
      }
      if (name === 'cancel_appointment') {
        const appt = await appointments.findOne(input.appointmentId).catch(() => null);
        if (!appt || appt.patientId !== patient.id) return 'No encuentro esa cita.';
        await appointments.cancel(appt.id);
        return `Cita cancelada: ${appt.serviceName} el ${formatHuman(appt.startsAt, timezone)}.`;
      }
      return 'Herramienta desconocida.';
    };

    const msgs: { role: string; content: unknown }[] = history.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    for (let step = 0; step < 6; step++) {
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          model: modelId,
          max_tokens: 1024,
          system,
          tools: ANTHROPIC_TOOLS,
          messages: msgs,
        }),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`Anthropic API ${res.status}: ${body}`);
      }

      const data = await res.json() as {
        stop_reason: string;
        content: { type: string; text?: string; id?: string; name?: string; input?: Record<string, string> }[];
      };

      if (data.stop_reason === 'end_turn') {
        const textBlock = data.content.find((b) => b.type === 'text');
        return (textBlock?.text ?? '').trim() || 'Perdona, ¿puedes repetirlo?';
      }

      if (data.stop_reason === 'tool_use') {
        msgs.push({ role: 'assistant', content: data.content });
        const toolResults = await Promise.all(
          data.content
            .filter((b) => b.type === 'tool_use')
            .map(async (b) => ({
              type: 'tool_result',
              tool_use_id: b.id,
              content: await runTool(b.name!, b.input ?? {}),
            })),
        );
        msgs.push({ role: 'user', content: toolResults });
        continue;
      }

      const textBlock = data.content.find((b) => b.type === 'text');
      return (textBlock?.text ?? '').trim() || 'Perdona, ¿puedes repetirlo?';
    }

    return 'No he podido completar la solicitud. Por favor, inténtalo de nuevo.';
  }

  /**
   * Voice-channel entry point. No Patient required — the caller is anonymous
   * until they identify themselves. Uses the same Anthropic agentic loop.
   */
  async generateReplyForVoice(
    history: { role: 'user' | 'assistant'; content: string }[],
  ): Promise<string> {
    const cfg = await this.config.getRaw();
    const knowledgeBase = await this.config.getKnowledgeBase();
    const apiKey = await this.config.resolveApiKey();
    const modelId = await this.config.resolveModel();

    if (!apiKey) return 'En este momento el sistema no está disponible. Por favor, llama más tarde.';

    const system = this.buildSystemPrompt(cfg, knowledgeBase);
    const deps: ToolDeps = {
      appointments: this.appointments,
      timezone: cfg.timezone,
      patient: undefined as any,
    };

    if (apiKey.startsWith('sk-ant-')) {
      return this.generateWithAnthropic(apiKey, modelId, system, history, deps);
    }

    // OpenRouter path
    const messages = history.map((m) => ({ role: m.role, content: m.content }));
    try {
      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId, messages: [{ role: 'system', content: system }, ...messages] }),
      });
      const data = await res.json() as any;
      return (data.choices?.[0]?.message?.content ?? '').trim() || 'Perdona, ¿puedes repetirlo?';
    } catch {
      return 'Disculpa, he tenido un problema técnico.';
    }
  }
}
